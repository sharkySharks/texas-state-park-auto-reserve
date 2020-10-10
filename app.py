import json
import os
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
        
    sign_in()
    search_for_location()
    reserve(wait_for_opening=rd["wait_for_opening"])

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

def reserve(wait_for_opening=False):
    # get current availability
    locals()[f'{rd["destination"]} Schedule'] = {}
    for x in range(rd["days_of_stay"]):
        calendar_day = driver.find_elements_by_css_selector(f"div.matrixheader div.calendar div.date")[x].text
        calendar_weekday = driver.find_elements_by_css_selector(f"div.matrixheader div.calendar div.weekday")[x].text
        
        locals()[f'{rd["destination"]} Schedule'][f'{calendar_weekday}-{calendar_day}'] = {}
        morning = driver.find_elements_by_css_selector(f"div.matrixrow div.status:nth-of-type({x+1})")[0]
        afternoon = driver.find_elements_by_css_selector(f"div.matrixrow div.status:nth-of-type({x+1})")[1]
        locals()[f'{rd["destination"]} Schedule'][f'{calendar_weekday}-{calendar_day}']["morning"] = morning.get_attribute("title")
        locals()[f'{rd["destination"]} Schedule'][f'{calendar_weekday}-{calendar_day}']["afternoon"] = afternoon.get_attribute("title")
    
    print(f'Day Pass Availability for {rd["days_of_stay"]} day pass(es) starting on {rd["arrival_date"]}:')
    print(locals()[f'{rd["destination"]} Schedule'])


if __name__ == "__main__":
    main()