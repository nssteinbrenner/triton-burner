#!/usr/bin/env python

import time
import requests
import splinter
import os

from bs4 import BeautifulSoup


class Triton:

    def __init__(self, sn, dev):
        self.serial = sn
        self.devid = dev
        self.battery = None
        self.snr = None
        self.mirrortemp = None
        self.ambtemp = None
        self.windvert = None
        self.lat = None
        self.lon = None
        self.weather = None
        self.burningstatus = False
        self.lastburn = None
        self.burn = False
        self.erroroccur = False
        self.burnurl = f'redacted'

    def __str__(self):
        return f"""\n\tT{self.serial}\n
            \tBattery: {self.battery}\n
            \tSNR: {self.snr}\n
            \tMirrorTemp: {self.mirrortemp}\n
            \tAmbientTemp: {self.ambtemp}\n
            \tWindVert: {self.windvert}\n
            \tLat: {self.lat}\n
            \tLon: {self.lon}\n
            \tWeather: {self.weather}\n
            \tBurning: {self.burningstatus}\n
            \tLast Burn: {self.lastburn}\n
            \tBurn URL: {self.burnurl}\n"""

    def setBattery(self, battery):
        if '(None)' not in battery:
            self.battery = float(battery)

    def setSnr(self, snr):
        if '(None)' not in snr:
            self.snr = float(snr)

    def setMirrortemp(self, mirrortemp):
        if '(None)' not in mirrortemp:
            self.mirrortemp = float(mirrortemp)

    def setAmbtemp(self, ambtemp):
        if '(None)' not in ambtemp:
            self.ambtemp = float(ambtemp)

    def setWindvert(self, windvert):
        if '(None)' not in windvert:
            self.windvert = float(windvert)

    def setBurningStatus(self, burning):
        if 'Running' in burning:
            self.burningstatus = True
        if 'Pending' in burning:
            self.burningstatus = True
        if 'Error' in burning:
            self.burningstatus = 'Error'

    def setLastBurn(self, lastburn):
        self.lastburn = lastburn

    def setLat(self, lat):
        if 'None' not in lat:
            self.lat = lat

    def setLon(self, lon):
        if 'None' not in lon:
            self.lon = lon

    def setDev(self, devid):
        self.devid = str(devid)

    def setWeather(self):
        allWeather = []
        today = time.strftime("%Y-%m-%d", time.gmtime())
        now = time.strftime("%H:%M", time.gmtime())

        try:
            with splinter.Browser('firefox', headless=True) as browser:
                url = (f'https://forecast.weather.gov/MapClick.php?'
                       f'lat={self.lat}&lon={self.lon}')
                browser.visit(url)
                time.sleep(5)
                webpage = browser.html
                soup = BeautifulSoup(webpage, 'html.parser')
                for p in soup.find_all('p', 'myforecast-current'):
                    if len(p.string) > 1:
                        allWeather.append(str(p.string).lower())

        except Exception as e:
            with open('weatherError', 'a+') as f:
                f.write(f'{today} {now} - Error grabbing weather '
                        f'from weather.gov for T{self.serial}\n\t{e}\n')

        try:
            with open('config', 'r') as config:
                lines = config.readlines()
                for line in lines:
                    if 'api:' in line:
                        target = line.strip().split(' ')
                        api = target[1]

            url = (f'https://api.darksky.net/forecast/{api}/'
                   f'{self.lat},{self.lon}')

            weather = requests.get(url)
            weather.raise_for_status()

            w = weather.json()
            allWeather.append(w['currently']['icon'])

        except Exception as e:
            with open('weatherError', 'a+') as f:
                f.write(f'{today} {now} - Error grabbing weather '
                        f'from darksky for T{self.serial}\n\t{e}\n')

        try:
            with splinter.Browser('firefox', headless=True) as browser:
                url = (f'https://www.wunderground.com/weather/'
                       f'{self.lat}%2C{self.lon}')
                browser.visit(url)
                time.sleep(5)
                wunderground = browser.html
                soup = BeautifulSoup(wunderground, 'html.parser')
                for p in soup.find_all('p'):
                    if p.string is not None:
                        if 'snow' in str(p.string.lower()):
                            allWeather.append(str(p.string).lower())

        except Exception as e:
            with open('weatherError', 'a+') as f:
                f.write(f'{today} {now} - Error grabbing weather'
                        f'from wunderground for T{self.serial}\n\t{e}\n')

        self.weather = ' '.join(allWeather)

    def setBurn(self):
        if self.windvert is not None and self.battery is not None \
                and self.ambtemp is not None:
            if self.windvert <= -0.5 and self.windvert >= -2.5:
                if self.battery >= 12:
                    if self.ambtemp <= 4:
                        self.burn = True

    def activateBurn(self):
        if self.errorChecker() is not None and self.errorChecker() <= 75:
            print(f"Skipping. T{self.serial} has been burned "
                  f"{self.errorChecker()} minutes ago. Check for errors.")
            self.errorWriter()
        elif f'T{self.serial}' in errored:
            print(f"Skipping. T{self.serial} is in error list.")
        else:
            self.logBurn()
            try:
                with splinter.Browser('firefox', headless=True) as browser:
                    browser.visit(self.burnurl)
                    time.sleep(7)
                    (browser.find_by_id('login').first
                            .find_by_name('username').fill(username))
                    (browser.find_by_id('login').first
                            .find_by_name('password').fill(password))
                    (browser.find_by_id('login')
                            .first.find_by_value('Login').click())
                    time.sleep(7)
                    value = '2'
                    for i in range(5, 20):
                        if browser.is_element_present_by_value(str(i)) is True:
                            value = str(i)
                            break
                    browser.execute_script(f'document.getElementById'
                                           f'("id_selection").value = '
                                           f'"{value}"')
                    browser.find_by_value('Burn Heaters').first.click()

            except Exception as e:
                with open('burnerror', 'a+') as f:
                    f.write(f'Failed to burn T{self.serial} at '
                            f'{today} {now} GMT\n{str(self)}\n\t{e}\n')

    def logBurn(self):
        today = time.strftime("%Y-%m-%d", time.gmtime())
        now = time.strftime("%H:%M", time.gmtime())
        with open(f'log/{today}', 'a+') as log:
            log.write(f'Issued burn to T{self.serial} at {now}\n')

    def errorChecker(self):
        if 'Error' in str(self.getBurningStatus()):
            return None
        if f'T{self.serial}' in burned:
            now = time.strftime("%H:%M", time.gmtime())
            then = burned[f'T{self.serial}']
            difference = timediff(now, then)
            return difference

    def errorWriter(self):
        today = time.strftime("%Y-%m-%d", time.gmtime())
        now = time.strftime("%H:%M", time.gmtime())
        with open(f'error/{today}', 'a') as error:
            error.write(f'T{self.serial} - {now} - Possible error\n')

    def getBurn(self):
        return self.burn

    def getBurningStatus(self):
        return self.burningstatus

    def getSerial(self):
        return self.serial

    def getWeather(self):
        return f'{self.weather}'

    def getDev(self):
        return self.devid


today = time.strftime("%Y-%m-%d", time.gmtime())
now = time.strftime("%H:%M", time.gmtime())
burned = {}
errored = []


def timediff(now, then):
    now = now.split(':')
    then = then.split(':')
    nowmin = ((int(now[0]) * 60) + int(now[1]))
    thenmin = ((int(then[0]) * 60) + int(then[1]))
    return nowmin - thenmin


if os.path.exists(f'log/{today}'):
    with open(f'log/{today}', 'r') as log:
        lines = log.readlines()
        for line in lines:
            if len(line) > 1:
                line = line.strip().split(' ')
                burned[line[3]] = line[5]

if os.path.exists(f'error/{today}'):
    with open(f'error/{today}') as error:
        lines = error.readlines()
        for line in lines:
            if len(line) > 1:
                line = line.strip().split(' ')
                errored.append(line[0])


with open('config', 'r') as config:
    lines = config.readlines()
    for line in lines:
        if 'pw:' in line:
            target = line.strip().split(' ')
            password = target[1]
        if 'user:' in line:
            target = line.strip().split(' ')
            username = target[1]

with splinter.Browser('firefox', headless=True) as browser:
    url = 'redacted'
    browser.visit(url)
    time.sleep(3)
    (browser.find_by_id('login-form').first
            .find_by_name('username').fill(username))
    (browser.find_by_id('login-form').first
            .find_by_name('password').fill(password))
    (browser.find_by_id('login-form').first
            .find_by_value('Log in').click())
    time.sleep(10)
    tritonwebpage = browser.html

soup = BeautifulSoup(tritonwebpage, 'html.parser')

index = 0
tritonclasslist = []

for a in soup.find_all('a'):
    if 'changelist_filters' in a['href'] and 'Add heater' not in str(a.string):
        spliturl = str(a['href']).split('/')
        deviceid = spliturl[4]
        tritonsn = str(a.string)
        exec(f'T{tritonsn} = Triton({tritonsn}, deviceid)')
        exec(f'tritonclasslist.append(T{tritonsn})')
    if 'forecast.weather.gov' in a['href'] or 'observations' in a['href']:
        coords = str(a.string).strip().split(' ')
        coords[0] = coords[0][:-1]
        exec(f'T{tritonsn}.setLat(coords[0])')
        exec(f'T{tritonsn}.setLon(coords[1])')
    if 'redacted' in a['href']:
        burning = str(a.string).strip().split(' ')
        burnstatus = ' '.join(burning[0:2])
        lastburntime = ' '.join(burning[2:])
        exec(f'T{tritonsn}.setBurningStatus(burnstatus)')
        exec(f'T{tritonsn}.setLastBurn(lastburntime)')

for td in soup.find_all('td'):
    if 'field-battery' in td['class']:
        battery = str(td.string)
        tritonclasslist[index].setBattery(battery)
    if 'field-wind_vert' in td['class']:
        windvert = str(td.string)
        tritonclasslist[index].setWindvert(windvert)
    if 'field-snr' in td['class']:
        snr = str(td.string)
        tritonclasslist[index].setSnr(snr)
    if 'field-amb_temp' in td['class']:
        ambtemp = str(td.string)
        tritonclasslist[index].setAmbtemp(ambtemp)
    if 'field-mirror_temp' in td['class']:
        mirrortemp = str(td.string)
        tritonclasslist[index].setMirrortemp(mirrortemp)
        index += 1

for i in tritonclasslist:
    i.setBurn()
    if i.getBurn() is True and i.getBurningStatus() is not True:
        i.setWeather()
        if 'snow' in i.getWeather():
            i.activateBurn()
