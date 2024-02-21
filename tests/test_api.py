import pytest
import os
from datetime import datetime
from unittest import mock
from requests_mock import Mocker
from warsaw_api import WarsawAPI


@pytest.fixture
def api_key():
    return "YOUR_API_KEY"


@pytest.fixture
def api():
    return WarsawAPI(api_key="YOUR_API_KEY")


def test_get_data_from_api(api):
    with Mocker() as m:
        url = "https://api.um.warszawa.pl/api/action/busestrams_get/"
        params = {
            "resource_id": "f2e5503e-927d-4ad3-9500-4ab9e55deb59",
            "apikey": api.api_key,
            "type": "1",
            "line": None,
            "brigade": None,
        }
        response_data = {"result": [{"bus_id": 1, "Lon": 21.0, "Lat": 52.0}]}
        m.get(url, json=response_data)

        response = api._WarsawAPI__get_data_from_api(url, params)

        assert response == response_data["result"]


def test_validate_buses_data(api):
    # current time
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response = [
        {"bus_id": 1, "Time": now, "Lon": 21.2, "Lat": 52.3},
        {"bus_id": 2, "Time": now, "Lon": 20.0, "Lat": 53.0},
        {"bus_id": 3, "Time": "2022-01-01 11:00:00", "Lon": 21.5, "Lat": 52.5},
    ]
    expected_result = [
        {"bus_id": 1, "Time": now, "Lon": 21.2, "Lat": 52.3},
    ]

    validated_data = api._WarsawAPI__validate_buses_data(response)

    assert validated_data == expected_result


def test_get_buses_location(api):
    line = "123"
    brigade = "456"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    expected_response = [{"bus_id": 1, "Lon": 21.2, "Lat": 52.3, "Time": now}]

    with Mocker() as m:
        url = "https://api.um.warszawa.pl/api/action/busestrams_get/"
        m.get(url, json={"result": expected_response})

        response = api._WarsawAPI__get_buses_location(line, brigade)

        assert response == expected_response


def test_parse_dict(api):
    response = {
        "values": [
            {"key": "key1", "value": "value1"},
            {"key": "key2", "value": "value2"},
        ]
    }
    expected_result = {"key1": "value1", "key2": "value2"}

    parsed_dict = api._WarsawAPI__parse_dict(response)

    assert parsed_dict == expected_result


def test_download_bus_stops(api):

    with Mocker() as m:
        url = "https://api.um.warszawa.pl/api/action/dbstore_get/"
        response_data = [
            {
                "values": [
                    {"key": "zespol", "value": "123"},
                    {"key": "slupek", "value": "4"},
                    {"key": "szer_geo", "value": 123.456},
                    {"key": "dlug_geo", "value": 123.456},
                ]
            }
        ]
        m.get(url, json={"result": response_data})

        open_mock = mock.mock_open()
        with mock.patch("builtins.open", open_mock, create=True):
            api.download_bus_stops()

        path = os.path.join(os.getcwd(), "bus_stops", "bus_stops.json")
        excepted_data = '{"123_4": {"zespol": "123", "slupek": "4", "szer_geo": 123.456, "dlug_geo": 123.456}}'
        open_mock.assert_called_with(path, "w")
        result = open_mock.return_value.write.call_count
        result_data = open_mock.return_value.write.call_args_list
        result_data = [str(data[0][0]) for data in result_data]
        result_data = "".join(result_data)
        assert result_data == excepted_data
        assert result == 21


def test_download_routes(api):

    with Mocker() as m:
        url = "https://api.um.warszawa.pl/api/action/public_transport_routes/"
        response_data = {
            "1": {
                "TD-3BAN": {
                    "1": {
                        "ulica_id": "2513",
                        "nr_zespolu": "R-03",
                        "nr_przystanku": "00",
                        "typ": "6",
                        "odleglosc": 0,
                    },
                    "2": {
                        "ulica_id": "1205",
                        "nr_zespolu": "3240",
                        "nr_przystanku": "04",
                        "typ": "5",
                        "odleglosc": 245,
                    },
                }
            }
        }
        m.get(url, json={"result": response_data})

        open_mock = mock.mock_open()
        with mock.patch("builtins.open", open_mock, create=True):
            api.download_routes()
        path = os.path.join(os.getcwd(), "bus_stops", "routes.json")
        excepted_data = ('{"1": {"TD-3BAN": {"1": {"ulica_id": "2513", "nr_zespolu": "R-03", "nr_przystanku": "00", '
                         '"typ": "6", "odleglosc": 0}, "2": {"ulica_id": "1205", "nr_zespolu": "3240", '
                         '"nr_przystanku": "04", "typ": "5", "odleglosc": 245}}}}')
        open_mock.assert_called_with(path, "w")
        result = open_mock.return_value.write.call_count
        result_data = open_mock.return_value.write.call_args_list
        result_data = [str(data[0][0]) for data in result_data]
        result_data = "".join(result_data)
        assert result_data == excepted_data
        assert result == 57
