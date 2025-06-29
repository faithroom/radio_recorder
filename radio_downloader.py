
import sys
import time
import base64
import requests
import subprocess
from lxml import etree

def auth1(url):
    authkey = b'bcd151073c03b352e1ef2fd66c32209da9ca0afa'
    header = {
        'User-Agent': 'curl/7.52.1',
        'Accept': '*/*',
        'x-radiko-user': 'johndoe',
        'x-radiko-app': 'pc_html5',
        'x-radiko-app-version': '0.0.1',
        'x-radiko-device': 'pi'
    }
    response = requests.get('https://radiko.jp/v2/api/auth1', headers=header)

    length = int(response.headers['X-Radiko-KeyLength'])
    offset = int(response.headers['X-Radiko-KeyOffset'])
    authtoken = response.headers['X-Radiko-AUTHTOKEN']
    partialkey = base64.b64encode(authkey[offset: offset + length])

    return authtoken, partialkey


def auth2(url, authtoken, partialkey):
    header = {
        'User-Agent': 'curl/7.52.1',
        'Accept': '*/*',
        'x-radiko-user': 'johndoe',
        'X-RADIKO-AUTHTOKEN': authtoken,
        'x-radiko-partialkey': partialkey,
        'x-radiko-device': 'pi'
    }
    response = requests.get('https://radiko.jp/v2/api/auth2', headers=header)
    return (response.status_code == 200)


def download(url, authtoken, output_file):
    header = {
        'X-RADIKO-AUTHTOKEN': authtoken
    }
    response = requests.get(url, headers=header)
    m3u8_url = response.content.splitlines()[-1]

    cmd = f'ffmpeg -headers "X-RADIKO-AUTHTOKEN:{authtoken}" -i {m3u8_url.decode()} -y -loglevel warning {output_file}'
    return subprocess.Popen(cmd.split(' '))


def record(filename, station, duration, start_time='', end_time=''):
    url = f'http://c-radiko.smartstream.ne.jp/{station}/_definst_/simul-stream.stream/playlist.m3u8'

    if start_time != '' and end_time != '': # Timefree 日時指定
        url = f'https://radiko.jp/v2/api/ts/playlist.m3u8?station_id={station}&l=15&ft={start_time}&to={end_time}'

    try:
        authtoken, partialkey = auth1(url)
    except Exception as e:
        print('Record error1: ', e)

    if auth2(url, authtoken, partialkey):
        try:
            process = download(url, authtoken, filename)
        except Exception as e:
            print('Record error2: ', e)

        if start_time != '':
            for i in range(duration):
                if process.poll() is not None:
                    break
                time.sleep(1)
        else:
            time.sleep(duration)
            process.terminate()

        process = None
