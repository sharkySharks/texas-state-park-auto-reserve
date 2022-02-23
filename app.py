from datetime import date, datetime
import json
import os
import re
import sys, traceback
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

# globals
rd = {}
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.implicitly_wait(10)

def main():  
    #  load reservation details
    with open('reservation_details.json') as json_file:
       global rd
       rd = json.load(json_file)

    driver.get("https://texasstateparks.reserveamerica.com/")

    try:
        sign_in()
        if rd["interest"] == "camping" or rd["interest"] == "day pass":
            search_for_location(rd["interest"])
            selection_made = select_reservation(rd["interest"])     
        else:
            raise ValueError(f'interest should be either "camping" or "day pass". received: {rd["interest"]}')
        
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
                    selection_made=select_reservation(rd["interest"])
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
    
    print(f'""""""""""""""""""""""""""""""""')
    print("RESERVATION SUCCESSFULLY MADE!")
    print("See your current bookings: https://texasstateparks.reserveamerica.com/reservation.do?mode=current")
    print(f'""""""""""""""""""""""""""""""""')

    driver.close()

def sign_in():
    driver.find_element(By.ID, "signIn").click()
    username = driver.find_element(By.ID, "AemailGroup_1733152645")
    username.send_keys(os.environ.get("TEXAS_STATE_PARK_USERNAME"))
    password = driver.find_element(By.ID, "ApasswrdGroup_704558654")
    password.send_keys(os.environ.get("TEXAS_STATE_PARK_PASSWORD"))
    time.sleep(1)
    driver.find_element(By.ID, "signinbutton").click()

def search_for_location(interest):
    # make reservation link
    driver.find_element(By.ID, "Home").click()
    # select location
    location = driver.find_element(By.ID, "locationCriteria")
    location.send_keys(rd["destination"])
    location_elem = driver.find_element(By.XPATH, "//div[@id='locationCriteria_container']//div[@class='selectable'][1]")
    ActionChains(driver).move_to_element(location_elem).click().perform()

    # interest supported: 'camping' and 'day pass'
    if interest == "camping":
        # select Camping and Lodging
        select_interest=Select(driver.find_element(By.ID, "interest"))
        select_interest.select_by_visible_text("Camping & Lodging")
        select_camp=Select(driver.find_element(By.ID, "lookingFor"))
        CAMP_SITE=""
        if rd["camp_site_selection"]["type"] == "tent":
            CAMP_SITE="Tent Sites"
        elif rd["camp_site_selection"]["type"] == "rv":
            CAMP_SITE="RV Sites"
        elif rd["camp_site_selection"]["type"] == "cabin":
            CAMP_SITE="Cabin, Lodges or Rooms"
        else:
            raise ValueError(f'camp_site_selection should be of one of the following values: tent, cabin, rv. received: {rd["camp_site_selection"]}')
        select_camp.select_by_visible_text(CAMP_SITE)
        # select date
        day_pass_date = driver.find_element(By.XPATH, "//div[@id='availability_section_camping']//input[@id='campingDate']")
        day_pass_date.send_keys(rd["arrival_date"])
        day_pass_date.send_keys(Keys.TAB)
        # input length of stay
        length_of_stay = driver.find_element(By.ID, "lengthOfStay")
        length_of_stay.send_keys(rd["days_of_stay"])

        # click search
        driver.find_element(By.XPATH, "//button[text()='Search']").click()

        # select first location in the list
        driver.find_element(By.XPATH, f'//div[@id="search_results_list"]//div[@class="facility_header_name"]//a[contains(text(),"{rd["destination"]}")]').click()

    elif interest == "day pass":
        # select Day Passes
        select_day_pass=Select(driver.find_element(By.ID, "interest"))
        select_day_pass.select_by_visible_text("Day Passes")
        # select date
        day_pass_date = driver.find_element(By.XPATH, "//div[@id='availability_section_daypass']//input[@id='dayPassDate']")
        time.sleep(3)
        day_pass_date.send_keys(rd["arrival_date"])
        day_pass_date.send_keys(Keys.TAB)
        # input length of stay
        length_of_stay = driver.find_element(By.ID, "dayPassLengthOfStay")
        length_of_stay.send_keys(rd["days_of_stay"])
        # click search
        driver.find_element(By.XPATH, "//button[text()='Search']").click()

        # select first location in the list
        driver.find_element(By.XPATH, f'//div[@id="search_results_list"]//div[@class="facility_header_name"]//a[contains(text(),"{rd["destination"]}")]').click()
        
        # enter number of vehicles
        vehicles = driver.find_element(By.ID, "quantity")
        vehicles.send_keys(rd["number_of_vehicles"])
        # click search availability
        driver.find_element(By.ID, "btnbookdates").click()

def select_reservation(interest):
    selection_made=False

    if interest == "camping":
        selection_made=select_camping_reservation()
    elif interest == "day pass":
        selection_made=select_day_pass_reservation()
    
    return selection_made

def select_camping_reservation():
    some_selection_made = False

    # no available options for camping
    available_options=driver.find_elements(By.CSS_SELECTOR, "div.alternativeSuggestion")
    if len(available_options) == 0:
        return some_selection_made

    # 
    # LEFT OFF HERE: 
    # - need to select the first camp site option and then select the default day selections
    #   for some reason it is not clicking the link
    # 
    if rd["camp_site_selection"]["preference"] == "any":
        first_option=driver.find_elements(By.XPATH, "//div[contains(text(), 'available')]//a[@class='book now']")
        ActionChains(driver).move_to_element(first_option).perform()
        time.sleep(3)
        first_option.click()
        time.sleep(100000)
    elif rd["camp_site_selection"]["preference"] == "electric":
        print()
    elif rd["camp_site_selection"]["preference"] == "primitive":
        print()
    else:
        raise ValueError(f'camp site select preference options are: "any", "electric", "primitive". received: {rd["camp_site_selection"]["preference"]}')
    
    
def select_day_pass_reservation():
    some_selection_made = False 
    locals()[f'{rd["destination"]} Schedule'] = {}
    
    # select days from scheduling matrix
    for x in range(rd["days_of_stay"]):
        calendar_day = driver.find_elements(By.CSS_SELECTOR, f"div.matrixheader div.calendar div.date")[x].text
        calendar_weekday = driver.find_elements(By.CSS_SELECTOR, f"div.matrixheader div.calendar div.weekday")[x].text
        
        locals()[f'{rd["destination"]} Schedule'][f'{calendar_weekday}-{calendar_day}'] = {}
        locals()[f'{rd["destination"]} Schedule'][f'{calendar_weekday}-{calendar_day}']["selected"] = "NONE"
        morning = driver.find_elements(By.CSS_SELECTOR, f"div.matrixrow div.status:nth-of-type({x+1})")[0]
        afternoon = driver.find_elements(By.CSS_SELECTOR, f"div.matrixrow div.status:nth-of-type({x+1})")[1]
        morning_availability = morning.get_attribute("title")
        afternoon_availability = afternoon.get_attribute("title")
        locals()[f'{rd["destination"]} Schedule'][f'{calendar_weekday}-{calendar_day}']["morning"] = morning_availability
        locals()[f'{rd["destination"]} Schedule'][f'{calendar_weekday}-{calendar_day}']["afternoon"] = afternoon_availability

        if morning_availability == "Reserved" and afternoon_availability == "Reserved":
            continue

        # try to select based on preferences provided
        if rd["day_pass_selection"]["preferences"][x] == "morning" and morning_availability == "Available":
            morning.click()
            locals()[f'{rd["destination"]} Schedule'][f'{calendar_weekday}-{calendar_day}']["selected"] = "morning"
            some_selection_made = True
        elif rd["day_pass_selection"]["preferences"][x] == "afternoon" and afternoon_availability == "Available":
            afternoon.click()
            locals()[f'{rd["destination"]} Schedule'][f'{calendar_weekday}-{calendar_day}']["selected"] = "afternoon"
            some_selection_made = True
        elif rd["day_pass_selection"]["preferences"][x] == "either":
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
        driver.find_element(By.ID, "btnbookdates").click()
    
    return some_selection_made
    
def book_reservation():
    # select vehicle information - Car
    driver.find_element(By.XPATH, "//select[@id='0_vehicletype']/option[text()='Car']").click()

    # enter number of adults
    adults = driver.find_element(By.ID, "v_qtyPersons_1id")
    adults.clear()
    adults.send_keys(rd["number_of_adults"])

    # enter number of children
    children = driver.find_element(By.ID, "v_qtyPersons_18id")
    children.clear()
    children.send_keys(rd["number_of_children"])
    
    # agree to information
    driver.find_element(By.ID, "agreement").click()
    
    # go to shopping cart
    driver.find_element(By.ID, "continueshop").click()
    driver.find_element(By.ID, "chkout").click()
    
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

    driver.find_element(By.XPATH, f'//select[@id="cardTypeId_1"]/option[text()="{card_type}"]').click()
    cc_num = driver.find_element(By.ID, "cardnum_1")
    cc_num.send_keys(rd["credit_card"]["number"])
    cc_cvc = driver.find_element(By.ID, "seccode_1")
    cc_cvc.send_keys(rd["credit_card"]["cvc"])
    cc_exp_month = driver.find_element(By.ID, "expmonth_1")
    cc_exp_month.send_keys(rd["credit_card"]["exp_month"])
    cc_exp_year = driver.find_element(By.ID, "expyear_1")
    cc_exp_year.send_keys(rd["credit_card"]["exp_year"])
    cc_first_name = driver.find_element(By.ID, "fname_1")
    cc_first_name.send_keys(rd["credit_card"]["first_name"])
    cc_last_name = driver.find_element(By.ID, "lname_1")
    cc_last_name.send_keys(rd["credit_card"]["last_name"])
    cc_zip = driver.find_element(By.ID, "ccPostCode_1")
    cc_zip.send_keys(rd["credit_card"]["zip_code"])

    # read and accept button
    driver.find_element(By.ID, "ackacc").click()

    # make reservation
    # driver.find_element(By.ID, "chkout").click()

if __name__ == "__main__":
    main()
