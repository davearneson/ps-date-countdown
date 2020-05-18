# Air Filter Countdown

## Introduction

This project creates a sensor that tracks when the HVAC filter is changed, and sends an alert when it needs to be changed 90 days later.

I'm using a Wyze sense door sensor to trigger the automation when the filter cover is opened, but any door sensor can be used. I set up the the Wyze sensors using this integration: ([https://github.com/kevinvincent/ha-wyzesense](https://github.com/kevinvincent/ha-wyzesense))

&#x200B;

https://preview.redd.it/889lwwlqrez41.jpg?width=2345&format=pjpg&auto=webp&s=d260b43be4fb77a00be84f8028693e39cade1872

I used one of HA’s helpers to set up a input\_datetime entity. I created this in the UI by going to Configuration/Helpers and clicking the add button, then “Date and/or time.” I then added a name, in my case “Air Filter Date Installed”. This entity will be used to set the date that the air filter was changed so that data can be sent to a python script.

A template sensor needs to be set up in order to calculate the days after an input date, and there will also be an actionable push notification on iOS, so configuration.yaml must include the following:

```
## configuration.yaml:

### Required Sensors ###
sensor:
- platform: time_date
  display_options:
      - 'time'
      - 'date'
      - 'date_time'
      - 'date_time_utc'
      - 'date_time_iso'
      - 'time_date'
      - 'time_utc'
      - 'beat'
      
- platform: template
  sensors:
    air_filter_life_remaining:
        value_template: >
          {{(((as_timestamp(states.input_datetime.air_filter_date_installed.state) + (90 * 86400) ) - as_timestamp(states.sensor.date.state)) /86400)|round(0)}} days
    
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

# About the template sensor:

I really struggled with this part in the original project, and after posting on Reddit, received some much appreciated guidance from u/DER31K which can be seen in the comments below. Essentially, I couldn't figure out how to get a template to add 90 days to a date, but if you convert the date to a timestamp, it becomes much easier to work with. This bypasses the need for the python script entirely, and makes this whole project much simpler. u/DER31K's template is explained below. 86400 is seconds in a day.

{{(((as_timestamp(states.input_datetime.air_filter_date_installed.state) + (90 * 86400) ) - as_timestamp(states.sensor.date.state)) /86400)|round(0)}}

So this is.... Date filter last changed + 90 days - today's date = days until the next filter change based on it needing be to done 90 days after the last filter change.

# Automations:

The first automation will send an actionable notification when the HVAC filter cover is opened. This is triggered by the Wyze door sensor, and prompts me to confirm the filter was changed. If you wanted, you could skip the actionable notification and just have the sensor trigger set the date that the filter was changed directly (essentially combining this automation with the next), but I wanted to have the extra control in case the filter cover was opened for any other reason.

&#x200B;

https://preview.redd.it/syr36tatrez41.jpg?width=828&format=pjpg&auto=webp&s=4dca6d07a789b2c707bb3c9dfce84a9c4522cbc1

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

Then I need an automation to actually set the date triggered by my notification action. This uses the service input\_datetime.set\_datetime.

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

Lastly, I need an automation that reminds me when the countdown is done and I need to change the filter again. I have it set up to remind me either when I get home or at 5 pm if I am already home.

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

## Air Filter Sensor Card

To add a custom card in lovelace, I created the following sensor using the picture-elements card. 

&#x200B;

https://preview.redd.it/culwd8bwrez41.jpg?width=828&format=pjpg&auto=webp&s=8a561d892f34fb34528f6d79724393f0eb1eb2e2

    elements:
      - entity: input_datetime.air_filter_date_installed
        style:
          bottom: 52%
          color: black
          font-size: 26px
          left: 4.5%
          transform: initial
        type: state-label
      - entity: sensor.air_filter_life_remaining
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
