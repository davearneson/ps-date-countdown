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
