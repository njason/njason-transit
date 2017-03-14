from datetime import datetime, timedelta
from collections import namedtuple

import requests
from bs4 import BeautifulSoup
from lxml import etree


BusInfo = namedtuple('BusInfo', ['id', 'lat', 'lon', 'njt_estimate'])
LocationInfo = namedtuple('LocationInfo', ['lr_origin_id', 'lr_origin_desc',
                                           'lr_dest_id', 'lr_dest_desc',
                                           'bus_number', 'bus_stop_id'])


def get_lighrail_departures(loc_info, num_departures):
    payload = {'selLineCode': 'HBLR',
               'selOrigin': loc_info.lr_origin_id,
               'selDestination': loc_info.lr_dest_id,
               'datepicker': datetime.now().strftime('%m/%d/%Y'),
               'LineDescription': 'Hudson-Bergen Light Rail',
               'OriginDescription': loc_info.lr_origin_desc,
               'DestDescription': loc_info.lr_dest_desc}

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


def get_bus_estimates(loc_info):
    time_url = ('http://mybusnow.njtransit.com/bustime/eta/'
                'getStopPredictionsETA.jsp?route={0}&stop={1}'.format(
                    loc_info.bus_number, loc_info.bus_stop_id))

    response = requests.get(time_url)

    tree = etree.fromstring(response.content)

    bus_times = {}  # type: Dict[int, str]

    for bus in tree.findall('pre'):
        id = int(bus.find('v').text)

        if bus.find('pu').text.strip() == 'MINUTES':
            estimate = datetime.now() + timedelta(minutes=int(bus.find('pt').text))
        else:
            estimate = bus.find('pu').text.strip().lower()

        bus_times[id] = estimate

    return bus_times


def get_bus_locations(loc_info):
    location_url = ('http://mybusnow.njtransit.com/bustime/map/'
                    'getBusesForRoute.jsp?route={0}'.format(
                        loc_info.bus_number))

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


def get_bus_infos(loc_info, num_departures):
    bus_estimates = get_bus_estimates(loc_info)

    bus_locations = get_bus_locations(loc_info)

    bus_infos = []

    for bus in bus_locations:
        id = bus['id']
        if id in bus_estimates:
            bus_infos.append(BusInfo(id, bus['lat'], bus['lon'],
                                     bus_estimates[id]))

    return bus_infos[:num_departures]


to_work = LocationInfo('38442', '9th Street - Congress Street', '39348',
                       'Hoboken', '87', '21061')
to_home = LocationInfo('39348', 'Hoboken', '38442',
                       '9th Street - Congress Street', '87', '20496')


time_format = '%-I:%M %p'

def main():
    lr_departures = get_lighrail_departures(to_work, 3)

    print('lightrail:')
    for lrd in lr_departures:
        print(lrd.strftime(time_format))

    bus_infos = get_bus_infos(to_work, 3)

    print('bus:')
    for bus in bus_infos:
        print(bus.njt_estimate.strftime(time_format))


if __name__ == '__main__':
    main()
