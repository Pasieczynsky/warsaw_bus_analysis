from datetime import datetime, timedelta
import time
from typing import Dict, Optional, Union
import requests
import os
import json
import concurrent.futures

# time interval for downloading data from API
TIME_INTERVAL = 10
# delta time for validating buses data
TIME_DELTA = 30

# TODO:
# - add terminal view:
#   * asking to download data if exists already
#   * progress bars or something like that


class WarsawAPI:
    api_key: str
    bus_url: str
    bus_stop_url: str
    scheldue_url: str
    routes_url: str
    dictionary_url: str

    def __init__(self, api_key):
        self.api_key = api_key
        self.bus_url = "https://api.um.warszawa.pl/api/action/busestrams_get/"
        self.bus_stop_url = "https://api.um.warszawa.pl/api/action/dbstore_get/"
        self.scheldue_url = "https://api.um.warszawa.pl/api/action/dbtimetable_get/"
        self.routes_url = (
            "https://api.um.warszawa.pl/api/action/public_transport_routes/"
        )
        self.dictionary_url = (
            "https://api.um.warszawa.pl/api/action/public_transport_dictionary/"
        )

    # TODO: response is empty -> schedule not found, than not raise exception
    # maybe add attribute MAX_REQUESTS to stop program after some time
    def __get_data_from_api(
        self,
        url: str,
        params: Dict[str, Union[str, int, None]],
        is_schedule: bool = False,
    ) -> Dict:
        """
        Get data from Warsaw API
        url: str - url to API
        params: Dict[str, Union[str, int, None]] - parameters for request to API
        """

        error_counter = 0
        while True:
            try:
                response = requests.get(url, params=params).json()
            except requests.exceptions.RequestException:
                error_counter += 1

            # Check if response is valid
            if (len(response["result"]) == 0) or (isinstance(response["result"], str)):
                if is_schedule:
                    error_counter += 25
                else:
                    error_counter += 1
                if error_counter >= 50:
                    if is_schedule and len(response["result"]) == 0:
                        # schedule could not be found (technical stops, etc.)
                        return {}
                    # stop program and print response
                    raise ValueError(response)
                time.sleep(0.5)
            else:
                # Success
                return response["result"]

    def __validate_buses_data(self, response: Dict) -> Dict:
        """
        Validate buses data, remove buses with wrong location or time
        response: Dict - response from Warsaw API
        """

        now = datetime.now()
        for bus in response.copy():

            try:
                bus_time = datetime.strptime(bus["Time"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                response.remove(bus)
                continue

            diff = (now - bus_time).seconds
            if diff > (TIME_DELTA):
                response.remove(bus)
            elif not (20 < bus["Lon"] < 22) or not (52 < bus["Lat"] < 53):
                response.remove(bus)
            else:
                continue

        return response

    def __get_buses_location(
        self, line: Optional[str] = None, brigade: Optional[str] = None
    ) -> dict:
        """
        Get buses location from Warsaw API
        if line and brigade are None, return all buses location
        if line is not None, return buses location for line
        if line and brigade is not None, return buses location for line and brigade
        """
        params = {
            "resource_id": "f2e5503e-927d-4ad3-9500-4ab9e55deb59",
            "apikey": self.api_key,
            "type": "1",
            "line": line,
            "brigade": brigade,
        }

        response = self.__get_data_from_api(self.bus_url, params)
        return self.__validate_buses_data(response)

    def download_buses_location_by_time(
        self,
        path: Optional[str] = os.getcwd(),
        download_time: int = 1,
        line: Optional[str] = None,
        brigade: Optional[str] = None,
    ) -> int:
        """
        Download buses location by time and save to file
        path: Optional[str] - path to directory where files will be saved
        download_time: int - the time for which data will be downloaded (in minutes)
        line: Optional[str] - line number
        brigade: Optional[str] - brigade number
        """

        # set end time for downloading data
        end_time = datetime.now() + timedelta(minutes=download_time)

        # path to directory where files will be saved
        dir_path = os.path.join(path, "buses_location")

        # create directory if not exists
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

        # create new folder for files
        date_and_hour = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = f"buses_location_{date_and_hour}"
        new_dir_path = os.path.join(dir_path, folder_name)
        os.mkdir(new_dir_path)

        # collect data from API
        # sends request to the API every TIME_INTERVAL seconds
        index = 0
        while datetime.now() < end_time:
            if index != 0:
                time.sleep(
                    TIME_INTERVAL - 1
                )  # -1 is a epsilon caused by the time of the request

            response = self.__get_buses_location(line, brigade)

            print(f"Request number: {index}, actual time: {datetime.now()}")

            path = os.path.join(new_dir_path, f"{index}.json")
            with open(path, "w") as f:
                json.dump(response, f)

            index += 1

        return index + 1

    def __parse_dict(self, response: Dict) -> Dict:
        """
        Parse dict from Warsaw API to more readable and useable format
        response: Dict - response from Warsaw API
        """
        result = {}
        for info in response["values"]:
            result[info["key"]] = info["value"]

        return result

    def download_bus_stops(self, path: Optional[str] = os.getcwd()) -> None:
        """
        Download bus stops from Warsaw API and save to file
        path: Optional[str] - path to directory where file will be saved
        """

        params = {
            "id": "ab75c33d-3a26-4342-b36a-6e5fef0a3ac3",
            "apikey": self.api_key,
        }

        response = self.__get_data_from_api(self.bus_stop_url, params)

        busStops = {}

        for stop in response:
            stop = self.__parse_dict(stop)
            key = stop["zespol"] + "_" + stop["slupek"]
            busStops[key] = stop

        path = os.path.join(path, "bus_stops", "bus_stops.json")
        # check if directory exists
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        with open(path, "w") as f:
            json.dump(busStops, f)

    def download_routes(self, path: Optional[str] = os.getcwd()) -> None:
        """
        Download routes from Warsaw API and save to file
        path: Optional[str] - path to directory where file will be saved
        """

        params = {
            "apikey": self.api_key,
        }

        response = self.__get_data_from_api(self.routes_url, params)

        path = os.path.join(path, "bus_stops", "routes.json")
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        with open(path, "w") as f:
            json.dump(response, f)

    def download_dictionary(self, path: Optional[str] = os.getcwd()) -> None:
        """
        Download dictionaries of terms for urban transport
        path: Optional[str] - path to directory where file will be saved
        """

        params = {
            "apikey": self.api_key,
        }

        response = self.__get_data_from_api(self.dictionary_url, params)

        path = os.path.join(path, "bus_stops", "dictionary.json")
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        with open(path, "w") as f:
            json.dump(response, f)

    def __get_schedule(self, line: int, path: Optional[str] = os.getcwd()) -> None:
        """
        Download schedule from Warsaw API and save to file
        line: int - line number
        path: Optional[str] - path to directory where file will be saved
        """

        schedule_dir = os.path.join(path, "bus_stops", "lines")
        routes = os.path.join(path, "bus_stops", "routes.json")
        if not os.path.exists(routes):
            raise ValueError(
                "Public transport routes not found, please download routes first (download_routes)"
            )

        line_schedule = {}
        line_stops = []

        with open(routes, "r") as f:
            data = json.load(f)
            # collect all stops for line
            for route_name in data[line]:
                for stop_number in data[line][route_name]:
                    line_stops.append(data[line][route_name][stop_number])

            # collect schedule for each stop
            for stop in range(len(line_stops)):
                params = {
                    "id": "e923fa0e-d96c-43f9-ae6e-60518c9f3238",
                    "apikey": self.api_key,
                    "busstopId": line_stops[stop]["nr_zespolu"],
                    "busstopNr": line_stops[stop]["nr_przystanku"],
                    "line": line,
                }

                # get schedule from API
                response = self.__get_data_from_api(
                    self.scheldue_url, params, is_schedule=True
                )

                if response == {}:  # schedule not found
                    continue

                bus_stop_key = (
                    line_stops[stop]["nr_zespolu"]
                    + "_"
                    + line_stops[stop]["nr_przystanku"]
                )
                for schedule in response:
                    schedule = self.__parse_dict(schedule)
                    brigade = schedule["brygada"]
                    # check if brigade exists in line_schedule
                    if brigade not in line_schedule:
                        line_schedule[brigade] = {}

                    # check if bus_stop_key exists in line_schedule[brigade]
                    if bus_stop_key not in line_schedule[brigade]:
                        line_schedule[brigade][bus_stop_key] = []

                    line_schedule[brigade][bus_stop_key].append(schedule["czas"])
                    # line_schedule[brigade][bus_stop_key].append(schedule)

        # create directory if not exists
        if not os.path.exists(schedule_dir):
            os.makedirs(schedule_dir)

        # save schedule to file
        path = os.path.join(schedule_dir, f"{line}.json")
        with open(path, "w") as f:
            json.dump(line_schedule, f)

        print(f"Schedule for line {line} saved to file")

    def download_schedule(self, path: Optional[str] = os.getcwd()) -> None:
        """
        Download schedule from Warsaw API and save to file
        path: Optional[str] - path to directory where file will be saved
        """

        routes = os.path.join(path, "bus_stops", "routes.json")
        if not os.path.exists(routes):
            raise ValueError(
                "Public transport routes not found, please download routes first (download_routes)"
            )

        with open(routes, "r") as f:
            data = json.load(f)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for line in data:
                if line > "999" or int(line) > 99:
                    # only lines with letters and numbers greater than 99 (buses)
                    print(f"Downloading schedule for line {line}")
                    futures.append(executor.submit(self.__get_schedule, line, path))

            # Wait for all futures to complete
            concurrent.futures.wait(futures)
