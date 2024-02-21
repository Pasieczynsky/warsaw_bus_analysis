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

    def prepare_data(self):
        """
        Prepares the data for analysis.
        Merges bus position data with the schedule and bus stops.
        """

        file_to_save = open(self.path_to_save, "w")
        file_to_save.write(
            "VehicleNumber,Line,Brigade,Stop,DiffTime,DiffDist,BusLat,BusLon\n"
        )

        # Dict with the bus ID as the key
        # Value is a list of dictionaries with bus_stops and the difference between actual and planned time
        # bus -> bus_stop -> (diff_time, diff_dist)
        data_to_save = {}

        # load bus stops data
        with open(self.path_stops, "r") as file:
            bus_stops = json.load(file)

        count_files = len(os.listdir(self.path_bus_location))

        # iterate over all the files in the directory
        for i in range(count_files):
            # open file with bus location
            with open(
                    os.path.join(self.path_bus_location, str(i) + ".json"), "r"
            ) as file:
                data = json.load(file)

                # iterate over all the buses
                schedule = {}
                for bus in data:
                    if bus["Lines"] < "999":
                        if int(bus["Lines"]) < 100:
                            continue

                    bus_id = get_busID(
                        bus["VehicleNumber"], bus["Lines"], bus["Brigade"]
                    )
                    # load the schedule for the bus line if it is not already loaded
                    if bus["Lines"] not in schedule:
                        with open(
                                os.path.join(self.path_schedule, bus["Lines"] + ".json"),
                                "r",
                        ) as f:
                            schedule[bus["Lines"]] = json.load(f)

                    # check if the bus brigade is in the schedule
                    if bus["Brigade"] not in schedule[bus["Lines"]]:
                        continue

                    # check if the bus is in data_to_save
                    if bus_id not in data_to_save:
                        data_to_save[bus_id] = {}

                    # find the closest bus stop to the bus
                    delta_dist = 0.01  # distance in km
                    closest_stop = None
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
                            bus_time = datetime.strptime(
                                bus["Time"], "%Y-%m-%d %H:%M:%S"
                            ).strftime("%H:%M:%S")
                            # find the closest time
                            best_time = (
                                3600  # difference between the actual and planned time
                            )
                            for stop_time in schedule[bus["Lines"]][bus["Brigade"]][
                                stop
                            ]:
                                if int(stop_time[:2]) >= 24:
                                    stop_time = (
                                            str(int(stop_time[:2]) - 24) + stop_time[2:]
                                    )

                                diff = abs(
                                    (
                                            datetime.strptime(stop_time, "%H:%M:%S")
                                            - datetime.strptime(bus_time, "%H:%M:%S")
                                    ).seconds
                                )

                                best_time = min(best_time, diff)

                            # check if the time difference is not too big
                            if best_time >= 3600:
                                continue
                            else:
                                delta_dist = distance
                                closest_stop = stop
                        else:
                            continue

                    # any close stop found
                    if closest_stop is None or best_time >= 3600:
                        continue

                    # check if the bus stop is in data_to_save
                    if closest_stop not in data_to_save[bus_id]:
                        data_to_save[bus_id][closest_stop] = (
                            best_time,
                            delta_dist,
                            bus["Lat"],
                            bus["Lon"],
                        )
                    else:
                        # check if the time difference is smaller than the previous one
                        if best_time < data_to_save[bus_id][closest_stop][0]:
                            data_to_save[bus_id][closest_stop] = (
                                best_time,
                                delta_dist,
                                bus["Lat"],
                                bus["Lon"],
                            )
                        else:
                            continue
            print(f"File {i} of {count_files - 1} done")

        # save the data to the file
        for bus in data_to_save:
            vehicle_number = bus[0]
            line = bus[1]
            brigade = bus[2]
            for stop in data_to_save[bus]:
                file_to_save.write(
                    f"{vehicle_number},{line},{brigade},{stop},{data_to_save[bus][stop][0]},"
                    f"{data_to_save[bus][stop][1]},{data_to_save[bus][stop][2]},{data_to_save[bus][stop][3]}\n"
                )

        file_to_save.close()

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
