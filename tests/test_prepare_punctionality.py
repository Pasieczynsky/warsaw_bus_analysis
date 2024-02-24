import pytest
import os
from unittest import mock
from analyse import Punctionality


@pytest.fixture
def punctionality():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "buses_location",
                        "buses_location_2024-02-15_18-17-37")
    punctionality = Punctionality(path_bus_location=path)
    return punctionality


def test_init_with_invalid_path_bus_location():
    with pytest.raises(ValueError):
        Punctionality(path_bus_location="/invalid/path")


def test_set_path_with_non_existing_path(punctionality):
    with pytest.raises(ValueError):
        punctionality._Punctionality__set_path("/invalid/path", "schedule")


def test_load_bus_location_data(punctionality):
    punctionality.path_bus_location = "/path/to/bus_location"
    file_index = 0
    expected_data = [{"VehicleNumber": 1, "Lines": "123", "Brigade": "456", "Lat": 52.3, "Lon": 21.2}]
    with mock.patch("builtins.open", mock.mock_open(
            read_data='[{"VehicleNumber": 1, "Lines": "123", "Brigade": "456", "Lat": 52.3, "Lon": 21.2}]')):
        data = punctionality._Punctionality__load_bus_location_data(punctionality.path_bus_location, file_index)
    assert data == expected_data


def test_load_schedule(punctionality):
    punctionality.path_schedule = "/path/to/schedule"
    bus_line = "123"
    expected_schedule = {"123": {
        "456": {"1": {"ulica_id": "2513", "nr_zespolu": "R-03", "nr_przystanku": "00", "typ": "6", "odleglosc": 0}}}}
    with mock.patch("builtins.open", mock.mock_open(
            read_data='{"123": {"456": {"1": '
                      '{"ulica_id": "2513", "nr_zespolu": "R-03", '
                      '"nr_przystanku": "00", "typ": "6", "odleglosc": 0}}}}')):
        schedule = punctionality._Punctionality__load_schedule({}, punctionality.path_schedule, bus_line)
    assert schedule[bus_line] == expected_schedule


def test_find_closest_stop(punctionality):
    bus = {"Lines": "123", "Brigade": "456", "VehicleNumber": "1234", "Time": "2024-02-16 15:25:00", "Lat": 52.3,
           "Lon": 21.2}
    schedule = {"123": {"456": {"1": ["12:00:00", "13:00:00"], "2": ["15:30:00", "16:30:00"]}}}
    bus_stops = {"1": {"zespol": "123", "slupek": "4", "szer_geo": 51.3, "dlug_geo": 21.0},
                 "2": {"zespol": "123", "slupek": "5", "szer_geo": 52.3, "dlug_geo": 21.2}}
    expected_result = ("2", 0.0, 5 * 60)
    result = punctionality._Punctionality__find_closest_stop(bus, schedule, bus_stops)
    assert result == expected_result


def test_update_data_to_save(punctionality):
    data_to_save = {}
    bus_id = ("123", "456")
    closest_stop = "R-03_00"
    bus = {"VehicleNumber": 1, "Lines": "123", "Brigade": "456", "Lat": 52.3, "Lon": 21.2}
    time = 0
    delta_dist = 0.01
    expected_data_to_save = {('123', '456'): {'R-03_00': (0, 0.01, 52.3, 21.2)}}
    result = punctionality._Punctionality__update_data_to_save(data_to_save, bus_id, closest_stop, bus, time,
                                                               delta_dist)
    assert result == expected_data_to_save
