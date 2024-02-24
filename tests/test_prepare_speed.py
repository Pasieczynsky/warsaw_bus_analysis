from unittest.mock import MagicMock
from analyse.prepare_speed import Velocity
from unittest.mock import call
import pytest
import os


def test_init_with_invalid_path_bus_location():
    with pytest.raises(ValueError):
        Velocity(path_bus_location="/invalid/path")

def test_process_data():
    # Arrange
    data = {
        ("1", "bus1", "2"): {"Time": "2022-01-01 10:00:00", "Lat": 52.0, "Lon": 21.0},
        ("1", "bus2", "2"): {"Time": "2022-01-01 10:01:00", "Lat": 52.1, "Lon": 21.1},
    }
    prev_data = {
        ("1", "bus1", "2"): {"Time": "2022-01-01 09:59:00", "Lat": 51.9, "Lon": 20.9},
        ("1", "bus2", "2"): {"Time": "2022-01-01 10:00:00", "Lat": 52.1, "Lon": 21.1},
    }
    file_to_save = MagicMock()

    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "buses_location",
                        "buses_location_2024-02-15_18-17-37")
    prepare_speed = Velocity(path_bus_location=path)

    # Act
    prepare_speed._Velocity__process_data(data, prev_data, file_to_save)

    # Assert
    expected_calls = [
        call("bus1, 50, 52.0, 21.0\n")
    # second bus does not move so it is not saved
    ]
    file_to_save.write.assert_has_calls(expected_calls)
