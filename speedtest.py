import os
import re
import subprocess
import time

import sys
import paho.mqtt.publish as publish

topic = sys.argv[1]
mqtt_host = sys.argv[2]
mqtt_client_name = sys.argv[3]

response = subprocess.Popen('speedtest-cli --simple', shell=True, stdout=subprocess.PIPE).stdout.read()

ping = re.findall('Ping:\s(.*?)\s', response, re.MULTILINE)
download = re.findall('Download:\s(.*?)\s', response, re.MULTILINE)
upload = re.findall('Upload:\s(.*?)\s', response, re.MULTILINE)

ping[0] = ping[0].replace(',', '.')
download[0] = download[0].replace(',', '.')
upload[0] = upload[0].replace(',', '.')

msgs = [(topic + "/upload", upload[0], 0, False), (topic + "/download", download[0], 0, False), (topic + "/ping", ping[0], 0, False)]

publish.multiple(msgs, hostname=mqtt_host, client_id=mqtt_client_name)

print '{};{};{};{};{}'.format(time.strftime('%y/%m/%d'), time.strftime('%H:%M'), ping[0], download[0], upload[0])
