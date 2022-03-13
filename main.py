from datetime import datetime
import pytz
import json
from string import Template

import requests

API_KEY = "e70463ce026e9c78bcc76377bc391cb9"

EXCLUDE = "minutely,hourly,alerts"

GEO_URL_TEMPLATE = Template(f"http://api.openweathermap.org/geo/1.0/"
                            f"direct?q=$city,$country&limit=1&appid={API_KEY}")

URL_TEMPLATE = Template(
    f"https://api.openweathermap.org/data/2.5/"
    f"onecall?lat=$latitude&lon=$longitude&exclude={EXCLUDE}&appid={API_KEY}&units=$units"
)

UNITS = {
    "Celsius": "metric",
    "Fahrenheit": "imperial",
    "Kelvin": "standart",
}


class Weather:
    def __init__(self, city, country, units):
        self.city = city
        self.country = country
        self.units = units
        self.longitude = None
        self.latitude = None
        self.timezone = None
        self.offset = None

    def get_coords(self, url):
        r = requests.get(url)

        status_code = r.status_code

        if status_code == 200:
            content = json.loads(r.content)
            if content:
                self.longitude = content[0].get('lon', None)
                self.latitude = content[0].get('lat', None)
        return status_code

    def datetime_from_seconds(self, seconds: int) -> datetime:
        return datetime.utcfromtimestamp(seconds + self.offset)

    def get_daily_info(self, info):
        days = []
        info.pop(0)
        for day in info:
            date = self.datetime_from_seconds(day["dt"]).date().strftime("%A %d-%m-%y")
            weather_description = day["weather"][0]["description"]
            morning_temp = day["temp"]["morn"]
            day_temp = day["temp"]["day"]
            night_temp = day["temp"]["night"]
            temperature_info = f"morning: {morning_temp}, day: {day_temp}, night: {night_temp}"
            days.append(f"{date} temperature {temperature_info}, {weather_description}")
        return days

    def time_from_seconds(self, seconds):
        time_ = self.datetime_from_seconds(seconds).time()
        return time_.replace(tzinfo=self.timezone)

    def get_current_info(self, current_info):
        temperature = current_info["temp"]
        feels_like = current_info["feels_like"]
        wind_speed = current_info["wind_speed"]
        sunrise = self.time_from_seconds(current_info["sunrise"]).strftime("%H:%M:%S")
        sunset = self.time_from_seconds(current_info["sunset"]).strftime("%H:%M:%S")
        now = self.datetime_from_seconds(current_info["dt"])
        current_info = f"Now {now}, temperature is {temperature}, feels like as {feels_like}, " \
                       f"wind speed is {wind_speed}m/s, sunrise at {sunrise}, sunset at {sunset}"
        return current_info

    def get_weather_info(self):
        url = URL_TEMPLATE.substitute(
            longitude=self.longitude,
            latitude=self.latitude,
            units=self.units
        )
        r = requests.get(url)
        if r.status_code == 200:
            content = json.loads(r.content)
            self.timezone = pytz.timezone(content["timezone"])
            self.offset = content["timezone_offset"]
            current_info = self.get_current_info(content["current"])
            daily_info = self.get_daily_info(content["daily"])
            return current_info, daily_info
        else:
            return "Can't get info from server.", ""

    def get_info(self):
        geo_url = GEO_URL_TEMPLATE.substitute(city=self.city, country=self.country)

        status_code = self.get_coords(geo_url)
        if all([status_code != 200, self.longitude, self.latitude]):
            print("Wrong city or country. Exit.")
            return

        current_info, daily_info = self.get_weather_info()
        if weather:
            print(current_info)
            print(*daily_info, sep="\n")


def get_user_input():
    units = "standart"
    e_units = list(enumerate(UNITS.keys()))
    city = input("Enter city name: ")
    country = input("Enter country name: ")
    print("Choose unit of measurement:")
    print(*[f"{unit[0]} for {unit[1]}" for unit in e_units], sep="\n")
    e_unit = input()
    if e_unit.isdigit() and int(e_unit) in range(len(e_units)):
        units = UNITS[e_units[int(e_unit)][1]]
    else:
        print("You choose haven't exist. We use Kelvin.")
    return city, country, units


if __name__ == '__main__':
    city, country, units = get_user_input()
    weather = Weather(city, country, units)
    weather.get_info()
