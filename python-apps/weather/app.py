#!/usr/bin/python3

import requests
import influxdb_client
import asyncio
import os
from influxdb_client.client.write_api import SYNCHRONOUS

weathermap_token = os.environ.get('WEATHERMAP_TOKEN')
weathermap_location = os.environ.get('WEATHERMAP_LOCATION')
weathermap_url = 'https://api.openweathermap.org/data/2.5/weather?{}&appid={}&units=metric'.format(weathermap_location, weathermap_token)

response = requests.get(weathermap_url)

payload = response.json()

client = influxdb_client.InfluxDBClient(
   url = os.environ['INFLUXDB_SERVICE_HOST_PORT'],
   token = os.environ.get('INFLUXDB_TOKEN'),
   org = os.environ.get('INFLUXDB_ORG')
)
write_api = client.write_api(write_options=SYNCHRONOUS)

p = influxdb_client.Point("weather").field("temp", payload["main"]["temp"])
write_api.write(bucket=os.environ.get('INFLUXDB_BUCKET'), org=os.environ.get('INFLUXDB_ORG'), record=p)
p = influxdb_client.Point("weather").field("pressure", payload["main"]["pressure"])
write_api.write(bucket=os.environ.get('INFLUXDB_BUCKET'), org=os.environ.get('INFLUXDB_ORG'), record=p)
p = influxdb_client.Point("weather").field("humidity", payload["main"]["humidity"])
write_api.write(bucket=os.environ.get('INFLUXDB_BUCKET'), org=os.environ.get('INFLUXDB_ORG'), record=p)
p = influxdb_client.Point("weather").field("wind_speed", payload["wind"]["speed"])
write_api.write(bucket=os.environ.get('INFLUXDB_BUCKET'), org=os.environ.get('INFLUXDB_ORG'), record=p)
p = influxdb_client.Point("weather").field("wind_deg", payload["wind"]["deg"])
write_api.write(bucket=os.environ.get('INFLUXDB_BUCKET'), org=os.environ.get('INFLUXDB_ORG'), record=p)
