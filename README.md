# ilab_digital_twin

This project is made in collaboration with the Innovation Lab (iLab) of the police in Heerlen(Limburg, Netherlands).
The goal of this project was to develop a Digital Twin to as much detail as possible with openly available data of the places:
- [Maasterp Ohé en Laak](https://www.google.nl/maps/@51.1111538,5.8207123,15.25z?entry=ttu&g_ep=EgoyMDI0MTAwNy4xIKXMDSoASAFQAw%3D%3D)
- [Boschmolenplas](https://www.google.nl/maps/@51.1821348,5.8789938,15.25z?entry=ttu&g_ep=EgoyMDI0MTAwNy4xIKXMDSoASAFQAw%3D%3D)

The application works for both of these location and essentially every other on-land location in the world, but certain simulation
elements are hardcoded to take place in either of those two named locations.

## Core Features
### Map Layers
- **Road Networks:** Downloads and displays road networks from OpenStreetMap.
- **Buildings:** Downloads and displays building data from OpenStreetMap.
- **Waterways:** Downloads and displays waterway data from OpenStreetMap.
- **Buffer Areas:** Renders buffer areas around roads and waterways.
- **Altitude Heatmap:** Renders an altitude heatmap using SRTM data.
- **Interactive Marker:** Adds an interactive marker to the map.
- **Camera Simulation:** Simulates camera views with configurable parameters.
- **Weather Report:** Displays a weather report with a draggable window and cloud coverage overlay.
- **Several different map styles:** The user can switch between several styles including some that only display the Netherlands
    - Standard OSM map
    - Dark mode (CartoDB)
    - Netherlands Grey (PDOK), very useful for visualizing cloud coverage
    - Netherlands Pastel (PDOK)
    - English location names (CartoDB)

All layers can be switched on and off from the top right of the generated HTML page.

## Installation

1. **Clone the repository:**
    ```sh
    git clone https://github.com/Research-Center-Data-Intelligence/ilab_digital_twin
    cd <repository-directory>
    ```

2. **Install the required packages:**
    ```sh
    pip install -r requirements.txt
    ```

## Usage

### Creating a Map

To create a detailed map, instantiate the `MapCreator` class with the wanted parameters and call the `create_detailed_map` function.

```python
from mapGenerator import MapCreator

# Example usage
map_creator = MapCreator(latitude=51.1797305, longitude=5.8812762, name="Boschmolenplas", load_dist=1500, water_buffer_size=150, road_buffer_size=20)
map_creator.create_detailed_map()
```
### Parameters
- `latitude`: Latitude of the location.
- `longitude`: Longitude of the location.
- `name`: Name of the location.
- `load_dist`: Distance in meters to load the infrastructure data.
- `water_buffer_size`: Size of the buffer around waterways.
- `road_buffer_size`: Size of the buffer around roads.

### Generated Map
The generated map will be exported and saved as an HTML file in the `static/maps` folder with a variation of the `name map_<location_name>.html`.

## Classes and methods

### Mapcreator
This class is the location where everything happens, this class uses the other classes to combine into a HTML digital twin.

#### Methods
- `__init__(self, latitude, longitude, name, load_dist=2000, water_buffer_size=150, road_buffer_size=20, cameras=[])` Initializes the MapCreator instance with the specified parameters.
    - ##### Parameters
        - `latitude`: Latitude of the location.
        - `longitude`: Longitude of the location.
        - `name`: Name of the location.
        - `load_dist`: Distance in meters to load the infrastructure data.
        - `water_buffer_size`: Size of the buffer around waterways.
        - `road_buffer_size`: Size of the buffer around roads.
        - `cameras`: List of to be simulated cameras with their properties.

- `create_detailed_map(self)` Creates a detailed map with all the data and saves it as a static HTML file.
- `download_road_network_data(self)` Downloads road network data and saves it as shapefiles and GeoJSON.
- `download_building_data(self)` Downloads building data and saves it as shapefiles and GeoJSON.
- `download_waterway_data(self)` Downloads waterway data and saves it as shapefiles and GeoJSON.
- `add_buildings_tooltips(self, buildings, buildings_fg, styler, extra_data=None)` Adds tooltips to the buildings.
    - ##### Parameters
        - `buildings`: GeoDataFrame containing buildings data.
        - `buildings_fg`: Folium FeatureGroup to add the buildings to.
        - `styler`: Function to style the buildings.
        - `extra_data`: Dictionary containing extra data to show in the tooltip.
- `render_altitude_heatmap(self)` Renders an altitude heatmap of the area using SRTM data.
- `render_buffer_area_road(self)` Renders buffer areas around roads and buildings nearby roads.
- `render_buffer_area_water(self)` Renders buffer areas around waterways and buildings nearby waterways.
- `render_buffer_areas(self, water_buffer=True, road_buffer=True)` Calls buffer area functions to render buffer areas.
    - ##### Parameters
        - `water_buffer`: Boolean indicating whether to render buffer areas around waterways.
        - `road_buffer`: Boolean indicating whether to render buffer areas around roads.
- `save_map(self, interactive_marker=True, camera_simulation=True, weather_report=True)` Saves the map with static information and injects interactive features.
    - ##### Parameters
        - `interactive_marker`: Boolean indicating whether to add an interactive marker.
        - `camera_simulation`: Boolean indicating whether to add camera simulation.
        - `weather_report`: Boolean indicating whether to add a weather report.

### MapStyler

This class contains the styles for the map elements.

#### Methods
-`style_roads(x)` Styles the roads.
-`style_waterways(x)` Styles the waterways.
-`style_buildings(x)` Styles the buildings.
-`style_nearby_buildings_water(x)` Styles the buildings near waterways.
-`style_nearby_buildings_road(x)` Styles the buildings near roads.
-`style_buffer_area_water(x)` Styles the buffer area around waterways.
-`style_buffer_area_road(x)` Styles the buffer area around roads.

### DataDownloader

This class downloads data from OpenStreetMap.

#### Methods
- `__init__(self, latitude, longitude, dist=1000, max_retries=5, sleep_time=5)` Initializes the DataDownloader instance with the specified parameters.
    - ##### Parameters
        - `latitude`: Latitude of the location.
        - `longitude`: Longitude of the location.
        - `dist`: Distance in meters to load the infrastructure data.
        - `max_retries`: Maximum number of retries to download the data.
        - `sleep_time`: Time in seconds to sleep between retries.
- `download_with_retry(self, tags)` Downloads data with retries.
    - ##### Parameters
        - `tags`: Dictionary containing tags to filter the data.

### JavaScriptInjector

This class handles all the JavaScript injecting into the HTML. Every method will read the HTML and add the Javascript to it.

#### Methods
- `inject_interactive_marker(self, map_file)` Injects live update JavaScript into the HTML to add a marker on the map when clicked.
    - ##### Parameters
        - `map_file`: Path to map file
- `inject_camera_simulation_script(self, map_file, camera_latitude, camera_longitude, direction, width, reach, camera_name, video_source, cone_outline_color='red', cone_fill_color='orange', camera_outline_color='blue', camera_fill_color='lightblue')` Injects a script to show camera simulation.
    - ##### Parameters
        - `map_file`: Path to the map file.
        - `camera_latitude`: Latitude of the camera.
        - `camera_longitude`: Longitude of the camera.
        - `direction`: Direction the camera is pointing in degrees.
        - `width`: Width of the camera view in degrees.
        - `reach`: Reach of the camera in meters.
        - `camera_name`: Name of the camera.
        - `video_source`: Source of the video to show in the popup.
        - `cone_outline_color`: Color of the outline of the cone.
        - `cone_fill_color`: Color of the fill of the cone.
        - `camera_outline_color`: Color of the outline of the camera.
        - `camera_fill_color`: Color of the fill of the camera.
    
- `inject_weather_report_script(self, map_file, latitude, longitude, api_key_openweathermap)` Injects a weather report script into the HTML.
    - ##### Parameters
        - `map_file`: Path to the map file.
        - `latitude`: Latitude of the location.
        - `longitude`: Longitude of the location.
        - `api_key_openweathermap`: API key for OpenWeatherMap.

### Directory Structure
- `shpFiles/`: Directory to store shapefiles.
- `geoJsonFiles/`: Directory to store GeoJSON files.
- `static/`: Directory to store static files.
    - `maps/`: Directory to store generated map HTML files.

### Ackknowledgements
- [Folium](https://python-visualization.github.io/folium/)
- [OpenStreetMap](https://www.openstreetmap.org/)
- [OpenWeatherMap](https://openweathermap.org/)
- [SRTM](https://www2.jpl.nasa.gov/srtm/)

# Project Group
- Shelly Andrien
- Esmée Croonen
- [Laura Moonen](https://github.com/laura-19502)
- [Oscar Theelen](https://github.com/Ozziehman)