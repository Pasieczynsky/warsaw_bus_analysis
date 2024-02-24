import json
from .tools import choose_data, calculate_distance, get_busID
import pandas as pd
import os
from datetime import datetime


class Punctionality:
    """
    Class for preparing and analyzing bus punctuality data.
    """

    path_bus_location: str
    path_schedule: str
    path_stops: str
    path_to_save: str

    # if the path is not given, the user will be asked to choose the file to analyse
    def __init__(
            self,
            path_bus_location: str = None,
            path_schedule: str = None,
            path_stops: str = None,
            path_to_save: str = None,
    ):
        """
        Initializes the Punctionality object.

        Args: path_bus_location (str, optional): Path to the directory containing bus location data. If not provided,
        the user will be prompted to choose the file. Defaults to None. path_schedule (str, optional): Path to the
        directory containing schedule data. Defaults to None. path_stops (str, optional): Path to the file containing
        bus stops data. Defaults to None.
        """
        if path_bus_location is None:
            self.path_bus_location = choose_data("buses_location")
        else:
            if not os.path.exists(path_bus_location):
                raise ValueError("The directory with the data does not exist.")
            else:
                self.path_bus_location = path_bus_location

        self.path_schedule = self.__set_path(path_schedule, "schedule")
        self.path_stops = self.__set_path(path_stops, "stops")
        self.__set_path_to_save(path_to_save)

    @staticmethod
    def __set_path(path: str, type_of_data: str):
        """
        Sets the path for schedule or stops data.

        Args:
            path (str): Path to the directory or file.
            type_of_data (str): Type of data (schedule or stops).

        Returns:
            str: The updated path.

        Raises:
            ValueError: If the directory or file does not exist.
        """
        # check if the path exists
        if path is None:
            path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # check if bus_stops directory exists
            path = os.path.join(path, "bus_stops")
            if not os.path.exists(path):
                raise ValueError("The directory with the data does not exist.")
            else:
                if type_of_data == "schedule":
                    path = os.path.join(path, "lines")
                elif type_of_data == "stops":
                    path = os.path.join(path, "bus_stops.json")
                else:
                    raise ValueError("Invalid type")

                if not os.path.exists(path):
                    raise ValueError("The directory with the data does not exist.")
                else:
                    return path
        else:
            # check if the path exists
            if not os.path.exists(path):
                raise ValueError("The directory with the data does not exist.")
            else:
                return path

    def __set_path_to_save(self, path_to_save: str = None):
        """
        Sets the path to save the prepared data.
        """
        if path_to_save is not None:
            self.path_to_save = path_to_save
            return

        date = (
                self.path_bus_location.split("_")[-2]
                + "_"
                + self.path_bus_location.split("_")[-1]
        )

        path = os.path.dirname(os.path.dirname(self.path_bus_location))
        path = os.path.join(path, "punctionality_data")

        if not os.path.exists(path):
            os.makedirs(path)
        path = os.path.join(path, "punctionality_data_" + date + ".csv")
        self.path_to_save = path

    def __load_bus_stops(self):
        """
        Loads the bus stops data from the file.

        Returns:
            dict: The bus stops data.
        """
        with open(self.path_stops, "r") as file:
            return json.load(file)

    def prepare_data(self):
        """
        Prepares the data for analysis.
        Merges bus position data with the schedule and bus stops.
        """

        file_to_save = open(self.path_to_save, "w")
        file_to_save.write(
            "VehicleNumber,Line,Brigade,Stop,DiffTime,DiffDist,BusLat,BusLon\n"
        )

        data_to_save = {}
        bus_stops = self.__load_bus_stops()
        count_files = len(os.listdir(self.path_bus_location))

        # Iterate over all files with bus location data
        for i in range(count_files):
            data = self.__load_bus_location_data(self.path_bus_location, i)
            schedule = {}

            # Iterate over all buses in the file
            for bus in data:
                # Skip trams (sometimes they are in the data, don't know why)
                if bus["Lines"] < "999":
                    if int(bus["Lines"]) < 100:
                        continue

                bus_id = get_busID(bus["VehicleNumber"], bus["Lines"], bus["Brigade"])
                schedule = self.__load_schedule(
                    schedule, self.path_schedule, bus["Lines"]
                )

                if bus["VehicleNumber"] == "1000" and bus["Lat"] == 52.22274:
                    print(bus)
                # check if the bus brigade is in the schedule
                if bus["Brigade"] not in schedule[bus["Lines"]]:
                    continue

                closest_stop, delta_dist, min_time = self.__find_closest_stop(
                    bus, schedule, bus_stops
                )

                if closest_stop is None:
                    continue

                data_to_save = self.__update_data_to_save(
                    data_to_save, bus_id, closest_stop, bus, min_time, delta_dist
                )

                if data_to_save is None:
                    continue

            print(f"File {i} of {count_files - 1} done")

        self.__save_data_to_file(data_to_save, file_to_save)
        file_to_save.close()

    @staticmethod
    def __load_bus_location_data(path_bus_location, file_index):
        """
        Loads the bus location data from the file.

        Args:
            path_bus_location (str): Path to the directory containing bus location data.
            file_index (int): Index of the file to load.

        Returns:
            list: The bus location data.
        """
        with open(
                os.path.join(path_bus_location, str(file_index) + ".json"), "r"
        ) as file:
            return json.load(file)

    @staticmethod
    def __load_schedule(schedule, path_schedule, bus_line):
        """
        Loads the schedule data from the file.

        Args:
            schedule (dict): The current schedule data.
            path_schedule (str): Path to the directory containing schedule data.
            bus_line (str): The bus line.

        Returns:
            dict: The updated schedule data.
        """
        if bus_line not in schedule:
            with open(os.path.join(path_schedule, bus_line + ".json"), "r") as f:
                schedule[bus_line] = json.load(f)
        return schedule

    @staticmethod
    def __find_closest_stop(bus, schedule, bus_stops):
        """
        Finds the closest bus stop for a given bus.

        Args:
            bus (dict): The bus data.
            schedule (dict): The schedule data.
            bus_stops (dict): The bus stops data.

        Returns:
            tuple: The closest stop, delta distance, and minimum time difference.
        """
        delta_dist = 0.01  # 10 meters
        closest_stop = None
        # Minimum time difference in seconds
        # Starting with 1 hour, because there should be
        # no bus that is late for more than 1 hour
        min_time = 3600

        for stop in schedule[bus["Lines"]][bus["Brigade"]].keys():
            if stop not in bus_stops:
                continue

            distance = calculate_distance(
                bus["Lat"],
                bus["Lon"],
                float(bus_stops[stop]["szer_geo"]),
                float(bus_stops[stop]["dlug_geo"]),
            )

            if distance < delta_dist:
                bus_time = datetime.strptime(bus["Time"], "%Y-%m-%d %H:%M:%S").strftime(
                    "%H:%M:%S"
                )

                for stop_time in schedule[bus["Lines"]][bus["Brigade"]][stop]:
                    # Fix date from schedule (like 25:00:00 -> 01:00:00)
                    if int(stop_time[:2]) >= 24:
                        stop_time = str(int(stop_time[:2]) - 24) + stop_time[2:]

                    diff = abs(
                        (
                                datetime.strptime(stop_time, "%H:%M:%S")
                                - datetime.strptime(bus_time, "%H:%M:%S")
                        ).seconds
                    )

                    min_time = min(min_time, diff)

                # Any bus that is late for more than 1 hour is not considered
                if min_time >= 3600:
                    continue
                else:
                    delta_dist = distance
                    closest_stop = stop
            else:
                continue

        return closest_stop, delta_dist, min_time

    @staticmethod
    def __update_data_to_save(
            data_to_save: dict, bus_id, closest_stop, bus, time, delta_dist
    ):
        """
        Updates the data to save.

        Args:
            data_to_save (dict): The current data to save.
            bus_id (tuple): The bus ID.
            closest_stop (str): The closest bus stop.
            bus (dict): The bus data.
            time (int): The time difference.
            delta_dist (float): The distance difference.

        Returns:
            dict: The updated data to save.
        """
        if bus_id not in data_to_save.keys():
            data_to_save[bus_id] = {}

        # If the bus stop is not in the data, add it
        if closest_stop not in data_to_save[bus_id]:
            data_to_save[bus_id][closest_stop] = (
                time,
                delta_dist,
                bus["Lat"],
                bus["Lon"],
            )

        elif time < data_to_save[bus_id][closest_stop][0]:
            data_to_save[bus_id][closest_stop] = (
                time,
                delta_dist,
                bus["Lat"],
                bus["Lon"],
            )

        return data_to_save

    @staticmethod
    def __save_data_to_file(data_to_save, file_to_save):
        """
        Saves the data to a file.

        Args:
            data_to_save (dict): The data to save.
            file_to_save (file): The file to save the data to.
        """
        for bus in data_to_save:
            vehicle_number = bus[0]
            line = bus[1]
            brigade = bus[2]

            for stop in data_to_save[bus]:
                file_to_save.write(
                    f"{vehicle_number},{line},{brigade},{stop},{data_to_save[bus][stop][0]},"
                    f"{data_to_save[bus][stop][1]},{data_to_save[bus][stop][2]},{data_to_save[bus][stop][3]}\n"
                )

    def get_data(self):
        """
        Returns the prepared data.

        Returns:
            pd.DataFrame: The prepared data.
        
        Raises:
            ValueError: If the file with the data does not exist.
        """

        if not os.path.exists(self.path_to_save):
            raise ValueError("The file with the data does not exist.")

        # load the data from the file
        data = pd.read_csv(self.path_to_save)
        return data
