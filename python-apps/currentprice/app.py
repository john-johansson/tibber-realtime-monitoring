#!/usr/bin/python3

import influxdb_client
import asyncio
import tibber
import os
from influxdb_client.client.write_api import SYNCHRONOUS


client = influxdb_client.InfluxDBClient(
   url = os.environ['INFLUXDB_SERVICE_HOST_PORT'],
   token = os.environ.get('INFLUXDB_TOKEN'),
   org = os.environ.get('INFLUXDB_ORG')
)

write_api = client.write_api(write_options=SYNCHRONOUS)

async def main():
    access_token = os.environ.get('TIBBER_TOKEN')
    tibber_connection = tibber.Tibber(access_token)
    await tibber_connection.update_info()
    home = tibber_connection.get_homes()[0]
    await home.update_info()
    await home.update_price_info()

    await tibber_connection.close_connection()
    p = influxdb_client.Point("tibber").field("cost", home.current_price_info["total"])
    write_api.write(bucket=os.environ.get('INFLUXDB_BUCKET'), org=os.environ.get('INFLUXDB_ORG'), record=p)

if __name__ ==  '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
