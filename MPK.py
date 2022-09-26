import datetime
import math
from enum import IntEnum

import requests
from bs4 import BeautifulSoup

class TypeOfDay(IntEnum):
    REGULAR = 1
    SATURDAY = 2
    HOLIDAY = 3

    # returns TypeOfDay based on date
    @staticmethod
    def get_type_of_the_day(date):
        if date.strftime("%A") == 'Saturday':
            return TypeOfDay.SATURDAY
        elif date.strftime("%A") == 'Sunday':
            return TypeOfDay.HOLIDAY
        return TypeOfDay.REGULAR


class MPKBus:
    """A class representing a MPK bus and it's information"""

    def __init__(self, lane_number, date = datetime.date.today()):
        self.lane_number = lane_number
        self.date = date

        self.__URL = 'https://rozklady.mpk.krakow.pl/'
        self.__payload = {'lang': 'PL', 'rozklad': date.strftime("%Y%m%d"), 'linia': str(self.lane_number) + '__1'}

        session = requests.Session()
        session.get(self.__URL)

        self.routes = self.__get_routes(session)

        self.schedule = []
        self.stops = []

        for route, route_id in zip(self.routes, range(len(self.routes))):
            self.stops.append(self.__get_stops(route_id + 1, session))
            self.schedule.append([])
            for stop, stop_id in zip(self.stops[route_id], range(len(self.stops[route_id]) - 1)):
                #print(route_id, ' : ', stop_id + 1 + max(0, route_id * len(self.stops[0]) - 1))
                self.schedule[route_id].append(self.__get_schedule(route_id + 1, stop_id + 1 + max(0, route_id * len(self.stops[0]) - 1), session))

    def __get_routes(self, session):
        page = session.get(self.__URL, params=self.__payload)
        soup = BeautifulSoup(page.content, "html.parser")
        routes = soup.find_all('td', attrs={'style': 'text-align: left; white-space: nowrap; '})[1]
        routes = routes.find_all('a')

        routes = [route.text[48:-45] for route in routes]

        return routes

    def __get_stops(self, route, session):
        payload = self.__payload
        payload['linia'] = str(self.lane_number) + '__' + str(route)
        page = session.get(self.__URL, params=payload)
        soup = BeautifulSoup(page.content, "html.parser")

        stops = soup.find_all('td', attrs={'style': ' text-align: right; '})
        list_of_stops = [stop.text[3:-6] for stop in stops][1:]
        list_of_stops[-1] = list_of_stops[-1][40:-26]

        return list_of_stops

    def __get_schedule(self, route, stop, session):
        payload = self.__payload
        payload['linia'] = str(self.lane_number) + '__' + str(route) + '__' + str(stop)
        page = session.get(self.__URL, params=payload)
        soup = BeautifulSoup(page.content, "html.parser")

        departures = []
        timetable = soup.find('td', attrs={'style':  '  border-right: solid black 1px;  text-align: left; white-space: nowrap;  border-bottom: solid black 1px; padding-right: 10px;  '}).parent.parent.find_all('tr')[1:-2]
        for tr in timetable:
            tr = tr.find_all('td')
            hour = int(tr[0].text)
            minutes = tr[TypeOfDay.get_type_of_the_day(self.date)].text.split(' ')
            minutes = [min for min in minutes if min.isdigit()]

            for min in minutes:
                departures.append(datetime.time(hour, int(min)))

        return departures