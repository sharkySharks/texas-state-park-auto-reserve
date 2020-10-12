from datetime import date, datetime
import json
import os
import re
import sys, traceback
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# globals
rd = {}
driver = webdriver.Chrome()
driver.implicitly_wait(10)

def main():  
    #  load reservation details
    with open('reservation_details.json') as json_file:
       global rd
       rd = json.load(json_file)

    driver.get("https://texasstateparks.reserveamerica.com/")

    try:
        sign_in()
        search_for_location()
        selection_made = select_reservation()
        if not selection_made:
            if rd["wait_for_opening"]:
                # check every 30 seconds for an opening
                while not selection_made:
                    # only continue processing if the requested date is earlier than the current date
                    today = date.today()
                    requested_date = datetime.date(datetime.strptime(rd["arrival_date"], '%m/%d/%Y'))
                    if today > requested_date:
                        raise ValueError(f'requested date ( {requested_date} ) is after current date ( {today} )')

                    print(f'[{datetime.now(tz=None)}] Waiting for opening in reservation...')
                    time.sleep(30)
                    driver.refresh()
                    selection_made = select_reservation()
            else:
                print("No reservations are available for your requested time. Set 'wait_for_opening' to true if you want me to keep trying for you.")
                driver.close()
                return
        book_reservation()
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        print(f'Errors returned: {e}')
        driver.close()
        return
    
    print("RESERVATION SUCCESSFULLY MADE!")

    driver.close()

def sign_in():
    driver.find_element_by_id("signIn").click()
    username = driver.find_element_by_name("AemailGroup_1733152645")
    username.send_keys(os.environ.get("TEXAS_STATE_PARK_USERNAME"))
    password = driver.find_element_by_name("ApasswrdGroup_704558654")
    password.send_keys(os.environ.get("TEXAS_STATE_PARK_PASSWORD"))
    time.sleep(1)
    driver.find_element_by_name("submitForm").click()

def search_for_location():
    # make reservation link
    driver.find_element_by_id("Home").click()
    # select location
    location = driver.find_element_by_name("locationCriteria")
    location.send_keys(rd["destination"])
    location_elem = driver.find_element_by_xpath("//div[@id='locationCriteria_container']//div[@class='selectable'][1]")
    ActionChains(driver).move_to_element(location_elem).click().perform()
    # select Day Passes
    driver.find_element_by_id("interest").click()
    driver.find_element_by_xpath('//option[text()="Day Passes"]').click()
    # select date
    day_pass_date = driver.find_element_by_xpath("//div[@id='availability_section_daypass']//input[@id='dayPassDate']")
    day_pass_date.send_keys(rd["arrival_date"])
    day_pass_date.send_keys(Keys.TAB)
    # input length of stay
    length_of_stay = driver.find_element_by_id("dayPassLengthOfStay")
    length_of_stay.send_keys(rd["days_of_stay"])
    # click search
    driver.find_element_by_xpath("//button[text()='Search']").click()
    # select location
    driver.find_element_by_xpath(f'//div[@id="search_results_list"]//div[@class="facility_header_name"]//a[contains(text(),"{rd["destination"]}")]').click()
    # enter number of vehicles
    vehicles = driver.find_element_by_id("quantity")
    vehicles.send_keys(rd["number_of_vehicles"])
    # click search availability
    driver.find_element_by_id("btnbookdates").click()

def select_reservation():
    some_selection_made = False 
    locals()[f'{rd["destination"]} Schedule'] = {}
    
    # select days from scheduling matrix
    for x in range(rd["days_of_stay"]):
        calendar_day = driver.find_elements_by_css_selector(f"div.matrixheader div.calendar div.date")[x].text
        calendar_weekday = driver.find_elements_by_css_selector(f"div.matrixheader div.calendar div.weekday")[x].text
        
        locals()[f'{rd["destination"]} Schedule'][f'{calendar_weekday}-{calendar_day}'] = {}
        locals()[f'{rd["destination"]} Schedule'][f'{calendar_weekday}-{calendar_day}']["selected"] = "NONE"
        morning = driver.find_elements_by_css_selector(f"div.matrixrow div.status:nth-of-type({x+1})")[0]
        afternoon = driver.find_elements_by_css_selector(f"div.matrixrow div.status:nth-of-type({x+1})")[1]
        morning_availability = morning.get_attribute("title")
        afternoon_availability = afternoon.get_attribute("title")
        locals()[f'{rd["destination"]} Schedule'][f'{calendar_weekday}-{calendar_day}']["morning"] = morning_availability
        locals()[f'{rd["destination"]} Schedule'][f'{calendar_weekday}-{calendar_day}']["afternoon"] = afternoon_availability

        if morning_availability == "Reserved" and afternoon_availability == "Reserved":
            continue

        # try to select based on preferences provided
        if rd["preferences"][x] == "morning" and morning_availability == "Available":
            morning.click()
            locals()[f'{rd["destination"]} Schedule'][f'{calendar_weekday}-{calendar_day}']["selected"] = "morning"
            some_selection_made = True
        elif rd["preferences"][x] == "afternoon" and afternoon_availability == "Available":
            afternoon.click()
            locals()[f'{rd["destination"]} Schedule'][f'{calendar_weekday}-{calendar_day}']["selected"] = "afternoon"
            some_selection_made = True
        elif rd["preferences"][x] == "either":
            if morning_availability == "Available":
                morning.click()
                locals()[f'{rd["destination"]} Schedule'][f'{calendar_weekday}-{calendar_day}']["selected"] = "morning"
                some_selection_made = True
            elif afternoon_availability == "Available":
                afternoon.click()
                locals()[f'{rd["destination"]} Schedule'][f'{calendar_weekday}-{calendar_day}']["selected"] = "afternoon"
                some_selection_made = True
    
    print(f'Day Pass Availability for {rd["days_of_stay"]} day pass(es) starting on {rd["arrival_date"]}:')
    print(locals()[f'{rd["destination"]} Schedule'])
    
    # if any selection is made, proceed with booking, otherwise wait for a booking to open up and try again
    if some_selection_made:
        driver.find_element_by_id("btnbookdates").click()
    
    return some_selection_made
    
def book_reservation():
    # select vehicle information - Car
    driver.find_element_by_xpath("//select[@id='0_vehicletype']/option[text()='Car']").click()

    # enter number of adults
    adults = driver.find_element_by_id("v_qtyPersons_1id")
    adults.clear()
    adults.send_keys(rd["number_of_adults"])

    # enter number of children
    children = driver.find_element_by_id("v_qtyPersons_18id")
    children.clear()
    children.send_keys(rd["number_of_children"])
    
    # agree to information
    driver.find_element_by_id("agreement").click()
    
    # go to shopping cart
    driver.find_element_by_id("continueshop").click()
    driver.find_element_by_id("chkout").click()
    
    # shopping cart checkout - card information
    lower_cc_type = rd["credit_card"]["type"].lower()
    if re.search(lower_cc_type, "discover"):
        card_type = "Discover"
    elif re.search(lower_cc_type, "mastercard"):
        card_type = "MasterCard"
    elif re.search(lower_cc_type, "visa"):
        card_type = "Visa"
    else:
        raise ValueError(f'only visa, mastercard, discover accepted. received: {lower_cc_type}')

    driver.find_element_by_xpath(f'//select[@id="cardTypeId_1"]/option[text()="{card_type}"]').click()
    cc_num = driver.find_element_by_id("cardnum_1")
    cc_num.send_keys(rd["credit_card"]["number"])
    cc_cvc = driver.find_element_by_id("seccode_1")
    cc_cvc.send_keys(rd["credit_card"]["cvc"])
    cc_exp_month = driver.find_element_by_id("expmonth_1")
    cc_exp_month.send_keys(rd["credit_card"]["exp_month"])
    cc_exp_year = driver.find_element_by_id("expyear_1")
    cc_exp_year.send_keys(rd["credit_card"]["exp_year"])
    cc_first_name = driver.find_element_by_id("fname_1")
    cc_first_name.send_keys(rd["credit_card"]["first_name"])
    cc_last_name = driver.find_element_by_id("lname_1")
    cc_last_name.send_keys(rd["credit_card"]["last_name"])
    cc_zip = driver.find_element_by_id("ccPostCode_1")
    cc_zip.send_keys(rd["credit_card"]["zip_code"])

    # read and accept button
    driver.find_element_by_id("ackacc").click()

    # make reservation
    driver.find_element_by_id("chkout").click()

if __name__ == "__main__":
    main()