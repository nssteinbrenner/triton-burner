#!/usr/bin/env python

import time
import requests
import splinter
import json
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
        self.country = None
        self.burnurl = (f'https://energy.vaisala.com/skyserve/'
                        f'heater_burn?device_ids={self.devid}')

    def __str__(self):
        return f"""\n\tT{self.serial}\n
            \tBattery: {self.battery}\n
            \tSNR: {self.snr}\n
            \tMirrorTemp: {self.mirrortemp}\n
            \tAmbientTemp: {self.ambtemp}\n
            \tWindVert: {self.windvert}\n
            \tLat: {self.lat}\n
            \tLon: {self.lon}\n
            \tCountry: {self.country}\n
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

        try:
            with splinter.Browser('firefox', headless=True) as browser:
                url = 'https://www.accuweather.com'
                browser.visit(url)
                time.sleep(3)
                (browser.find_by_id('s').first
                        .fill(f'{self.lat},{self.lon}'))
                (browser.find_by_xpath('/html/body/div[4]/div[1]/div'
                                       '[2]/div/div/div[2]/div[2]/div'
                                       '[1]/div/div/form/button')
                    .first.click())
                accuweather = browser.html

                soup = BeautifulSoup(accuweather, 'html.parser')

                current = soup.find_all('span', 'cond')[0]
                allWeather.append('accuweather ')
                allWeather.append(str(current.string).lower())

        except Exception as e:
            today = time.strftime("%Y-%m-%d", time.gmtime())
            now = time.strftime("%H:%M", time.gmtime())
            with open('weatherError', 'a+') as f:
                f.write(f'{today} {now} - Error grabbing weather '
                        f'from weather.gov for T{self.serial}\n\t{e}\n')

        try:
            with splinter.Browser('firefox', headless=True) as browser:
                url = (f'https://forecast.weather.gov/MapClick.php?'
                       f'lat={self.lat}&lon={self.lon}')
                browser.visit(url)
                time.sleep(5)
                webpage = browser.html
                soup = BeautifulSoup(webpage, 'html.parser')
                for p in soup.find_all('p', 'myforecast-current'):
                    if p.string is not None:
                        if len(p.string) > 1:
                            allWeather.append(str(p.string).lower())

        except Exception as e:
            today = time.strftime("%Y-%m-%d", time.gmtime())
            now = time.strftime("%H:%M", time.gmtime())
            with open('weatherError', 'a+') as f:
                f.write(f'{today} {now} - Error grabbing weather '
                        f'from weather.gov for T{self.serial}\n\t{e}\n')

        try:
            with open('config', 'r') as config:
                lines = config.readlines()
                for line in lines:
                    if 'darksky:' in line:
                        target = line.strip().split(' ')
                        api = target[1]

            url = (f'https://api.darksky.net/forecast/{api}/'
                   f'{self.lat},{self.lon}')

            weather = requests.get(url)
            weather.raise_for_status()

            w = weather.json()
            allWeather.append(w['currently']['icon'])

        except Exception as e:
            today = time.strftime("%Y-%m-%d", time.gmtime())
            now = time.strftime("%H:%M", time.gmtime())
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
            today = time.strftime("%Y-%m-%d", time.gmtime())
            now = time.strftime("%H:%M", time.gmtime())
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
        if f'T{self.serial}' in errored:
            print(f"Skipping. T{self.serial} is in error list.")
        elif self.errorChecker() is not None and self.errorChecker() <= 75:
            print(f"Skipping. T{self.serial} has been burned "
                  f"{self.errorChecker()} minutes ago. Check for errors.")
            self.errorWriter()
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
                today = time.strftime("%Y-%m-%d", time.gmtime())
                now = time.strftime("%H:%M", time.gmtime())
                with open('burnerror', 'a+') as f:
                    f.write(f'Failed to burn T{self.serial} at '
                            f'{today} {now} GMT\n{str(self)}\n\t{e}\n')

    def logBurn(self):
        today = time.strftime("%Y-%m-%d", time.gmtime())
        now = time.strftime("%H:%M", time.gmtime())
        with open(f'log/{today}', 'a+') as log:
            log.write(f'Issued burn to T{self.serial} at {now}\n')

    def setCountry(self):
        if self.lat is None or self.lon is None:
            return None

        with open('config', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if 'google:' in line:
                    line = line.strip().split(' ')
                    gapi = line[1]

        try:
            geourl = (f'https://maps.googleapis.com/maps/api/geocode/json?'
                      f'latlng={self.lat},{self.lon}&key={gapi}')

            location = requests.get(geourl)
            location.raise_for_status()

            loc = location.json()

            country = loc['results'][-1]['address_components'][0]['short_name']

            self.country = country

        except Exception as e:
            today = time.strftime("%Y-%m-%d", time.gmtime())
            now = time.strftime("%H:%M", time.gmtime())
            with open('countryError', 'a+') as f:
                f.write(f'{today} {now} - Error grabbing country '
                        f'from Google API for T{self.serial}\n\t{e}\n')

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

    def burnChecker(self):
        lastburn = ('https://energy.vaisala.com/admin/skyserve/'
                    f'heater/burn_output/{self.serial}#lastBurnRaw')
        try:
            with splinter.Browser('firefox', headless=True) as browser:
                browser.visit(lastburn)
                time.sleep(7)
                (browser.find_by_id('login-form').first
                        .find_by_name('username').fill(username))
                (browser.find_by_id('login-form').first
                        .find_by_name('password').fill(password))
                (browser.find_by_id('login-form').first
                        .find_by_value('Log in').click())
                time.sleep(7)
                burnhtml = browser.html

            with open('.burnhtml', 'w+') as f:
                f.write(str(burnhtml))
                f.seek(0)
                lines = f.readlines()
                for line in lines:
                    if '    data =' in line:
                        target = (str(line[10:-2]))

        except Exception as e:
            with open('burnData', 'a+') as f:
                f.write('{today} {now} - Error grabbing burn data'
                        f'for T{self.serial}\n\t{e}\n')

        try:

            data = json.loads(target)

            self.intemp = data["in_temp"]["0"]
            self.pressure = data["pressure"]["0"]
            self.outtemp = data["out_temp"]["0"]
            self.vsol = data["v_solenoid"]["0"]

            if len(self.outtemp) > 29:
                if float(self.vsol[30]) < 10.5:
                    with open('testing', 'a+') as f:
                        f.write(f'T{self.serial} bad vsol\n')

            if len(self.outtemp) > 29:
                if float(self.outtemp[5]) <= 4:
                    gas = float(self.outtemp[30]) - float(self.outtemp[5])
                    if gas < 5:
                        with open('testing', 'a+') as f:
                            f.write(f'T{self.serial} out of propane\n')

            if len(self.outtemp) > 89:
                if float(self.outtemp[5]) <= 4:
                    slow = float(self.outtemp[90]) - float(self.outtemp[5])
                    if slow < 15:
                        with open('testing', 'a+') as f:
                            f.write(f'T{self.serial} slow burner\n')

            if len(self.outtemp) > 37:
                if float(self.intemp[37]) > float(self.outtemp[37] + 5):
                    with open(f'testing', 'a+') as f:
                            f.write(f'T{self.serial} clogged system\n')

        except Exception as e:
            with open('uhoh', 'a+') as f:
                f.write(f'T{self.serial} - {e}\n')

    def getBurn(self):
        return self.burn

    def getBurningStatus(self):
        return self.burningstatus

    def getSerial(self):
        return self.serial

    def getWeather(self):
        return str(self.weather)

    def getDev(self):
        return self.devid

    def getCountry(self):
        return str(self.country)


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
    url = ('https://energy.vaisala.com/admin/skyserve/'
           'heater/?all=&burnable=0%2C3')
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
    if '/admin/skyserve/heater/burn_output' in a['href']:
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
    if i.getBurningStatus() is True:
        i.burnChecker()
        with open('checked', 'a+') as f:
            f.write(f'{now} - T{i.getSerial()} checked\n')
    i.setBurn()
    if i.getBurn() is True:
        i.setWeather()
        i.setCountry()
        with open('potato', 'a+') as f:
            f.write(str(i))
#    if i.getBurn() is True and i.getBurningStatus() is not True:
#        i.setWeather()
#        i.setCountry()
#        if 'snow' in i.getWeather() or 'sleet' in i.getWeather():
#            if 'US' in i.getCountry() or 'CA' in i.getCountry()
#                print("You should burn me!")
