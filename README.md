# Warsaw_buses

This is a simple project that uses the [Warsaw public transport API](https://api.um.warszawa.pl/) to downlad data about buses in Warsaw and then analyze it.

## How to use

#### Sample usage

###### Download data

```python

api_key = 'your_api_key' # get it from https://api.um.warszawa.pl/
path = os.getcwd() # path to save the data
api.download_bus_stops(path)
api.download_routes(path)
api.download_dictionary(path)
api.download_buses_location_by_time(path, download_time=60)
api.download_schedule(path)

```

###### Analyse data

```python

# punctuality
analyse_punctionality = Punctionality()
analyse_punctionality.prepare_data()
data_punctionality = analyse_punctionality.get_data()
# velocity
analyse_speed = Velocity()
analyse_speed.prepare_speed() 
data_speed = analyse_speed.get_speed_data()

```

## Documentation

### warsaw_api

- download_bus_stops(path) -> None:

    Download bus stops from Warsaw API and save to file.  
    Args:
        path (Optional[str], optional): Path to directory where file will be saved. Defaults to os.getcwd().
- download_routes(path) -> None:

    Download routes from Warsaw API and save to file.  
    Args:
        path (Optional[str], optional): Path to directory where file will be saved. Defaults to os.getcwd().
- download_dictionary(path) -> None:

    Download dictionary from Warsaw API and save to file.  
    Args:
        path (Optional[str], optional): Path to directory where file will be saved. Defaults to os.getcwd().
- download_buses_location_by_time(path, download_time=60) -> None:

    Download buses location from Warsaw API and save to file.  
    Args:
        path (Optional[str], optional): Path to directory where file will be saved. Defaults to os.getcwd().
        download_time (int, optional): Time in seconds between downloads. Defaults to 60.
- download_schedule(path) -> None:
    
    Download schedule from Warsaw API and save to file.  
    Args:
        path (Optional[str], optional): Path to directory where file will be saved. Defaults to os.getcwd().

### analyse

#### Punctionality

- prepare_data() -> None:

    Prepares the data for analysis.  
    Merges bus position data with the schedule and bus stops.

- get_data() -> pd.DataFrame:
    
    Returns: (pd.DataFrame) The prepared data.       

#### Velocity

- prepare_speed() -> None:

    Reads the data about buses location from the directory and prepares it for analysis.

- get_speed_data() -> pd.DataFrame:

    Returns: (pd.DataFrame) The prepared data.

- change_path_data(path) -> None:

    Changes the path to the data directory.


