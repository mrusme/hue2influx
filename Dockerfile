FROM python:3-alpine

RUN pip install --no-cache-dir influxdb phue

WORKDIR /srv
ADD ./hue2influx.py .

CMD [ "python", "/srv/hue2influx.py" ]
