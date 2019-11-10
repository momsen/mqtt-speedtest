import argparse, re, time, subprocess, os, sys, traceback, json
import paho.mqtt.publish as publish
from configparser import SafeConfigParser

def run_speedtest():
    proc = subprocess.Popen('speedtest-cli --simple', shell=True, stdout=subprocess.PIPE)
    try:
        outs, errs = proc.communicate(timeout=300)
    except subprocess.TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate()
    result = outs.decode('UTF-8')
    ping = re.findall('Ping:\s(.*?)\s', result, re.MULTILINE)
    download = re.findall('Download:\s(.*?)\s', result, re.MULTILINE)
    upload = re.findall('Upload:\s(.*?)\s', result, re.MULTILINE)

    ping[0] = ping[0].replace(',', '.')
    download[0] = download[0].replace(',', '.')
    upload[0] = upload[0].replace(',', '.')
    return (ping[0], download[0], upload[0])

def create_discovery_message(name, state_topic, unit):
    return json.dumps({'name': name, 'state_topic': state_topic, 'unit_of_meas': unit})

def publish_messages(ping, upload, download, cfg):
    auth = {'username': cfg['mqtt']['user'], 'password': cfg['mqtt']['pw']}
    discovery_msgs = [(cfg['upload']['discovery_topic'], create_discovery_message(cfg['upload']['discovery_name'], cfg['upload']['state_topic'], 'MBit/s'), 0, True),\
                     (cfg['download']['discovery_topic'], create_discovery_message(cfg['download']['discovery_name'], cfg['download']['state_topic'], 'MBit/s'), 0, True),\
                     (cfg['ping']['discovery_topic'], create_discovery_message(cfg['ping']['discovery_name'], cfg['ping']['state_topic'], 'ms'), 0, True)]
    try:
        publish.multiple(discovery_msgs, hostname=cfg['mqtt']['host'], client_id=cfg['mqtt']['client_id'], port=cfg['mqtt']['port'], auth=auth)
    except ConnectionError:
        print("Unable to publish discovery messages via mqtt:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

    state_msgs = [(cfg['ping']['state_topic'], ping, 0, False),\
                  (cfg['upload']['state_topic'], upload, 0, False),\
                  (cfg['download']['state_topic'], download, 0, False)]
    try:
        publish.multiple(state_msgs, hostname=cfg['mqtt']['host'], client_id=cfg['mqtt']['client_id'], port=cfg['mqtt']['port'], auth=auth)
    except ConnectionError:
        print("Unable to publish state messages via mqtt:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

def read_config(filename):
    parser = SafeConfigParser()
    found = parser.read(filename)
    if not filename in found:
        print("The ini file " + filename + " was not found.", file=sys.stderr)
        sys.exit(-1)

    cfg = {}
    for section_definition in [ { 'name': 'mqtt', 'parameters': [ 'host', 'port', 'client_id', 'user', 'pw'] },\
                                { 'name': 'upload', 'parameters': ['discovery_topic', 'discovery_name', 'state_topic']},\
                                { 'name': 'download', 'parameters': ['discovery_topic', 'discovery_name', 'state_topic']},\
                                { 'name': 'ping', 'parameters': ['discovery_topic', 'discovery_name', 'state_topic']}]:

        section_name = section_definition['name']

        section = {}
        for parameter in section_definition['parameters']:
            if not parser.has_option(section_name, parameter):
                print("Parameter '" + parameter + "' is missing in section '" + section_name + "'", file=sys.stderr)
                sys.exit(-1)
            section[parameter] = parser.get(section_name, parameter)

        cfg[section_name] = section

    try:
        cfg['mqtt']['port'] = int(cfg['mqtt']['port'])
    except ValueError:
        print("The port " + cfg['mqtt']['port'] + " cannot be parsed as integer.", file=sys.stderr)
        sys.exit(-1)

    return cfg

parser = argparse.ArgumentParser(description="Run speedtest and publish results via mqtt.")
parser.add_argument("inifile", type=str, action="store", help="name of the ini file")
args = parser.parse_args()

cfg = read_config(args.inifile)
ping, download, upload = run_speedtest()
#ping, download, upload = (10, 200,100)
publish_messages(ping, upload, download, cfg)

print('{};{};{};{};{}'.format(time.strftime('%y/%m/%d'), time.strftime('%H:%M'), ping, download, upload))
