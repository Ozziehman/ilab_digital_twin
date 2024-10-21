import osmnx as ox
import geopandas as gpd
import folium
import time
import srtm
from folium.plugins import HeatMap
import os 
import numpy as np

if not os.path.exists('shpFiles'):
    os.makedirs('shpFiles')

if not os.path.exists('geoJsonFiles'):
    os.makedirs('geoJsonFiles')

if not os.path.exists('static'):
    os.makedirs('static')

if not os.path.exists('static/maps'):
    os.makedirs('static/maps')

class MapStyler:
    """
    Class containing the styles for the map elements
    """
    @staticmethod
    def style_roads(x):
        return {'color': 'blue', 'weight': 2}

    @staticmethod
    def style_waterways(x):
        return {'fillColor': 'purple', 'color': 'purple', 'weight': 3}

    @staticmethod
    def style_buildings(x):
        return {'color': 'orange', 'weight': 2}

    @staticmethod
    def style_nearby_buildings_water(x):
        return {'color': 'purple', 'weight': 2}

    @staticmethod   
    def style_nearby_buildings_road(x):
        return {'color': 'red', 'weight': 2}

    @staticmethod
    def style_buffer_area_water(x):
        return {'fillColor': 'magenta','color': 'maroon','weight': 1,'fillOpacity': 0.2}

    @staticmethod
    def style_buffer_area_road(x):
        return {'fillColor': 'red','color': 'purple','weight': 1,'fillOpacity': 0.2}

class DataDownloader:
    """
    Downloads data from OpenStreetMap

    Parameters:
    latitude: float, latitude of the location
    longitude: float, longitude of the location
    dist: int, distance in meters to load the infrastructure data
    max_retries: int, max number of retries to download the data
    sleep_time: int, time in seconds to sleep between retries
    """
    def __init__(self, latitude, longitude, dist=1000, max_retries=5, sleep_time=5):
        
        self.point = (latitude, longitude)
        self.dist = dist
        self.max_retries = max_retries
        self.sleep_time = sleep_time
    
    def download_with_retry(self, tags):
        """
        reattemps, because sometimes server fails, the point, dist and other settings are made when making the object

        Parameters:
        tags: dict, tags to filter the data
        """
        for attempt in range(self.max_retries):
            try:
                return ox.features_from_point(self.point, tags=tags, dist=self.dist)
            except:
                print(f"Timeout on attempt {attempt + 1}. retrying in {self.sleep_time} seconds...")
                time.sleep(self.sleep_time)  # retry after a while again
        raise Exception("Failed to download")
    
class JavaScriptInjector:
    """
    Class that handles all the javascript injecting into the HTML
    """
    def inject_interactive_marker(self, map_file):
        """
        Injects live update js into the html.
        This will add a marker on the map when clicked on a location

        Parameters:
        map_file: str, path to the map file
        """
        with open(map_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        self.interactive_marker = """
<script>
    var mapDiv = document.querySelector('.folium-map');
    var mapDivId = mapDiv.id;
    var mapObject = window[mapDivId];
    
    mapObject.on('click', function(e) {
        var lat = e.latlng.lat;
        var lng = e.latlng.lng;
        var marker = L.marker([lat, lng]).addTo(mapObject);
        marker.bindPopup("Lat: " + lat.toFixed(6) + ", Lon: " + lng.toFixed(6)).openPopup();

        // Listen for the popupclose event to remove the marker
        marker.on('popupclose', function() {
            mapObject.removeLayer(marker);
        });
    });
</script>
        """
        # inject marker js into correct spot
        self.modified_html_interactive_marker = html_content.replace("</html>", self.interactive_marker + "\n</html>") #modify the html by 

        # save modified html back
        with open(map_file, 'w', encoding='utf-8') as f:
            f.write(self.modified_html_interactive_marker)
        
        print(f"interactive marker js injected and map saved back as {map_file}")

    def inject_camera_simulation_script(self, map_file, camera_latitude, camera_longitude, direction, width, reach, camera_name, video_source, cone_outline_color = 'red', cone_fill_color = 'orange', camera_outline_color = 'blue', camera_fill_color = 'lightblue'):
        """
        Inject script to show camera 'simulation', If pointing upwards angle1 would be the left bound and angle2 the right side.
        The cone shape is made by creating a polygon with a lot of points, the more points the smoother the shape.

        Parameters:
        map_file: str, path to the map file
        camera_latitude: float, latitude of the camera
        camera_longitude: float, longitude of the camera
        direction: int, direction the camera is pointing in degrees
        width: int, width of the camera view in degrees
        reach: int, reach of the camera in meters
        camera_name: str, name of the camera
        video_source: str, source of the video to show in the popup
        cone_outline_color: str, color of the outline of the cone
        cone_fill_color: str, color of the fill of the cone
        camera_outline_color: str, color of the outline of the camera
        camera_fill_color: str, color of the fill of the camera
        """
        
        with open(map_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        # replace spaces with underscores in camera name
        camera_name = camera_name.replace(' ', '_')

        self.camera_simulation_script = """
<script src="https://cdnjs.cloudflare.com/ajax/libs/Leaflet.EasyButton/2.4.0/easy-button.min.js"></script>
<script>
    var mapDiv = document.querySelector('.folium-map');
    var mapDivId = mapDiv.id;
    var mapObject = window[mapDivId];
    var circle_radius = 5;
    var guide_circle_radius = {{ reach }};
    var lat = {{ latitude }};
    var lon = {{ longitude }};

    // small circle at camrea location
    var circle_{{ camera_name }} = L.circle([lat, lon], {
        color: '{{ camera_outline_color }}',
        fillColor: '{{ camera_fill_color }}',
        fillOpacity: 0.5,
        radius: circle_radius // meters radius
    }).addTo(mapObject);

    // outer angles absed on direction and width
    var direction = {{ direction }}; // degrees
    var width = {{ width }}; // degrees
    var angle1 = direction - width / 2;
    var angle2 = direction + width / 2;

    // get points for cone shape
    var latlongpairs = [[lat, lon]];
    var numPoints = 100; // Number of points to create the arc
    var latFactor = guide_circle_radius / 111320; // convert meters to degrees latitude
    var lonFactor = guide_circle_radius / (111320 * Math.cos(lat * Math.PI / 180)); // convert meters to degrees longitude, needs to be corrected
    for (var i = 0; i <= numPoints; i++) {
        var angle = angle1 + (i * (angle2 - angle1) / numPoints);
        latlongpairs.push([
            lat + latFactor * Math.cos(angle * Math.PI / 180),
            lon + lonFactor * Math.sin(angle * Math.PI / 180)
        ]);
    }
    latlongpairs.push([lat, lon]); // Close the polygon

    // make cone shape
    var cone_{{ camera_name }} = L.polygon(latlongpairs, {
        color: '{{ cone_outline_color }}',
        fillColor: '{{ cone_fill_color }}',
        fillOpacity: 0.5
    }).addTo(mapObject);

    // bind popup with video
    cone_{{ camera_name }}.bindPopup('<iframe width="288" height="163" src="{{ video_source }}" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>');

    var popup_active_{{ camera_name }} = false
    // show popup on clicky
    cone_{{ camera_name }}.on('mouseup', function (e) {{
        if (popup_active_{{ camera_name }} == false){this.openPopup();}
    }});
    cone_{{ camera_name }}.on('mouseup', function (e) {{
        if (popup_active_{{ camera_name }} == true){this.closePopup();}
    }});

    var cameraLayer_{{ camera_name }} = [circle_{{ camera_name }}, cone_{{ camera_name }}];
    var cameraButton_{{ camera_name }} = L.easyButton({
        states: [{
            stateName: 'show-camera',
            icon: 'fa-video-camera',
            title: 'Show camera: {{ camera_name }}',
            onClick: function(btn, map) {
                cameraLayer_{{ camera_name }}.forEach(function(layer) {
                    map.removeLayer(layer);
                });
                btn.state('hide-camera');
            }
        }, {
            stateName: 'hide-camera',
            icon: 'fa-eye-slash',
            title: 'Hide camera: {{ camera_name }}',
            onClick: function(btn, map) {
                cameraLayer_{{ camera_name }}.forEach(function(layer) {
                    map.addLayer(layer);
                });
                btn.state('show-camera');
            }
        }]
    }).addTo(mapObject);
</script>
    """

        self.camera_simulation_script = self.camera_simulation_script.replace("{{ latitude }}", str(camera_latitude))
        self.camera_simulation_script = self.camera_simulation_script.replace("{{ longitude }}", str(camera_longitude))
        self.camera_simulation_script = self.camera_simulation_script.replace("{{ direction }}", str(direction))
        self.camera_simulation_script = self.camera_simulation_script.replace("{{ width }}", str(width))
        self.camera_simulation_script = self.camera_simulation_script.replace("{{ reach }}", str(reach))
        self.camera_simulation_script = self.camera_simulation_script.replace("{{ camera_outline_color }}", str(camera_outline_color))
        self.camera_simulation_script = self.camera_simulation_script.replace("{{ camera_fill_color }}", str(camera_fill_color))
        self.camera_simulation_script = self.camera_simulation_script.replace("{{ cone_outline_color }}", str(cone_outline_color))
        self.camera_simulation_script = self.camera_simulation_script.replace("{{ cone_fill_color }}", str(cone_fill_color))
        self.camera_simulation_script = self.camera_simulation_script.replace("{{ camera_name }}", str(camera_name))
        self.camera_simulation_script = self.camera_simulation_script.replace("{{ video_source }}", str(video_source))
        self.modified_html_camera = html_content.replace("</html>", self.camera_simulation_script + "\n</html>")

        # save modified html back
        with open(map_file, 'w', encoding='utf-8') as f:
            f.write(self.modified_html_camera)

        print(f"camrea simulation ({camera_name}) injected and map saved back as {map_file}\nwith paramaters:\nlat: {camera_latitude} \nlon: {camera_longitude} \ndirection: {direction} \nwidth: {width} \nreach: {reach} meters")
        
    def inject_weather_report_script(self, map_file, latitude, longitude, api_key_openweathermap):
        """
        Injects weather report js into the html
        This will show a draggable window with weather report and a slider to change the hour

        This will also create a cloud coverage layer that will overlay the map with the cloud coverage

        Parameters:
        map_file: str, path to the map file
        latitude: float, latitude of the location
        longitude: float, longitude of the location
        api_key_openweathermap: str, api key for openweathermap
        """
        # use open-meteo to get weather report
        with open(map_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        self.weather_report_script = """
<style>
    .draggable-window {
        position: absolute;
        top: 50px;
        left: 50px;
        width: 300px;
        height: auto;
        background-color: white;
        border: 1px solid #4b637f;
        padding: 10px;
        z-index: 1000;
        cursor: move;
        border-radius: 5px;
    }
    .draggable-window-header {
        background-color: #2271b3;
        border-radius: 5px 5px 0 0;
        padding: 10px;
        cursor: move;
        z-index: 1001;
    }
    .slider-container {
        margin-top: 10px;
    }
    .slider {
        width: 100%;
    }
</style>
<div id="draggable-window" class="draggable-window" style="top: 95%; left: 0.5%;">
    <div style="font-weight: bold; text-align: center; color: white" class="draggable-window-header">Weather report</div>
    <div class="draggable-window-content">
        <div id="weatherReport">
            <p>Loading weather data...</p>
        </div>
        <div class="slider-container">
            <input type="range" min="0" max="23" value="0" class="slider" id="hourSlider">
            <p>Hour: <span id="hourValue">0</span></p>
        </div>
    </div>
</div>
<script>
    let weatherData = null;

    async function fetchWeatherReport() {
        const now = new Date();
        const comingDay = new Date(now.getTime() + 24 * 60 * 60 * 1000); // time is given in Unix, hence i do the maths to add up a day in milliseconds
        const currentHourStr = now.toISOString().split('T')[0]; // start time, the API call will get the current time UNTIL the comingDay time, hard to find fitting variable name for the next 24 hours
        const comingDayStr = comingDay.toISOString().split('T')[0];
        
        const apiUrl = `https://api.open-meteo.com/v1/forecast?latitude={{ latitude }}&longitude={{ longitude }}&hourly=temperature_80m,precipitation,precipitation_probability,wind_direction_10m,visibility,weather_code&start_date=${currentHourStr}&end_date=${comingDayStr}&timezone=UTC`;

        const response = await fetch(apiUrl);
        weatherData = await response.json();
        displayWeatherReport(0); // hour index 0 means it will show the current hour first
    }

    function displayWeatherReport(hourIndex) {
        const weatherReportDiv = document.getElementById('weatherReport');
        const hourly = weatherData.hourly;
        // console.log(hourly);

        // calculate actual time for the given hour index
        const now = new Date();
        const reportTime = new Date(now.getTime() + hourIndex * 60 * 60 * 1000); //the data given is essentially only each hour but to make it more understandable it will show exact hours from the moment of refresh
        const reportTimeStr = reportTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        // html with report in it:
        const reportHtml = `
            <h2 style="font-weight: bold; text-align: center;">Weather report for ${reportTimeStr}</h2>
            <p>Temperature: ${hourly.temperature_80m[hourIndex]} Celcius</p>
            <p>Rain: ${hourly.precipitation[hourIndex]} mm</p>
            <p>Rain probability: ${hourly.precipitation_probability[hourIndex]}%</p>
            <p>Wind direction: ${hourly.wind_direction_10m[hourIndex]} degrees</p>
            <p>Visibility: ${hourly.visibility[hourIndex]} meters</p>
        `;
        // replace loading text with contents
        weatherReportDiv.innerHTML = reportHtml;

        // update the slider and hour display
        document.getElementById('hourSlider').value = hourIndex;
        document.getElementById('hourValue').innerText = hourIndex;
    }

    
    // to make the window draggable, script that follow mouse cursor when held down
    dragElement(document.getElementById("draggable-window"));

    function dragElement(elmnt) {
        var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        if (document.getElementsByClassName("draggable-window-header")[0]) {
            document.getElementsByClassName("draggable-window-header")[0].onmousedown = dragMouseDown;
        } else {
            elmnt.onmousedown = dragMouseDown;
        }

        function dragMouseDown(e) {
            e = e || window.event;
            e.preventDefault();
            pos3 = e.clientX;
            pos4 = e.clientY;
            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
        }

        function elementDrag(e) {
            e = e || window.event;
            e.preventDefault();
            pos1 = pos3 - e.clientX;
            pos2 = pos4 - e.clientY;
            pos3 = e.clientX;
            pos4 = e.clientY;
            elmnt.style.top = (elmnt.offsetTop - pos2) + "px";
            elmnt.style.left = (elmnt.offsetLeft - pos1) + "px";
        }

        function closeDragElement() {
            document.onmouseup = null;
            document.onmousemove = null;
        }
    }

    fetchWeatherReport(); // first initial fetch, would be a shame if there's no data at first
    
    // if hour sliders moves update the displayed weather report WITHOUT asking for another API call
    document.getElementById('hourSlider').addEventListener('input', function() {
        const hourIndex = parseInt(this.value);
        displayWeatherReport(hourIndex);
    });

    // get and display weather data
    setInterval(fetchWeatherReport, 60000); // refresh every minute
</script>
<script>
    var cloudCoverageLayer = L.featureGroup();
    cloudCoverageLayer.addTo(mapObject); 
    L.control.layers(null, { 'Cloud Coverage': cloudCoverageLayer }).addTo(mapObject);

    let currentCloudCoverageOverlay = null;
    
    async function fetchCloudCoverageImage() {
        const now = new Date();
        const reportTimeEpoch = Math.floor(now.getTime() / 1000); // convert to UNIX time

        // get zoom of map
        const zoomLevel = mapObject.getZoom();
        const latitude = {{ latitude }};
        const longitude = {{ longitude }};

        // convert to tile coords used by openweathermap
        const tileSize = 256; // Size of the tile
        const x = Math.floor((longitude + 180) / 360 * Math.pow(2, zoomLevel));
        const y = Math.floor((1 - (Math.log(Math.tan(latitude * Math.PI / 180) + 1 / Math.cos(latitude * Math.PI / 180)) / Math.PI)) / 2 * Math.pow(2, zoomLevel));

        // api url with params
        const apiUrl = `https://tile.openweathermap.org/map/clouds_new/${zoomLevel}/${x}/${y}.png?appid={{ API_KEY_OPENWEATHERMAP }}&forecast=${reportTimeEpoch}`;
        console.log(apiUrl);
        
        // remove previous laye if exists
        if (currentCloudCoverageOverlay) {
            cloudCoverageLayer.removeLayer(currentCloudCoverageOverlay);
        }

        // overlay image over the map
        currentCloudCoverageOverlay = L.imageOverlay(apiUrl, mapObject.getBounds());
        currentCloudCoverageOverlay.addTo(cloudCoverageLayer);
    }

    fetchCloudCoverageImage(); // initial fetch
    setInterval(fetchCloudCoverageImage, 60000); // refresh every minute
</script>
    """
        self.weather_report_script = self.weather_report_script.replace("{{ latitude }}", str(latitude))
        self.weather_report_script = self.weather_report_script.replace("{{ longitude }}", str(longitude))
        self.weather_report_script = self.weather_report_script.replace("{{ API_KEY_OPENWEATHERMAP }}", str(api_key_openweathermap))

        # inject weather report into correct spot
        self.modified_html_weather_report = html_content.replace("</html>", self.weather_report_script + "\n</html>") #modify the html by 

        # save modified html back
        with open(map_file, 'w', encoding='utf-8') as f:
            f.write(self.modified_html_weather_report)
        
        print(f"weather report js injected and map saved back as {map_file}")

    def inject_passage_simulation_script(self, map_file, point, simulation_speed=500):
        """Simulates passages past a point. The point should be a tuple with lat, lon.
        The simulation speed is the speed of the simulation in milliseconds per random addition of a point.
        
        Parameters:
        map_file: str, path to the map file
        point: tuple, a tuple with lat, lon
        simulation_speed: int, speed of the simulation in milliseconds per random addition of a point
        """

        with open(map_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        self.passage_simulation_script = """
<script>
    var mapDiv = document.querySelector('.folium-map');
    var mapDivId = mapDiv.id;
    var mapObject = window[mapDivId];

    // if simulationPointsDict is not defined, make it
    if (typeof simulationPointsDict === 'undefined') {
        simulationPointsDict = {};
    }
    if (typeof passageLayer === 'undefined') {
        passageLayer = L.featureGroup().addTo(mapObject);
        L.control.layers(null, { 'Passage Layer': passageLayer }).addTo(mapObject);
    }

    // the speed is the amount of milliseconds between each random addition of a point, so the lower this number the faster the simulation
    var simulationSpeed = {{ simulation_speed }};
    var point = {{ point }};
    var key = point[0] + ', ' + point[1];
    if (!simulationPointsDict[key]) {
        simulationPointsDict[key] = 0; // start with 0 passages
    }

    // gives a nice color hue depending on the value
    function getColorHue(value) {
        var maxValue = 1800; // value at which it's fully red
        value = Math.min(Math.max(value, 0), maxValue); 
        var hue = (1 - value / maxValue) * 120;
        return `hsl(${hue}, 100%, 50%)`;
    }

    // gives a radius that grows with the value
    function getRadius(value) {
        var normalizedValue = Math.min(value, 1440);
        return 2 * Math.sqrt(normalizedValue);
    }

    // update the visuals of the simulation 
    function updateVisuals() {
        passageLayer.clearLayers();  // clear existing to update again
        for (var key in simulationPointsDict) {
            var coords = key.split(', ').map(Number);
            var value = simulationPointsDict[key];
            var radius = getRadius(value);  // radius based on value
            var color = getColorHue(value);  // color based on value

            var circleName = 'circle_' + key.replace(', ', '_');
            var circle = L.circle(coords, {
                radius: radius,
                color: color,
                fillColor: color,
                fillOpacity: 0.5
            }).addTo(passageLayer);

            circle.bindTooltip(`Passages: ${value}, Coordinates: ${coords}`, {
                permanent: false,
                direction: 'top'
            });
        }
    }

    // In an actual product this should be fetched from a server thats connected to sensors
    function addValueToRandomPoint() {
        var keyList = Object.keys(simulationPointsDict);
        var randomIndex = Math.floor(Math.random() * keyList.length);
        var randomPoint = keyList[randomIndex];

        simulationPointsDict[randomPoint] += Math.floor(Math.random() * 10) + 1;
        updateVisuals();
    }

    setInterval(addValueToRandomPoint, simulationSpeed);
    setInterval(function() {
        console.log(simulationPointsDict);
    }, 5000); // log every 5 seconds
</script>
        """
        formatted_point = str(point).replace("(", "[").replace(")", "]")
        self.passage_simulation_script = self.passage_simulation_script.replace("{{ point }}", formatted_point)
        self.passage_simulation_script = self.passage_simulation_script.replace("{{ simulation_speed }}", str(simulation_speed))

        self.modified_html_passage_simulation = html_content.replace("</html>", self.passage_simulation_script + "\n</html>") #modify the html by

        # save modified html back
        with open(map_file, 'w', encoding='utf-8') as f:
            f.write(self.modified_html_passage_simulation)

        print(f"Passage simulation js injected and map saved back as {map_file}")
    
class MapCreator:
    """This class combines all elements into one so a map can be generated by using the create_detailed_map function
    Parameters:
    latitude: float, latitude of the location
    longitude: float, longitude of the location
    name: str, name of the location
    load_dist: int, distance in meters to load the infrastructure data
    water_buffer_size: int, size of the buffer around waterways
    road_buffer_size: int, size of the buffer around roads
    """
    def __init__(self, latitude, longitude, name, load_dist=2000, water_buffer_size = 150, road_buffer_size=20, cameras=[], passage_points=[]):
        self.latitude = latitude
        self.longitude = longitude
        self.point = (latitude, longitude)
        self.name = name
        self.load_dist = load_dist
        self.water_buffer_size = water_buffer_size
        self.road_buffer_size = road_buffer_size
        self.dataDownloader = DataDownloader(self.latitude, self.longitude, dist=self.load_dist)
        self.mapStyler = MapStyler()
        self.m = folium.Map(location=[self.latitude, self.longitude], zoom_start=8)
        self.javaScriptInjector = JavaScriptInjector()
        self.map_name = f'static/maps/map_{self.name}.html'
        self.cameras = cameras
        self.passage_points = passage_points

        # Base map is added automatically

        # Netherlands specific maps
        folium.TileLayer(
            tiles='https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/grijs/EPSG:3857/{z}/{x}/{y}.png',
            attr='PDOK',
            name='Nederland Grijs',
            overlay=False,
            control=True
        ).add_to(self.m)

        folium.TileLayer(
            tiles='https://service.pdok.nl/brt/achtergrondkaart/wmts/v2_0/pastel/EPSG:3857/{z}/{x}/{y}.png',
            attr='PDOK',
            name='Nederland Pastel',
            overlay=False,
            control=True
        ).add_to(self.m)

        # Base map (English names)
        folium.TileLayer(
            tiles='https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
            attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors & CartoDB',
            name='CartoDB Voyager',
            overlay=False
        ).add_to(self.m)

        # Dark map
        folium.TileLayer(
            tiles='cartodbdark_matter',
            name='CartoDB Dark Matter',
            attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors & CartoDB',
            overlay=False,
            control=True           
        ).add_to(self.m)
        
    def download_road_network_data(self):
        """
        Downloads road network data and saves it as shapefiles and geojson
        """
        print("Downloading road network..")
        G = ox.graph_from_point(self.point, dist=self.load_dist, network_type='all')

        print("Converting road network to GeoDataFrame, getting the roads all prepared")
        self.gdf_roads = ox.graph_to_gdfs(G, nodes=False)
        if 'nodes' in self.gdf_roads.columns:
            self.gdf_roads = self.gdf_roads.drop(columns=['nodes'])
        print("Saving shapefiles...")
        self.gdf_roads.to_file(f'shpFiles/roads_{self.name}.shp', driver='ESRI Shapefile')
        self.gdf_roads.to_file(f'geoJsonFiles/roads_{self.name}.geojson', driver='GeoJSON')

    def download_building_data(self):
        """
        Downloads building data and saves it as shapefiles and geojson
        """
        print("Downloading buildings..")
        self.buildings = self.dataDownloader.download_with_retry(tags={'building': True})
        self.buildings = self.buildings[self.buildings.geometry.type == 'Polygon']
        self.buildings.to_file(f'shpFiles/buildings_{self.name}.shp', driver='ESRI Shapefile')
        self.buildings.to_file(f'geoJsonFiles/buildings_{self.name}.geojson', driver='GeoJSON')

    def download_waterway_data(self):
        """
        Downloads waterway data and saves it as shapefiles and geojson
        """
        print("Downloading waterways..")
        self.waterways = self.dataDownloader.download_with_retry(tags={'waterway': True})
        self.waterways = self.waterways[self.waterways.geometry.type == 'LineString']
        self.waterways.to_file(f'shpFiles/waterways_{self.name}.shp', driver='ESRI Shapefile')
        self.waterways.to_file(f'geoJsonFiles/waterways_{self.name}.geojson', driver='GeoJSON') 
    
    def add_buildings_tooltips(self, buildings, buildings_fg, styler, extra_data=None):
        """
        Adds tooltips to the buildings, only data that is not null or nan will be shown in the tooltip

        Parameters:
        buildings: GeoDataFrame, buildings data
        buildings_fg: folium.FeatureGroup, folium FeatureGroup to add the buildings to
        styler: function, function to style the buildings
        extra_data: dict, extra data to show in the tooltip
        """
        for _, building in buildings.iterrows():
            geometry = building.geometry
            properties = building.drop('geometry').to_dict() # gets properties

            tooltip_content = "<br>".join([f"{key}: {value}" for key, value in properties.items() if value is not None and value is not np.nan]) #lists all data not None in popup/tooltip
            if extra_data is not None:
                tooltip_content += "<br>" + "<br>".join([f"{key}: {value}" for key, value in extra_data.items() if value is not None and value is not np.nan])
            tooltip = folium.Tooltip(tooltip_content)

            folium.GeoJson(
                geometry,
                style_function=styler,
                tooltip=tooltip
            ).add_to(buildings_fg) # adds the tooltip to the GeoJson that is save under this
        
        return buildings_fg
    
    def render_altitude_heatmap(self):
        """Renders altitude heatmap of the area with the use of SRTM data, 
        heatmap will be drawn only to the edges of the loaded infrastructure"""
        self.elevation_data = srtm.get_data()
        # set bound to the outer part of the loaded infrastructure
        self.lat_min = min(self.buildings.geometry.bounds.miny.min(), self.roads.geometry.bounds.miny.min())
        self.lat_max = max(self.buildings.geometry.bounds.maxy.max(), self.roads.geometry.bounds.maxy.max())
        self.lon_min = min(self.buildings.geometry.bounds.minx.min(), self.roads.geometry.bounds.minx.min())
        self.lon_max = max(self.buildings.geometry.bounds.maxx.max(), self.roads.geometry.bounds.maxx.max())

        self.heatmap_data = []
        for lat in np.arange(self.lat_min, self.lat_max, 0.00005):
            for lon in np.arange(self.lon_min, self.lon_max, 0.00005):
                altitude = self.elevation_data.get_elevation(lat, lon)
                if altitude is not None:
                    self.heatmap_data.append([lat, lon, altitude])

        gradient = {0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'}
        self.heatmap = HeatMap(self.heatmap_data, min_opacity=0.05, radius=15, blur=20, max_zoom=1, gradient=gradient)
        
        self.elevation_heatmap = folium.FeatureGroup(name="Elevation heatmap")
        self.heatmap.add_to(self.elevation_heatmap)
        self.elevation_heatmap.add_to(self.m)

        # convert heatmap to geodataframe to save as geojson, this is not needed but can be useful in the future, WARNING: LARGE FILE, LONG PROCESSING TIME
        # print("Creating heatmap gdf")
        # self.elevation_heatmap_geometry = [Point(lon, lat) for lat, lon, intensity in self.heatmap_data]
        # self.gdf_elevation_heatmap = gpd.GeoDataFrame(self.heatmap_data, geometry=self.elevation_heatmap_geometry, columns=['Latitude', 'Longitude', 'Intensity'])
        # self.gdf_elevation_heatmap.to_file(f'geoJsonFiles/elevation_heatmap_{self.name}.geojson', driver='GeoJSON')
        # print(f"Heatmap creaated and also saved as GeoJSON as geoJsonFiles/elevation_heatmap_{self.name}.geojson ")

    def render_buffer_area_road(self):
        """Renders buffer area around roads and buildings nearby roads"""
        self.projected_roads = self.roads.to_crs(epsg=self.epsg_code)
        self.road_buffer = self.projected_roads.buffer(self.road_buffer_size)
        self.road_buffer = self.road_buffer.to_crs(self.roads.crs)
        self.road_buffer_union = self.road_buffer.unary_union

        self.buffer_geojson_road = gpd.GeoSeries([self.road_buffer_union]).__geo_interface__

        # create FeatureGroup for the buffer area road
        self.buffer_area_road_fg = folium.FeatureGroup(name="Buffer area road")
        folium.GeoJson(self.buffer_geojson_road, style_function=self.mapStyler.style_buffer_area_road).add_to(self.buffer_area_road_fg)
        self.buffer_area_road_fg.add_to(self.m)

        # buildings nearby roads
        self.nearby_buildings_road = self.buildings[self.buildings.intersects(self.road_buffer_union)]

        self.nearby_buildings_road_fg = folium.FeatureGroup(name="Buildings nearby roads")
        folium.GeoJson(self.nearby_buildings_road, style_function=self.mapStyler.style_nearby_buildings_road).add_to(self.nearby_buildings_road_fg)
        self.nearby_buildings_road_fg = self.add_buildings_tooltips(self.nearby_buildings_road, self.nearby_buildings_road_fg, styler=self.mapStyler.style_nearby_buildings_road, extra_data = {'Digital Twin Name': self.name, 'Building Type': 'within road buffer'})
        self.nearby_buildings_road_fg.add_to(self.m)

    def render_buffer_area_water(self):
        """Renders buffer area around waterways and buildings nearby waterways"""
        self.projected_waterways = self.waterways.to_crs(epsg=self.epsg_code)
        self.water_buffer = self.projected_waterways.buffer(self.water_buffer_size)
        self.water_buffer = self.water_buffer.to_crs(self.waterways.crs)
        self.water_buffer_union = self.water_buffer.unary_union

        self.buffer_geojson_water = gpd.GeoSeries([self.water_buffer_union]).__geo_interface__

        # create FeatureGroup for the buffer area water
        self.buffer_area_water_fg = folium.FeatureGroup(name="Buffer area waterways")
        folium.GeoJson(self.buffer_geojson_water, style_function=self.mapStyler.style_buffer_area_water).add_to(self.buffer_area_water_fg)
        self.buffer_area_water_fg.add_to(self.m)

        # buildings nearby water
        self.nearby_buildings_water = self.buildings[self.buildings.intersects(self.water_buffer_union)]

        self.nearby_buildings_water_fg = folium.FeatureGroup(name="Buildings nearby waterways")
        folium.GeoJson(self.nearby_buildings_water, style_function=self.mapStyler.style_nearby_buildings_water).add_to(self.nearby_buildings_water_fg)
        self.nearby_buildings_water_fg = self.add_buildings_tooltips(self.nearby_buildings_water, self.nearby_buildings_water_fg, styler=self.mapStyler.style_nearby_buildings_water, extra_data = {'Digital Twin Name': self.name, 'Building Type': 'within water buffer'})
        self.nearby_buildings_water_fg.add_to(self.m)

    def render_buffer_areas(self, water_buffer=True, road_buffer=True):
        """Calls buffer area functions to render buffer areas"""
        self.utm_zone = int((self.longitude + 180) // 6) + 1 # calculate UTM zone
        self.is_northern_hemisphere = self.latitude >= 0 # check if in northern hemisphere
        self.epsg_code = 32600 + self.utm_zone if self.is_northern_hemisphere else 32700 + self.utm_zone # calculate EPSG code

        if water_buffer==True:
            self.render_buffer_area_water()
        if road_buffer==True:
            self.render_buffer_area_road()

    def save_map(self, interactive_marker=True, camera_simulation=True, weather_report=True, passage_simulation=True):
        """
        Saves barebones map with static info
        
        Parameters:
        interactive_marker: bool, if True, interactive marker will be added
        camera_simulation: bool, if True, camera simulation will be added
        weather_report: bool, if True, weather report will be added
        """
        self.m.save(self.map_name)

        # these NEED to take place AFTER saving the base html with static info
        if interactive_marker == True:
            self.javaScriptInjector.inject_interactive_marker(self.map_name)
        if camera_simulation == True:
            # Adds camera simulation scripts
            for camera in self.cameras:
                self.javaScriptInjector.inject_camera_simulation_script(
                    self.map_name,
                    camera_latitude=camera['latitude'],
                    camera_longitude=camera['longitude'],
                    direction=camera['direction'],
                    width=camera['width'],
                    reach=camera['reach'],
                    camera_name=camera['name'],
                    video_source=camera['video_source'],
                    cone_outline_color=camera.get('cone_outline_color', 'red'),
                    cone_fill_color=camera.get('cone_fill_color', 'orange'),
                    camera_outline_color=camera.get('camera_outline_color', 'blue'),
                    camera_fill_color=camera.get('camera_fill_color', 'lightblue')
                )
        if weather_report == True:
            # Should be changed to a more secure way of storing the API key when fully released
            self.api_key_openweathermap = "d0160058812e1e5f9b9bdfb04c5ffca9"
            self.javaScriptInjector.inject_weather_report_script(self.map_name, self.latitude, self.longitude, self.api_key_openweathermap)
        if passage_simulation == True:
            for point in self.passage_points:
                self.javaScriptInjector.inject_passage_simulation_script(self.map_name, point)
        
        return self.map_name

    def create_detailed_map(self):
        """
        Creates detailed map with all the data and saves it as a static html
        """
        #download data with downloader
        self.download_building_data()
        self.download_road_network_data()
        self.download_waterway_data()
        
        #read saved files
        self.roads = gpd.read_file(f'shpFiles/roads_{self.name}.shp') # read roads
        self.all_buildings = gpd.read_file(f'shpFiles/buildings_{self.name}.shp') # read buildings
        self.waterways = gpd.read_file(f'shpFiles/waterways_{self.name}.shp') # read waterways
        
        # add roads to a featuregroup
        self.roads_fg = folium.FeatureGroup(name='Roads') # create featuregroup
        folium.GeoJson(self.roads,style_function=self.mapStyler.style_roads).add_to(self.roads_fg) # add roads to featuregroup
        self.roads_fg.add_to(self.m) # add featuregroup to map

        # add waterways to a featuregroup
        self.waterways_fg = folium.FeatureGroup(name='Waterways') # create featuregroup
        folium.GeoJson(self.waterways,style_function=self.mapStyler.style_waterways).add_to(self.waterways_fg) # add waterways to featuregroup
        self.waterways_fg.add_to(self.m) # add featuregroup to map

        # add all buildings to featuregroup
        self.all_buildings_fg = folium.FeatureGroup(name="All buildings") # create featuregroup
        folium.GeoJson(self.all_buildings, style_function=self.mapStyler.style_buildings).add_to(self.all_buildings_fg) # add buildings to featuregroup
        self.all_buildings_fg = self.add_buildings_tooltips(self.all_buildings, self.all_buildings_fg, styler=self.mapStyler.style_buildings, extra_data = {'Digital Twin Name': self.name, 'Building Type': 'general'}) # add tooltips to buildings
        self.all_buildings_fg.add_to(self.m) # add featuregroup to map
        
        self.render_buffer_areas(water_buffer=True, road_buffer=True) # render buffer areas
        self.render_altitude_heatmap() #render altitude heatmap, BE CAUTIOUS, at large area options this will use a LOT of storage

        folium.LayerControl(collapsed=False, draggable=True).add_to(self.m) # add layer control to map

        self.save_map() # save map with static info
        
        saved_map_name = f'maps/map_{self.name}.html' # name of the saved map WITHIN the static folder
        print(f"Map saved under {saved_map_name} in the static folder.") # print where the map is saved

        return saved_map_name # return the name of the saved map within the static folder
    
# This is for testing it standalone without any flask app
if __name__ == "__main__":
    cameras = [
            {
                'latitude': 51.176858,
                'longitude': 5.882079,
                'direction': -60,
                'width': 94,
                'reach': 200,
                'name': 'camera 1 red',
                'video_source': 'https://www.youtube.com/embed/4qOxFyZLcl0?si=VO9YbHXW7mDSENHO',
                'cone_outline_color': 'red',
                'cone_fill_color': 'lightred',
                'camera_outline_color': 'blue',
                'camera_fill_color': 'lightblue'
            },
            {
                'latitude': 51.179512,
                'longitude': 5.878201,
                'direction': 180,
                'width': 94,
                'reach': 200,
                'name': 'camera 2 blue',
                'video_source': 'https://www.youtube.com/embed/4qOxFyZLcl0?si=VO9YbHXW7mDSENHO',
                'cone_outline_color': 'blue',
                'cone_fill_color': 'lightblue',
                'camera_outline_color': 'red',
                'camera_fill_color': 'lightred'
            },
            {
                'latitude': 51.184346,
                'longitude': 5.876827,
                'direction': 278,
                'width': 137,
                'reach': 800,
                'name': 'camera 3 green',
                'video_source': 'https://www.youtube.com/embed/lffpBLDQqqc?si=H6um6OemAf8UQc56',
                'cone_outline_color': 'green',
                'cone_fill_color': 'lightgreen',
                'camera_outline_color': 'purple',
                'camera_fill_color': 'lightpurple'
            },
            {
                'latitude': 51.109750,
                'longitude': 5.819703,
                'direction': 180,
                'width': 120,
                'reach': 300,
                'name': 'camera 3 green',
                'video_source': 'https://www.youtube.com/embed/lffpBLDQqqc?si=H6um6OemAf8UQc56',
                'cone_outline_color': 'green',
                'cone_fill_color': 'lightgreen',
                'camera_outline_color': 'purple',
                'camera_fill_color': 'lightpurple'
            },
            {
                'latitude': 51.109534,
                'longitude': 5.828372,
                'direction': 90,
                'width': 94,
                'reach': 600,
                'name': 'camera 2 blue',
                'video_source': 'https://www.youtube.com/embed/4qOxFyZLcl0?si=VO9YbHXW7mDSENHO',
                'cone_outline_color': 'blue',
                'cone_fill_color': 'lightblue',
                'camera_outline_color': 'red',
                'camera_fill_color': 'lightred'
            }
        ]

    # Define passage points
    passage_points = [
        (51.184965, 5.884337),
        (51.179639, 5.894701),
        (51.175684, 5.876698),
        (51.178336, 5.872226),
        (51.180796, 5.883265),
        (51.110852, 5.829212),
        (51.111270, 5.818420),
        (51.110960, 5.828311),
        (51.111741, 5.818032),
        (51.116604, 5.823438),
        (51.115297, 5.829746)
    ]

    map_creator_1 = MapCreator(51.1797305,5.8812762,"Boschmolenplas", 1500, 150, 20, cameras, passage_points)
    map_creator_1.create_detailed_map()