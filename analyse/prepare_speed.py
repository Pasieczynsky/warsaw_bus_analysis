import json
import os
from datetime import datetime
from typing import Optional
import pandas as pd
from .tools import choose_data, calculate_velocity, get_busID


class Velocity:
    """
    A class that represents the velocity of buses.
    """
    path_bus_location: str  # path to the directory with the data
    path_speed_data: str  # path to the file with the speed data

    def __init__(self, path_bus_location: str = None, path_speed_data: str = None):
        """
        Initializes a Velocity object.

        Parameters:
        - path_bus_location (str): Path to the directory with the data. If None, a default path will be chosen.
        - path_speed_data (str): Path to the file with the speed data. If None, a default path will be chosen.
        """
        if path_bus_location is None:
            self.path_bus_location = choose_data("buses_location")
        else:
            if not os.path.exists(path_bus_location):
                raise ValueError("The directory with the data does not exist.")
            else:
                self.path_bus_location = path_bus_location

        if path_speed_data is None:
            # open file to save the data
            path_to_save = os.path.dirname(os.path.dirname(__file__))
            path_to_save = os.path.join(path_to_save, "speed_data")
            # check if the directory exists
            if not os.path.exists(path_to_save):
                os.makedirs(path_to_save)
            self.path_speed_data = path_to_save
        else:
            # check if the directory exists
            if not os.path.exists(path_speed_data):
                raise ValueError("The directory with the data does not exist.")
            else:
                self.path_speed_data = path_speed_data

    @staticmethod
    def __change_format(data: list[dict]) -> dict:
        """
        Changes the format of the data from the list of dictionaries to the dictionary with the bus ID as the key.

        Parameters:
        - data (list[dict]): The data in the original format.

        Returns:
        - dict: The data in the new format.
        """
        new_data = {}
        for bus in data:
            new_data[get_busID(bus["VehicleNumber"], bus["Lines"], bus["Brigade"])] = {
                "Lat": bus["Lat"],
                "Lon": bus["Lon"],
                "Time": bus["Time"] if "Time" in bus else "0",
            }
        return new_data

    def prepare_speed(self):
        """
        Reads the data from the directory and prepares it for analysis.
        """

        path = self.path_bus_location
        # count how many files are in the directory
        count_files = len(os.listdir(path))

        # get date from the path
        date = path.split("_")[-2] + "_" + path.split("_")[-1]
        path_to_save = os.path.join(self.path_speed_data, "speed_data_" + date + ".csv")

        # open the file to save the data
        file_to_save = open(path_to_save, "w")
        file_to_save.write("line,velocity,latitude,longitude\n")

        prev_file = open(os.path.join(path, "0.json"), "r")
        prev_data = json.load(prev_file)
        prev_data = self.__change_format(prev_data)

        # iterate over all the files in the directory
        for i in range(1, count_files):
            # open the file
            with open(os.path.join(path, str(i) + ".json"), "r") as file:
                data = self.__change_format(json.load(file))
                # iterate over all the buses
                for bus in data:
                    # check if the bus is in the previous data
                    if bus in prev_data:
                        # calculate the velocity
                        # fix the time difference
                        delta_time = datetime.strptime(
                            data[bus]["Time"], "%Y-%m-%d %H:%M:%S"
                        ) - datetime.strptime(prev_data[bus]["Time"], "%Y-%m-%d %H:%M:%S")
                        velocity = calculate_velocity(
                            data[bus]["Lat"],
                            data[bus]["Lon"],
                            prev_data[bus]["Lat"],
                            prev_data[bus]["Lon"],
                            delta_time.total_seconds(),
                        )
                        if velocity > 0:
                            # if the velocity is greater than 0, save the data
                            file_to_save.write(
                                f"{bus[1]}, {velocity}, {data[bus]["Lat"]}, {data[bus]["Lon"]}\n"
                            )
                prev_data = data

        file_to_save.close()

    def change_path_data(self, path: Optional[str] = None):
        """
        Changes the path to the directory with the data.

        Parameters:
        - path (str): The new path to the directory with the data. If None, a default path will be chosen.
        """
        if path is None:
            self.path_bus_location = choose_data("buses_location")
        else:
            if not os.path.exists(path):
                raise ValueError("The directory with the data does not exist.")
            else:
                self.path_bus_location = path

    def get_speed_data(self) -> pd.DataFrame:
        """
        Returns the speed data from the file.

        Returns:
        - pd.DataFrame: The speed data.
        """
        path = choose_data("speed_data")
        return pd.read_csv(path)
