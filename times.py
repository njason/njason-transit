from datetime import datetime
from collections import namedtuple

import requests
from bs4 import BeautifulSoup
from lxml import etree


def get_lighrail_departures(num_departures):
    payload = {'selLineCode': 'HBLR',
               'selOrigin': '38442',
               'selDestination': '39348',
               'datepicker': datetime.now().strftime('%m/%d/%Y'),
               'LineDescription': 'Hudson-Bergen Light Rail',
               'OriginDescription': '9th Street - Congress Street',
               'DestDescription': 'Hoboken'}

    url = ('http://www.njtransit.com/sf/sf_servlet.srv?hdnPageAction='
           'LightRailSchedulesFrom')

    response = requests.post(url, data=payload)
    soup = BeautifulSoup(response.text, 'html.parser')
    time_table = soup.find_all(text='Schedule Information')[0].parent.parent

    def parse_time(time_str):
        return datetime.strptime(time_str, '%I:%M %p').time()

    rows = time_table.find_all('tr')

    departures = []
    for row in rows[1:]:
        data = row.find_all('span')

        if data[1].text.strip() != '':
            continue

        departures.append(parse_time(data[0].text.strip()))

    now = datetime.now()

    next_departures = [d for d in departures if d > now.time()]

    return next_departures[:num_departures]


def get_bus_estimates():
    time_url = ('http://mybusnow.njtransit.com/bustime/eta/'
                'getStopPredictionsETA.jsp?route=all&stop=21061&'
                'key=0.9878138302668902')

    response = requests.get(time_url)

    tree = etree.fromstring(response.content)

    bus_times = {}  # type: Dict[int, str]

    for bus in tree.findall('pre'):
        id = int(bus.find('v').text)

        if bus.find('pu').text.strip() == 'MINUTES':
            estimate = bus.find('pt').text + ' minutes'
        else:
            estimate = bus.find('pu').text.strip().lower()

        bus_times[id] = estimate

    return bus_times


BusInfo = namedtuple('BusInfo', ['id', 'lat', 'lon', 'njt_estimate'])


def get_bus_locations():
    location_url = ('http://mybusnow.njtransit.com/bustime/map/'
                    'getBusesForRoute.jsp?route=87')

    response = requests.get(location_url)

    tree = etree.fromstring(response.content)

    buses = []

    for bus in tree.findall('bus'):
        buses.append({
            'id': int(bus.find('id').text),
            'lat': bus.find('lat').text,
            'lon': bus.find('lon').text
        })

    return buses


def get_bus_infos():
    bus_estimates = get_bus_estimates()

    bus_locations = get_bus_locations()

    bus_infos = []

    for bus in bus_locations:
        id = bus['id']
        if id in bus_estimates:
            bus_infos.append(BusInfo(id, bus['lat'], bus['lon'],
                                     bus_estimates[id]))

    return bus_infos


def main():
    lr_departures = get_lighrail_departures(3)
    for lrd in lr_departures:
        print(lrd.strftime('%-I:%M %p'))

    bus_infos = get_bus_infos()
    for bus in bus_infos:
        print(bus)


if __name__ == '__main__':
    main()
