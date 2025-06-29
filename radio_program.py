import sys
import requests
from lxml import etree
from datetime import datetime, timedelta

def get_programs(date, station):
    r = requests.get(f'http://radiko.jp/v3/program/station/date/{date}/{station}.xml')
    r.encoding = r.apparent_encoding
    root = etree.fromstring(r.text.encode('utf-8'))

    print('\n\nProgram list ########################################################\n', station, date)
    for p in root.xpath('//prog'):
        print(f'{p.attrib["ftl"]}-{p.attrib["tol"]} {p.xpath("pfm")[0].text} {p.xpath("title")[0].text} {p.xpath("url")[0].text}')

if len(sys.argv) < 2:
    print("Usage: python radio_program.py <date> [station_id]")
    print("ex) python radio_program.py 20250315 TBS\n")
    print("TBS             TBSラジオ")
    print("QRR             文化放送")
    print("LFR             ニッポン放送")
    print("RN1             ラジオNIKKEI第一")
    print("RN2             ラジオNIKKEI第二")
    print("INT             InterFM897")
    print("FMT             TOKYO FM")
    print("FMJ             J-WAVE")
    print("JORF            ラジオ日本")
    print("bayfm78         bayfm78")
    print("NACK5           NACK5")
    print("YFM             FMヨコハマ")
    print("HOUSOU-DAIGAKU  放送大学")
    print("JOAK            NHKラジオ第1")
    print("JOAB            NHKラジオ第2")
    print("JPAK-FM         NHK-FM")

else:
    date_str = sys.argv[1]
    if len(sys.argv) < 3:
        stations = ['TBS', 'QRR', 'LFR', 'RN1', 'RN2', 'INT', 'FMT', 'FMJ', 'JORF', 'bayfm78', 'NACK5', 'YFM', 'HOUSOU-DAIGAKU', 'JOAK', 'JOAB', 'JPAK-FM']
        for station in stations:
            get_programs(date_str, station)
    else:
        station = sys.argv[2]
        get_programs(date_str, station)
