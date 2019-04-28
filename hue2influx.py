#!/usr/bin/env python3
# coding=utf8

import os
import signal
import time
import datetime
from influxdb import InfluxDBClient
from phue import Bridge

HUE_BRIDGE      =  os.getenv('HUE_BRIDGE', None)
INFLUXDB_SERVER =  os.getenv('INFLUXDB_SERVER', None)
INFLUXDB_PORT   =  os.getenv('INFLUXDB_PORT', 8086)
INFLUXDB_UDP    = (os.getenv('INFLUXDB_UDP', "0") == "1")
INFLUXDB_DB     =  os.getenv('INFLUXDB_DB', None)
INFLUXDB_USER   =  os.getenv('INFLUXDB_USER', None)
INFLUXDB_PASS   =  os.getenv('INFLUXDB_PASS', None)

class Hue2Influx:
    def __init__(self):
        if HUE_BRIDGE == None or HUE_BRIDGE == '':
            print('Please set the environment variable HUE_BRIDGE to the IP/hostname of your Hue Bridge!')
            exit(-1)

        self._hue = Bridge(HUE_BRIDGE)
        self._data_sensors = []
        self._data_lights = []

        self._influxdb = None
        self._data_influx = []

        if INFLUXDB_SERVER == None or INFLUXDB_SERVER == "" or INFLUXDB_DB == None or INFLUXDB_DB == "":
            print("Please set at least the environment variables INFLUXDB_SERVER and INFLUXDB_DB!")
            exit(-1)

        if INFLUXDB_UDP == False:
            self._influxdb = InfluxDBClient(host=INFLUXDB_SERVER, port=INFLUXDB_PORT, database=INFLUXDB_DB, username=INFLUXDB_USER, password=INFLUXDB_PASS)
        else:
            self._influxdb = InfluxDBClient(host=INFLUXDB_SERVER, use_udp=True, udp_port=INFLUXDB_PORT, database=INFLUXDB_DB, username=INFLUXDB_USER, password=INFLUXDB_PASS)


    def run(self):
        print("hue2influx running ...")
        while True:
            self.sync_sensors()
            self.sync_lights()
            time.sleep(60)

    def _get_sensors(self):
        self._data_sensors = self._hue.get_sensor_objects('id')
        return True

    def _convert_sensors_to_influx(self):
        for sensor_key in self._data_sensors:
            sensor = self._data_sensors[sensor_key]._get(None)

            measurement = {
                "measurement": "hue-sensors",
                "tags": {
                    "name": sensor['name'],
                    "type": sensor['type'],
                    "modelid": sensor['modelid'],
                    "manufacturername": sensor['manufacturername'],
                    "productname": sensor['productname'] if 'productname' in sensor else '',
                    "on": sensor['config']['on'] if 'config' in sensor and 'on' in sensor['config'] else True
                },
                "time": datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(),
                "fields": {
                    "reachable": sensor['config']['reachable'] if 'config' in sensor and 'reachable' in sensor['config'] else True,
                    "battery": sensor['config']['battery'] if 'config' in sensor and 'battery' in sensor['config'] else -1,
                    "sensitivity": sensor['config']['sensitivity'] if 'config' in sensor and 'sensitivity' in sensor['config'] else -1,
                    "sensitivitymax": sensor['config']['sensitivitymax'] if 'config' in sensor and 'sensitivitymax' in sensor['config'] else -1,
                    "tholddark": sensor['config']['tholddark'] if 'config' in sensor and 'tholddark' in sensor['config'] else -1,
                    "tholdoffset": sensor['config']['tholdoffset'] if 'config' in sensor and 'tholdoffset' in sensor['config'] else -1,
                }
            }

            for state_key in sensor['state']:
                state_value = sensor['state'][state_key]

                if state_key == 'lastupdated':
                    continue
                elif state_key == 'temperature':
                    measurement['fields'][state_key] = state_value / 100
                elif type(state_value) is dict:
                    measurement['fields'].update(self._flatten_dict(state_key, state_value))
                elif type(state_value) is list:
                    measurement['fields'].update(self._flatten_list(state_key, state_value))
                else:
                    measurement['fields'][state_key] = state_value

            self._data_influx.append(measurement)
        return self._data_influx

    def _get_lights(self):
        self._data_lights = self._hue.get_light_objects('id')
        return True

    def _convert_lights_to_influx(self):
        for light_key in self._data_lights:
            light = self._data_lights[light_key]._get(None)

            measurement = {
                "measurement": "hue-lights",
                "tags": {
                    "name": light['name'],
                    "type": light['type'],
                    "modelid": light['modelid'],
                    "manufacturername": light['manufacturername'],
                    "productname": light['productname'] if 'productname' in light else '',
                    "productid": light['productid'] if 'productid' in light else '',
                    "archetype": light['config']['archetype'] if 'config' in light and 'archetype' in light['config'] else '',
                    "function": light['config']['function'] if 'config' in light and 'function' in light['config'] else '',
                    "direction": light['config']['direction'] if 'config' in light and 'direction' in light['config'] else ''
                },
                "time": datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(),
                "fields": {
                }
            }

            for state_key in light['state']:
                state_value = light['state'][state_key]

                if type(state_value) is dict:
                    measurement['fields'].update(self._flatten_dict(state_key, state_value))
                elif type(state_value) is list:
                    measurement['fields'].update(self._flatten_list(state_key, state_value))
                else:
                    measurement['fields'][state_key] = state_value
            self._data_influx.append(measurement)
        return self._data_influx

    def _flatten_dict(self, key_name, the_dict):
        flat_dict = {}

        for dict_key in the_dict:
            dict_value = the_dict[dict_key]
            flat_key = key_name + "_" + dict_key

            if type(dict_value) is dict:
                flat_dict.update(self._flatten_dict(flat_key, dict_value))
            elif type(dict_value) is list:
                flat_dict.update(self._flatten_list(flat_key, dict_value))
            else:
                flat_dict[flat_key] = dict_value
        return flat_dict

    def _flatten_list(self, key_name, the_list):
        flat_dict = {}

        for list_index in range(len(the_list)):
            list_value = the_list[list_index]
            flat_key = key_name + "_" + str(list_index)

            if type(list_value) is dict:
                flat_dict.update(self._flatten_dict(flat_key, list_value))
            elif type(list_value) is list:
                flat_dict.update(self._flatten_list(flat_key, list_value))
            else:
                flat_dict[flat_key] = list_value
        return flat_dict

    def _put_influx(self):
        success = self._influxdb.write_points(self._data_influx)

        if success == True:
            self._data_influx = []

        return success

    def sync_sensors(self):
        self._get_sensors()
        self._convert_sensors_to_influx()
        return self._put_influx()

    def sync_lights(self):
        self._get_lights()
        self._convert_lights_to_influx()
        return self._put_influx()

def quit(signum, frame):
    signal.signal(signal.SIGINT, original_sigint)
    print("Goodbye!")
    exit(0)

if __name__ == '__main__':
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, quit)

    hue2influx = Hue2Influx()
    hue2influx.run()

