from typing import Tuple
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

def get(log_output: bool = False) -> Tuple[dict, int]:
    result = {
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
    
    try:
        url = f"{DUCO_ROOT_ENDPOINT}/board_info"
        response = session.get(url, timeout=10)
        response.raise_for_status()
        board = response.json()
        result['box']['uptime'] = board['uptime']
        
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
                result['box']['logtime'] = datetime.now(tz=timezone.utc)
                result['box']['mode'] = node['mode']
                result['box']['state'] = node['state']
                result['box']['level'] = node['trgt']
                result['box']['cntdwn'] = node['cntdwn']
                  
                url = f"{DUCO_ROOT_ENDPOINT}/boxinfoget')"
                response = session.get(url, timeout=10)
                response.raise_for_status()     
                box = response.json()

                result['box']['temp_oda'] = box['EnergyInfo']['TempODA']/10 # Outdoor air. Supply air from outdoors to the unit
                result['box']['temp_sup'] = box['EnergyInfo']['TempSUP']/10 # Supply air. Supply air from unit to house
                result['box']['temp_eta'] = box['EnergyInfo']['TempETA']/10 # Extract air. Supply air from the house to the unit
                result['box']['temp_eha'] = box['EnergyInfo']['TempEHA']/10 # Exhaust air. Exhaust air from the unit to outdoors        
                result['box']['remainfilter_days'] = box['EnergyInfo']['FilterRemainingTime']
                result['box']['remainfilter_percent'] = round(box['EnergyInfo']['FilterRemainingTime']/(365/2)*100)
                result['box']['bypass'] = box['EnergyInfo']['BypassStatus']
                result['box']['frost'] = box['EnergyInfo']['FrostProtState']
                result['box']['power'] = (box['EnergyFan']['SupplyFanPwmLevel'] + box['EnergyFan']['ExhaustFanPwmLevel'])/1000
            
            elif node['devtype'] == 'UCCO2' or node['devtype'] == 'UCRH' or (node['devtype'] == 'UC' and node['netw'] == 'VIRT'):
                sensor = {}
                sensor['logtime'] = datetime.now(tz=timezone.utc)
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

                result['sensors'].append(sensor)
                if sensor['target'] > target:
                    location = sensor['location']
                    target = sensor['target']

        result['box']['has_control'] = 'Manual' if result['box']['mode'] == 'MANU' else location

        if log_output:
            db = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                db=MYSQL_DB,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD
            )
            c = db.cursor()
            
            box = result['box']
            sql = f"INSERT INTO box ({', '.join(box.keys())}) VALUES ({', '.join(['%s'] * len(box.values()))})"
            c.execute(sql, list(box.values()))
            result['box']['logid'] = c.lastrowid

            for n in range(len(result['sensors'])):
                result['sensors'][n]['box_logid'] = result['box']['logid']
                sql = f"INSERT INTO sensors ({', '.join(result['sensors'][n].keys())}) VALUES ({', '.join(['%s'] * len(result['sensors'][n].values()))})"
                c.execute(sql, list(result['sensors'][n].values()))
                result['sensors'][n]['logid'] = c.lastrowid

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
    finally:
        session.close()
 
    return result, status_code

if __name__ == "__main__":
    # For debugging while developing
    result, status_code = get(log_output=False)
    print(status_code)
    print(json.dumps(result, indent=4, sort_keys=True, default=str))
