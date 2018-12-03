#!/usr/bin/env python

import requests
import tconfig

from triton import Triton
from lxml import html
from bs4 import BeautifulSoup


def getBurnable(url):
    with requests.Session() as session:
        r = session.get(url)

        tree = html.fromstring(r.text)
        csrf = list(set(tree.xpath("//input[@name='csrfmiddlewaretoken']"
                                   "/@value")))[0]

        payload = {
                'username': tconfig.energyuser,
                'password': tconfig.energypass,
                'next': '/admin/redacted/heater/?all=&burnable=0%2C3',
                'csrfmiddlewaretoken': csrf,
                }

        headers = {
                'user-agent': ('Mozilla/5.0 (X11; Linux x86_64;'
                               'rv:60.0) Gecko/20100101 Firefox/60.0'),
                'referer': ('https://energy.redacted.com/admin/login/'
                            '?next=/admin/redacted/heater/%3Fall%3D%'
                            '26burnable%3D0%252C3'),
                }

        r = session.post(url, data=payload, headers=headers)
    return r.text


def tritonBuilder(burnablehtml):
    soup = BeautifulSoup(burnablehtml, 'lxml')

    index = 0
    tritons = []

    for a in soup.find_all('a'):
        if ('changelist_filters' in a['href'] and 'Add heater'
           not in str(a.string)):
            spliturl = str(a['href']).split('/')
            deviceid = spliturl[4]
            tritonsn = str(a.string)
            exec(f'T{tritonsn} = Triton({tritonsn}, deviceid)')
            exec(f'tritons.append(T{tritonsn})')
        if 'forecast.weather.gov' in a['href'] or 'observations' in a['href']:
            coords = str(a.string).strip().split(' ')
            coords[0] = coords[0][:-1]
            exec(f'T{tritonsn}.setLat(coords[0])')
            exec(f'T{tritonsn}.setLon(coords[1])')
        if '/admin/redacted/heater/burn_output' in a['href']:
            burning = str(a.string).strip().split(' ')
            burnstatus = ' '.join(burning[0:2])
            lastburntime = ' '.join(burning[2:])
            exec(f'T{tritonsn}.setBurningStatus(burnstatus)')
            exec(f'T{tritonsn}.setLastBurn(lastburntime)')

    for td in soup.find_all('td'):
        if 'field-battery' in td['class']:
            battery = str(td.string)
            tritons[index].setBattery(battery)
        if 'field-wind_vert' in td['class']:
            windvert = str(td.string)
            tritons[index].setWindvert(windvert)
        if 'field-snr' in td['class']:
            snr = str(td.string)
            tritons[index].setSnr(snr)
        if 'field-amb_temp' in td['class']:
            ambtemp = str(td.string)
            tritons[index].setAmbtemp(ambtemp)
        if 'field-mirror_temp' in td['class']:
            mirrortemp = str(td.string)
            tritons[index].setMirrortemp(mirrortemp)
        if 'field-has_efoy' in td['class']:
            efoy = str(td.contents[0]['alt'])
            tritons[index].setEfoy(efoy)
            index += 1
    return tritons


def getDoNotBurn():
    donotburn = []
    with open('donotburn', 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = str(line.strip())
            donotburn.append(line)
    return donotburn


def issueBurn(tritons, donotburn):
    for triton in tritons:
        if f'T{triton.getSerial()}' in donotburn:
            triton.setDoNotBurn(True)
        triton.setBurn()
        if triton.getBurn() is True and triton.getBurningStatus() is not True:
            triton.setWeather()
            triton.setCountry()
            if 'snow' in triton.getWeather() or 'sleet' in triton.getWeather():
                if 'US' in triton.getCountry() or 'CA' in triton.getCountry():
                    triton.activateBurn()
