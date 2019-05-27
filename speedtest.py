import os
import re
import subprocess
import time

import argparse
import paho.mqtt.publish as publish

def run_speedtest():
    response = subprocess.Popen('speedtest-cli --simple', shell=True, stdout=subprocess.PIPE).stdout.read()
    ping = re.findall('Ping:\s(.*?)\s', response, re.MULTILINE)
    download = re.findall('Download:\s(.*?)\s', response, re.MULTILINE)
    upload = re.findall('Upload:\s(.*?)\s', response, re.MULTILINE)

    ping[0] = ping[0].replace(',', '.')
    download[0] = download[0].replace(',', '.')
    upload[0] = upload[0].replace(',', '.')
    return (ping[0], download[0], upload[0])

def publish_messages(ping, upload, download, mqtt_config):
    msgs = [(mqtt_config.mqttpingtopic, ping, 0, False), (mqtt_config.mqttuploadtopic, upload, 0, False), (mqtt_config.mqttdownloadtopic, download, 0, False)]
    publish.multiple(msgs, hostname=mqtt_config.mqtthost, client_id=mqtt_config.mqttclientid, port=mqtt_config.mqttport)

parser = argparse.ArgumentParser(description="Run speedtest and publish results via mqtt.")
parser.add_argument("-mh", "--mqtt-host", type=str, action="store", dest="mqtthost", help="host of the mqtt broker", default="localhost")
parser.add_argument("-mp", "--mqtt-port", type=int, action="store", dest="mqttport", help="port of the mqtt broker", default=1883)
parser.add_argument("-mc", "--mqtt-client-id", type=str, action="store", dest="mqttclientid", help="client id of the published messages", default="speedtest")
parser.add_argument("-tp", "--mqtt-ping-topic", type=str, action="store", dest="mqttpingtopic", help="Topic of the measured ping data", default="/network/speedtest/ping")
parser.add_argument("-tu", "--mqtt-upload-topic", type=str, action="store", dest="mqttuploadtopic", help="Topic of the measrued upload data", default="/network/speedtest/upload")
parser.add_argument("-td", "--mqtt-download-topic", type=str, action="store", dest="mqttdownloadtopic", help="topic of the measured download data", default="/network/speedtest/download")

args = parser.parse_args()
ping, upload, download = run_speedtest()
publish_messages(ping, upload, download, args)

print('{};{};{};{};{}'.format(time.strftime('%y/%m/%d'), time.strftime('%H:%M'), ping, download, upload))

