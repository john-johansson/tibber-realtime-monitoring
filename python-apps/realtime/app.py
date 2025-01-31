#!/usr/bin/env python3

import influxdb_client
import asyncio
import aiohttp
import tibber
import configparser
import os
from influxdb_client.client.write_api import SYNCHRONOUS

conf = configparser.ConfigParser()
conf.read('config.ini')

client = influxdb_client.InfluxDBClient(
   url = os.environ['INFLUXDB_SERVICE_HOST_PORT'],
   token = os.environ.get('INFLUXDB_TOKEN'),
   org = os.environ.get('INFLUXDB_ORG')
)

write_api = client.write_api(write_options=SYNCHRONOUS)

def _writeInflux(field, value):
    p = influxdb_client.Point("tibber").field(field, value)
    write_api.write(bucket=os.environ.get('INFLUXDB_BUCKET'), org=os.environ.get('INFLUXDB_ORG'), record=p)

def _callback(pkg):
    data = pkg.get("data")
    if data is None:
        return
    payload=data.get("liveMeasurement")
    _writeInflux('accumulatedConsumption', float(payload['accumulatedConsumption']))
    _writeInflux('accumulatedConsumptionLastHour', float(payload['accumulatedConsumptionLastHour']))
    _writeInflux('accumulatedCost', float(payload['accumulatedCost']))
    _writeInflux('averagePower', float(payload['averagePower']))
    _writeInflux('currentL1', int(payload['currentL1']))
    _writeInflux('currentL2', float(payload['currentL2']))
    _writeInflux('currentL3', float(payload['currentL3']))
    _writeInflux('lastMeterConsumption', float(payload['lastMeterConsumption']))
    _writeInflux('maxPower', int(payload['maxPower']))
    _writeInflux('minPower', int(payload['minPower']))
    _writeInflux('power', int(payload['power']))
    _writeInflux('powerFactor', float(payload['powerFactor']))
#    _writeInflux('signalStrength', payload['signalStrength'])
    _writeInflux('voltagePhase1', float(payload['voltagePhase1']))
    _writeInflux('voltagePhase2', float(payload['voltagePhase2']))
    _writeInflux('voltagePhase3', float(payload['voltagePhase3']))
    _writeInflux('estimatedHourConsumption', payload['estimatedHourConsumption'])

async def run():
    async with aiohttp.ClientSession() as session:
        tibber_connection = tibber.Tibber(os.environ['TIBBER_TOKEN'], websession=session, user_agent="baltimore")
        await tibber_connection.update_info()
    home = tibber_connection.get_homes()[0]
    await home.rt_subscribe(_callback)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    asyncio.ensure_future(run())
    loop.run_forever()
