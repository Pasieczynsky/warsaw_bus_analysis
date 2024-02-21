import os
import math


def choose_file(files: list[str]) -> str:
    """In infinite loop, asks the user to choose the file with the data of the buses location."""
    # print the list of files
    print("Choose the file with the data")
    for i, file in enumerate(files):
        print(f"{i + 1}. {file}")

    # ask the user to choose the file
    while True:
        try:
            choice = int(input("Enter the number of the file: "))
            if 0 < choice <= len(files):
                return files[choice - 1]
            else:
                print("Invalid input. Enter the number of the file.")
        except ValueError:
            print("Invalid input. Enter the number of the file.")


def choose_data(data_type: str) -> str | None:
    """Returns the path of the data file."""

    # find the path of the bus_location directory in the parent directory
    path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # check if the buses_location directory exists
    if not (os.path.exists(os.path.join(path, data_type))):
        print("The directory with the data does not exist.")
        return None

    # list all the files in the directory one by one
    files = os.listdir(os.path.join(path, data_type))

    # check if there are any files in the directory
    if not files:
        print("The directory with the data is empty.")
        return None

    # ask the user to choose the file
    file = choose_file(files)
    return os.path.join(path, data_type, file)


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculates the distance between two sets of latitude and longitude coordinates using the Haversine formula."""
    R = 6371  # Radius of the Earth in kilometers

    # Convert latitude and longitude to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Calculate the differences between the coordinates
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Apply the Haversine formula
    a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance


def calculate_velocity(lat1, lon1, lat2, lon2, time):
    """
    Calculates the velocity between two sets of latitude and longitude coordinates using the Haversine formula and
    time difference.
    """

    # Calculate the distance
    distance = calculate_distance(lat1, lon1, lat2, lon2)

    # Calculate velocity
    if time == 0:
        velocity = 0
    else:
        # convert time to hours
        time = time / 3600
        velocity = distance / time

    # if the velocity is greater than 90 km/h, set it to 50 km/h
    if velocity > 90:
        velocity = 50

    return velocity


def get_busID(vehicle_number: int, line: int, brigade: int) -> tuple:
    """Returns a tuple with the bus ID in the format VehicleNumber_Line_Brigade."""
    return (vehicle_number, line, brigade)
