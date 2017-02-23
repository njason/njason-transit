from datetime import datetime

import requests
from bs4 import BeautifulSoup


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


def get_bus_departures():
    url = ('http://mybusnow.njtransit.com/bustime/wireless/html/eta.jsp?'
           'route=87&direction=Hoboken&id=21061&showAllBusses=off')

    response = requests.get(url)


lr_departures = get_lighrail_departures(3)

for lrd in lr_departures:
    print(lrd.strftime('%-I:%M %p'))
