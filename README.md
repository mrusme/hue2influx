hue2influx
----------

Sync Philips Hue component states to InfluxDB.

## Environment variables

```sh
HUE_BRIDGE="your bridge IP or hostname here"
INFLUXDB_SERVER="your InfluxDB server IP or hostname here"
INFLUXDB_PORT=your InfluxDB port (tcp or udp) here
INFLUXDB_UDP="0" for TCP, "1" for UDP
INFLUXDB_DB="your InfluxDB database here"
INFLUXDB_USER="your InfluxDB username here"
INFLUXDB_PASS="your InfluxDB password here"
```

## Running locally

```sh
$ pip3 install influxdb phue
$ python3 ./hue2influx.py
```

## Docker

```sh
docker run -it --rm -e HUE_BRIDGE="your bridge IP or hostname here" -e INFLUXDB_SERVER="your InfluxDB server IP or hostname here" -e ... mrusme/hue2influx:latest
```
