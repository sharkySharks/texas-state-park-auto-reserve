# Texas State Park Auto Reserve

An application that automates making Texas State Park reservations through the [Texas State Park website](https://texasstateparks.reserveamerica.com/).

## Why does this application exist?
I made this app due to the high volume of people making reservations to visit Texas State Parks during the global pandemic, which has caused the parks to reach daily capacity. Sometimes reservations are cancelled, but the Texas State Park website does not have a notification system to let you know.  

Rather than manually checking back in on the website every few hours and potentially missing an opportunity to book a coveted slot that someone gives up, I built this application to check the website for me for any openings on specific days I want to book and if a slot opens up it will reserve a spot for me.

## Can other people use the application?
Yes, though I did make this with a specific reservation in mind, in theory this should work for any Texas Park reservation through the above website. 

Fill in your personal request information in a .env file, following the `sample.env` file, make sure you have login credentials for the Texas State Park website, and run the application.

### Run the app:

1. Copy `reservation_details.sample.json` to `reservation_details.json` and fill in all of the fields.
1. Copy `sample.env` to `.env` and fill in your Texas State Park username and password. This will be used to make your reservation.
1. Run the following commands to run the application:

```
python3 -m venv ENV
source ENV/bin/activate
pip3 install -r requirements.txt
python3 app.py

# run this command to exit venv activate mode and return to regular shell environment
deactivate
```
### Values for reservation_details.json
There are limited options supported at this time. Some options will have some defaults that you can edit after your reservation is made.

| Key                              | Default Values (type)         | Description  |
|---                               |---                            |---           |
| `destination`                    | `""` (string)                 | The Texas State Park you want to visit - should be the first result when searching on the website. |
| `interest`                       | `""` (string)                 | Options: `camping` or `day pass` |
| `arrival_date`                   | `"MM/DD/YYYY"` (string)       | First day you want to visit, format is important: `MM/DD/YYYY` |
| `days_of_stay`                   | `0` (integer)                 | Number of days you want to stay |
| `number_of_vehicles`             | `1` (integer)                 | how many vehicles |
| `type_of_vehicle`                | `""` (string)                 | type of vehicle. options: `car`, `truck`, `suv`, `van` |
| `number_of_adults`               | `0` (integer)                 | how many adults are going |
| `number_of_children`             | `0` (integer)                 | how many children are going |
| `wait_for_opening`               | `false` (bool)                | continuously check for an opening and auto book when one is available |
| `camp_site_selection`            | empty strings object          | Camp Site Options |
| `camp_site_selection.type`       | `""` (string)                 | Camp Site type. Supported options: `tent` |
| `camp_site_selection.preference` | `"any"` (string)              | Camp Site preference. Supported options: `electric`, `primitive`, `any` |
| `day_pass_selection`             | empty strings object          | Day Pass Options |
| `day_pass_selection.preferences` | `[ "either" ]` (array)        | length should match `days_of_stay`. values are: `morning`, `afternoon`, `either` |
| `credit_card`                    | empty strings object          | credit card information for booking |

## What is the application doing exactly?
I use [selenium web driver for python](https://selenium-python.readthedocs.io/index.html) to navigate to the Texas State Park website, login, and go through the reservation steps. If the days the requestor want to go to the park are available, then I look at the requestor's preferences for morning or afternoon visitation and make the reservation, including payment. 

If the dates are already booked then the application continuously checks for availability on the requested days until either, a) an available spot opens up, then it books the opening, or b) stops after the requestor's visitation date has passed.

## Future Features

"...a work is never truly completed [...] but abandoned..." Paul Valéry

Nice-to-have features:
- add features for reserving more camp grounds. currently only `tent` camp option is available
- add json value validation for `reservation_details.json` and validate against website limits
- replace `time.sleep` with `WebDriverWait` - better practice with selenium to wait for an element than an arbitrary sleep time
- add deploy code for application so that people do not have to run the code locally on their computer
- add testing

## Questions or feedback?
Feel free to submit a github issue or pull request
