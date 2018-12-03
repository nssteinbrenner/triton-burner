#!/usr/bin/env python

import time
import requests
import tconfig

from bs4 import BeautifulSoup
from lxml import html


class Triton:

    def __init__(self, sn, dev):
        self.serial = sn
        self.devid = dev
        self.donotburn = False
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
        self.efoy = False
        self.erroroccur = False
        self.country = None
        self.sunrise = None
        self.sunset = None
        self.burnurl = ('https://energy.redacted.com/redeacted/'
                        f'heater_burn?device_ids={self.devid}')
        self.loginburn = ('https://energy.redacted.com/account/login/'
                          '?next=/redeacted/heater_burn%3Fdevice_ids'
                          f'%3D{self.devid}')

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
            \tBurn URL: {self.burnurl}\n
            \tSunrise: {self.sunrise}\n
            \tSunset: {self.sunset}\n
            \tCurrent Time: {time.time()}\n
            \tEfoy: {self.efoy}\n"""

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

    def setEfoy(self, efoy):
        if str(efoy) == 'True':
            self.efoy = True
        elif str(efoy) == 'False':
            self.efoy = False
        else:
            self.efoy = False

    def setDoNotBurn(self, donotburn):
        self.donotburn = donotburn

    def setWeather(self):
        allWeather = []

        try:
            url = ('https://forecast.weather.gov/MapClick.php?'
                   f'lat={self.lat}&lon={self.lon}')

            r = requests.get(url)
            soup = BeautifulSoup(r.text, 'lxml')
            for p in soup.find_all('p', 'myforecast-current'):
                if p.string is not None:
                    if len(p.string) > 1:
                        allWeather.append(str(p.string).lower())

        except Exception as e:
            self.logWriter('setWeather(weathergov)', errored=e)

        try:

            url = (f'https://api.darksky.net/forecast/{tconfig.darkapi}/'
                   f'{self.lat},{self.lon}')

            weather = requests.get(url)
            weather.raise_for_status()

            w = weather.json()

            self.sunrise = w['daily']['data'][0]['sunriseTime']
            self.sunset = w['daily']['data'][0]['sunsetTime']

            allWeather.append(w['currently']['icon'])

        except Exception as e:
            self.logWriter('setWeather(darksky)', errored=e)

        self.weather = ' '.join(allWeather)

    def setBurn(self):
        if self.donotburn is True:
            self.burn = False
        elif (self.windvert is not None and self.battery is not None
              and self.ambtemp is not None):
                if self.windvert <= -0.5:  # and self.windvert >= -2.5:
                    if self.ambtemp <= 4:
                        if self.efoy is True:
                            self.burn = True
                        elif self.battery >= 12:
                            self.burn = True
                        elif self.battery >= 11.8:
                            if self.setDaytime():
                                self.burn = True

    def activateBurn(self):
        try:
            with requests.Session() as session:
                r = session.get(self.loginburn)
                r.raise_for_status()

                tree = html.fromstring(r.text)
                csrf = list(set(tree.xpath("//input[@name="
                                           "'csrfmiddlewaretoken']"
                                           "/@value")))[0]

                payload = {
                        'username': tconfig.energyuser,
                        'password': tconfig.energypass,
                        'next': ('/redeacted/heater_burn?'
                                 f'device_ids={self.devid}'),
                        'csrfmiddlewaretoken': csrf,
                        }

                headers = {
                        'user-agent': ('Mozilla/5.0 (X11; Linux x86_64;'
                                       'rv:60.0) Gecko/20100101 Firefox/60.0'),
                        'referer': ('https://energy.redacted.com/account/login/'
                                    '?next=/redeacted/heater_burn%3F'
                                    f'device_ids%3D{self.devid}'),
                        }

                r = session.post(self.loginburn,
                                 data=payload,
                                 headers=headers)
                r.raise_for_status()

                soup = BeautifulSoup(r.text, 'lxml')
                action = soup.find('form').get('action')

                start = action.find('=') + 1
                end = action.find('&')

                scripts = [int(i) for i in action[start:end].split(',')]

                if max(scripts) > 4:
                    scriptvalue = str(max(scripts))
                else:
                    scriptvalue = '2'

                payload = {
                        'selection': scriptvalue,
                        }

                params = {
                        'command_ids': action[start:end],
                        'device_ids': self.devid,
                        }

                r = session.post(self.burnurl,
                                 data=payload,
                                 params=params,
                                 headers=headers)
                r.raise_for_status()

            self.self.logWriter('activateBurn()')

        except Exception as e:
            self.logWriter('activateBurn()', errored=e)

    def setCountry(self):
        if self.lat is None or self.lon is None:
            return None

        try:
            geourl = (f'https://maps.googleapis.com/maps/api/geocode/json?'
                      f'latlng={self.lat},{self.lon}&key={tconfig.googleapi}')

            location = requests.get(geourl)
            location.raise_for_status()

            loc = location.json()

            country = loc['results'][-1]['address_components'][0]['short_name']

            self.country = country

        except Exception as e:
            self.logWriter('setCountry()', errored=e)

    def setDaytime(self):

        try:
            if self.sunrise is None or self.sunset is None:
                url = (f'https://api.darksky.net/forecast/{tconfig.darkapi}/'
                       f'{self.lat},{self.lon}')

                weather = requests.get(url)
                weather.raise_for_status()

                w = weather.json()

                self.sunrise = w['daily']['data'][0]['sunriseTime']
                self.sunset = w['daily']['data'][0]['sunsetTime']
                current = time.time()

            else:
                current = time.time()

            if current >= self.sunrise and current <= self.sunset:
                return True
            else:
                return False

        except Exception as e:
            self.logWriter('setDaytime()', errored=e)

    def logWriter(self, func, errored=False):
        today = time.strftime("%Y-%m-%d", time.gmtime())
        now = time.strftime("%H:%M", time.gmtime())
        if errored is False:
            with open(f'burned/{today}', 'a+') as log:
                log.write(f'{today} {now} - {func} - '
                          f'Issued burn to T{self.serial}\n')
        elif errored is not False:
            with open(f'log/{today}', 'a+') as error:
                error.write(f'{today} {now} - {func} - Errored '
                            f'at T{self.serial}\n\t{errored}\n')

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
