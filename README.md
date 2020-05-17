# Air Filter Countdown

## Introduction

This project creates a sensor that tracks when the HVAC filter is changed, and sends an alert when it needs to be changed 90 days later.

I'm using a Wyze sense door sensor to trigger the automation when the filter cover is opened, but any door sensor can be used. I set up the the Wyze sensors using this integration: (https://github.com/kevinvincent/ha-wyzesense)

![Air Filter Actionable Notification](https://i.imgur.com/dlOt5QC.jpg)

I used one of HA’s helpers to set up a input_datetime entity. I created this in the UI by going to Configuration/Helpers and clicking the add button, then “Date and/or time.” I then added a name, in my case “Air Filter Date Installed”. This entity will be used to set the date that the air filter was changed so that data can be sent to a python script. 

A python script needs to be run in order to calculate the days after an input date, and there will also be an actionable push notification on iOS, so configuration.yaml must include the following:

## configuration.yaml:
```
###Air Filter Date Reminder Requires This###
python_script:

###For Actionable Push Notification###
ios:
  push:
    categories:
      - name: Air Filter Confirm
        identifier: 'airfilterconfirm'
        actions:
          - identifier: 'CONFIRM_AIRFILTER'
            title: 'I changed the filter.'
          - identifier: 'CANCEL_AIRFILTER'
            title: 'I did not change the filter.'
```

## The Python Script:

I modified this project by mf-social https://github.com/mf-social/ps-date-countdown to change the calculation to 90 days from the current date, instead of a yearly occurrence. It requires an automation to run the script every day or each time HA is restarted in order to update the countdown, and to set the parameters of the reminder. The script must be placed in the /config/python_scripts/ directory. (Create it if it doesn't exist - I created a new file called 'date_countdown.py' in this directory and populated it with the following code:


## /config/python_scripts/date_countdown.py

```
"""       Requires python_script: to be enabled in configuration           """


""" Usage:                                                                 """
"""                                                                        """
""" automation:                                                            """
"""   alias: Air filter reminder sensor                                    """
"""   trigger:                                                             """
"""     platform: time                                                     """
"""     at: '00:00:01'                                                     """
"""   action:                                                              """
"""     service: python_script.date_countdown                              """
"""     data:                                                              """
"""       name: Air Filter                                                 """
"""       type: reminder                                                   """
"""       date: 2020-05-12   #YYYY-MM-DD                                   """


"""  This will create a sensor with entity_id sensor.reminder_air_filter   """
"""  with a friendly name of 'Air Filter reminder'.  The sensors value     """
"""  will be the number of days until the 90 days after the date the       """
"""          filter was installed.                                         """



today = datetime.datetime.now().date()

name = data.get('name')
type = data.get('type')
sensorName = "sensor.{}_{}".format(type , name.replace(" " , "_"))

dateStr = data.get('date')
dateSplit = dateStr.split("-")

dateDay = int(dateSplit[2])
dateMonth = int(dateSplit[1])
dateYear =  int(dateSplit[0])
date = datetime.date(dateYear,dateMonth,dateDay)

nextOccur = date + datetime.timedelta(days=90)

numberOfDays = (nextOccur - today).days

hass.states.set(sensorName , numberOfDays ,
  {
    "icon" : "mdi:calendar-star" ,
    "unit_of_measurement" : "days" ,
    "friendly_name" : "{} {}".format(name, type)
  }
)
```
Change the following section in the script to change the amount of days in your countdown.
```
nextOccur = date + datetime.timedelta(days=90)
```
For example, for 30 days, change this section to:
```
nextOccur = date + datetime.timedelta(days=30)
```
# Automations:

The first automation will run the python script once a day at the start of the day, or when HA is restarted, and will set the python script data for date, name, and type.
```
- alias: Air Filter - Reminder - Refresh date countdown sensors
  trigger:
  - at: 00:00:01
    platform: time
  - event: start
    platform: homeassistant
  action:
  - service: python_script.date_countdown
    data_template:
      date: '{{ states(''input_datetime.air_filter_date_installed'') }}'
      name: Air Filter
      type: reminder
  initial_state: true
```
Next we need an automation to trigger an actionable notification when the HVAC filter cover is opened. This is triggered by the Wyze door sensor, and prompts me to confirm the filter was changed. If you wanted, you could skip the actionable notification and just have the sensor trigger set the date that the filter was changed directly (essentially combining this automation with the next), but I wanted to have the extra control in case the filter cover was opened for any other reason.

![Air Filter Actionable Notification](https://i.imgur.com/bh9380X.jpg)

```
- alias: Air Filter - Open Detected - Send iOS Actionable Notification
  description: ''
  trigger:
  - entity_id: binary_sensor.wyzesense_77842647
    platform: state
    to: 'on'
  condition: []
  action:
  - data:
      data:
        push:
          category: airfilterconfirm
      message: Did you change the AC filter?
      title: AC Filter Cover Opened
    service: notify.mobile_app_iphone
```
Then I need an automation to actually set the date triggered by my notification action. This uses the service input_datetime.set_datetime. This also triggers the automation to run the python script and get an updated countdown.
```
- alias: Air Filter - Set Date
  description: ''
  trigger:
  - event_data:
      actionName: CONFIRM_AIRFILTER
    event_type: ios.notification_action_fired
    platform: event
  condition: []
  action:
  - data_template:
      date: '{{ as_timestamp(now())|timestamp_custom(''%Y-%m-%d'') }}'
    entity_id: input_datetime.air_filter_date_installed
    service: input_datetime.set_datetime
  - data: {}
    entity_id: automation.reminder_refresh_date_countdown_sensors
    service: automation.trigger
```
Lastly, I need an automation that reminds me when the countdown is done and I need to change the filter again. I have it set up to remind me either when I get home or at 5 pm if I am already home.
```
- alias: Air Filter - Filter Needs to Be Changed
  description: ''
  trigger:
  - entity_id: person.me
    event: enter
    platform: zone
    zone: zone.home
  - at: '17:00:00'
    platform: time
  condition:
  - below: '1'
    condition: numeric_state
    entity_id: sensor.reminder_air_filter
  - condition: zone
    entity_id: person.me
    zone: zone.home
  action:
  - data:
      message: The AC Filter is due to be changed.
    service: notify.mobile_app_iphone
```
## Air Filter Sensor Card
To add a custom card in lovelace, I created the following sensor using the picture-elements card
![Air Filter Sensor Card](https://i.imgur.com/YNYpnG3.jpg)
```
elements:
  - entity: input_datetime.air_filter_date_installed
    style:
      bottom: 52%
      color: black
      font-size: 26px
      left: 4.5%
      transform: initial
    type: state-label
  - entity: sensor.reminder_air_filter
    style:
      bottom: 6%
      color: black
      font-size: 26px
      left: 4.5%
      transform: initial
    type: state-label
  - entity: automation.reminder_refresh_date_countdown_sensors
    state_image:
      'off': 'https://i.imgur.com/jsXMqex.png'
      'on': 'https://i.imgur.com/jsXMqex.png’
    style:
      left: 80%
      top: 50%
      width: 25%
    tap_action:
      action: call-service
      service: automation.trigger
      service_data:
        entity_id: automation.reminder_refresh_date_countdown_sensors
    type: image
image: 'https://i.imgur.com/OutUp0O.png’'
type: picture-elements
```
