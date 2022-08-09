import requests
import urllib.parse
import mysql.connector
from datetime import datetime, timezone
import json
import config

CONFIG = config.Configuration()
DUCO_ROOT_ENDPOINT = str(urllib.parse.urlunparse(CONFIG.url('DUCO_ROOT_ENDPOINT')))
MYSQL_HOST = CONFIG.str('MYSQL_HOST')
MYSQL_PORT = CONFIG.int('MYSQL_PORT', 3306)
MYSQL_DB = CONFIG.str('MYSQL_DB', 'ducologger')
MYSQL_USER = CONFIG.str('MYSQL_USER')
MYSQL_PASSWORD = CONFIG.str('MYSQL_PASSWORD')

def getinfo():
    info = {
        'box': {
            'logtime': None,
            'mode': None, 
            'state': None,
            'level': None, 
            'cntdwn': None,
            'temp_oda': None,
            'temp_sup': None,
            'temp_eta': None,
            'temp_eha': None,
            'remainfilter_days': None,
            'remainfilter_percent': None,
            'bypass': None,
            'frost': None,
            'power': None,
            'has_control': None
        },
        'sensors': []
    }

    session = requests.Session()
    session.headers.update({'Accept': 'application/json', 'Content-Type': 'application/json'})
    logtime = datetime.now(tz=timezone.utc)
    
    try:
        url = f"{DUCO_ROOT_ENDPOINT}/board_info"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        board = response.json()
        info['box']['uptime'] = board['uptime']
        
        url = f"{DUCO_ROOT_ENDPOINT}/nodelist')"
        response = session.get(url, timeout=10)
        response.raise_for_status()     
        nodelist = response.json()['nodelist']

        location = None
        target = 0  
        for n in nodelist:
            url = f"{DUCO_ROOT_ENDPOINT}/nodeinfoget"
            response = session.get(url, params={'node': n}, timeout=10)
            response.raise_for_status()         
            node = response.json()

            if node['devtype'] == 'BOX':
                info['box']['logtime'] = logtime
                info['box']['mode'] = node['mode']
                info['box']['state'] = node['state']
                info['box']['level'] = node['trgt']
                info['box']['cntdwn'] = node['cntdwn']
                  
                url = f"{DUCO_ROOT_ENDPOINT}/boxinfoget')"
                response = session.get(url, timeout=10)
                response.raise_for_status()     
                box = response.json()

                info['box']['temp_oda'] = box['EnergyInfo']['TempODA']/10 # Outdoor air. Supply air from outdoors to the unit
                info['box']['temp_sup'] = box['EnergyInfo']['TempSUP']/10 # Supply air. Supply air from unit to house
                info['box']['temp_eta'] = box['EnergyInfo']['TempETA']/10 # Extract air. Supply air from the house to the unit
                info['box']['temp_eha'] = box['EnergyInfo']['TempEHA']/10 # Exhaust air. Exhaust air from the unit to outdoors        
                info['box']['remainfilter_days'] = box['EnergyInfo']['FilterRemainingTime']
                info['box']['remainfilter_percent'] = round(box['EnergyInfo']['FilterRemainingTime']/(365/2)*100)
                info['box']['bypass'] = box['EnergyInfo']['BypassStatus']
                info['box']['frost'] = box['EnergyInfo']['FrostProtState']
                info['box']['power'] = (box['EnergyFan']['SupplyFanPwmLevel'] + box['EnergyFan']['ExhaustFanPwmLevel'])/1000
            
            elif node['devtype'] == 'UCCO2' or node['devtype'] == 'UCRH' or (node['devtype'] == 'UC' and node['netw'] == 'VIRT'):
                sensor = {}
                sensor['logtime'] = logtime
                sensor['nid'] = n
                sensor['devtype'] = node['devtype']
                sensor['location'] = node['location']
                sensor['target'] = node['snsr']
                sensor['temp'] = None
                sensor['co2'] = None
                sensor['rh'] = None

                if node['devtype'] == 'UCCO2':
                    sensor['temp'] = node['temp']
                    sensor['co2'] = node['co2']
                elif node['devtype'] == 'UCRH':
                    sensor['temp'] = node['temp']
                    sensor['rh'] = node['rh']
                else: # (node['devtype'] == 'UC' and node['netw'] == 'VIRT')
                    sensor['devtype'] = 'PROGRM'
                    sensor['location'] = 'Program'

                info['sensors'].append(sensor)
                if sensor['target'] > target:
                    location = sensor['location']
                    target = sensor['target']

        info['box']['has_control'] = 'Manual' if info['box']['mode'] == 'MANU' else location
    except Exception as err: 
        info = {'error': {}}
        status_code = requests.codes.internal_server_error
        info['error']['code'] = status_code
        info['error']['reason'] = err.__class__.__name__
        info['error']['message'] = str(err)
    else:
        status_code = requests.codes.ok
    finally:
        session.close()
 
    return info, status_code

def writelog():
    info, status_code = getinfo()
    if status_code != requests.codes.ok:
        return info, status_code

    result = {
        'timestamp': info['box']['logtime'],
        'box_logid': None,
        'sensor_logids': []
    }

    try:
        db = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            db=MYSQL_DB,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        c = db.cursor()
        
        box = info['box']
        sql = f"INSERT INTO box ({', '.join(box.keys())}) VALUES ({', '.join(['%s'] * len(box.values()))})"
        c.execute(sql, list(box.values()))
        result['box_logid'] = c.lastrowid

        for sensor in info['sensors']:
            sensor['box_logid'] = result['box_logid']
            sql = f"INSERT INTO sensors ({', '.join(sensor.keys())}) VALUES ({', '.join(['%s'] * len(sensor.values()))})"
            c.execute(sql, list(sensor.values()))
            result['sensor_logids'].append(c.lastrowid)

        db.commit()
        db.close()
    except Exception as err: 
        result = {'error': {}}
        status_code = requests.codes.internal_server_error
        result['error']['code'] = status_code
        result['error']['reason'] = err.__class__.__name__
        result['error']['message'] = str(err)
    else:
        status_code = requests.codes.ok
 
    return result, status_code

def chksensor(location, field, threshold):
    info, status_code = getinfo()
    if status_code != requests.codes.ok:
        return info, status_code

    try:
        sensor = {}
        for n in range(len(info['sensors'])):
            if info['sensors'][n]['location'].casefold() == location.casefold():
                sensor = info['sensors'][n]
    
        result = {
            'field': field,
            'value': sensor[field],
            'threshold': threshold,
            'ok': float(sensor[field]) <= float(threshold)
        }
    except Exception as err: 
        result = {'error': {}}
        status_code = requests.codes.bad_request
        result['error']['code'] = status_code
        result['error']['reason'] = err.__class__.__name__
        result['error']['message'] = str(err)
    else:
        status_code = requests.codes.ok
 
    return result, status_code

if __name__ == "__main__":
    # For debugging while developing
    info, status_code = getinfo()
    print(status_code)
    print(json.dumps(info, indent=4, default=str))

    stat, status_code = chksensor('Keuken', 'co2', 500)
    print(status_code)
    print(json.dumps(stat, indent=4, default=str))

