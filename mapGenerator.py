import osmnx as ox
import geopandas as gpd
import folium
import time
import srtm
from folium.plugins import HeatMap
import os 
import numpy as np
from shapely.geometry import Point

if not os.path.exists('shpFiles'):
    os.makedirs('shpFiles')

if not os.path.exists('geoJsonFiles'):
    os.makedirs('geoJsonFiles')

if not os.path.exists('static'):
    os.makedirs('static')

if not os.path.exists('static/maps'):
    os.makedirs('static/maps')

class MapStyler:
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
    def __init__(self, latitude, longitude, dist=1000, max_retries=5, sleep_time=5):
        
        self.point = (latitude, longitude)
        self.dist = dist
        self.max_retries = max_retries
        self.sleep_time = sleep_time
    
    def download_with_retry(self, tags):
        """reattemps, because sometimes server fails, the point, dist and other settings are made when making the object"""
        for attempt in range(self.max_retries):
            try:
                return ox.features_from_point(self.point, tags=tags, dist=self.dist)
            except:
                print(f"Timeout on attempt {attempt + 1}. retrying in {self.sleep_time} seconds...")
                time.sleep(self.sleep_time)  # retry after a while again
        raise Exception("Failed to download")
    
class JavaScriptInjector:
    def inject_interactive_marker(self, map_file):
        """Injects live update js into the html"""
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
        """Inject script to show camera 'simulation', IF pointing upwards angle1 would be the left bound and angle2 the right side"""
        
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
        
        // overlay iamg over the map
        const cloudCoverageOverlay = L.imageOverlay(apiUrl, mapObject.getBounds());
        cloudCoverageOverlay.addTo(cloudCoverageLayer);
    }

    fetchCloudCoverageImage(); // initial fetch
    setInterval(fetchCloudCoverageImage(), 60000); // refresh every minute
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
    
class MapCreator:
    def __init__(self, latitude, longitude, name, load_dist=2000, water_buffer_size = 150, road_buffer_size=20):
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

    def download_road_network_data(self):
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
        print("Downloading buildings..")
        self.buildings = self.dataDownloader.download_with_retry(tags={'building': True})
        self.buildings = self.buildings[self.buildings.geometry.type == 'Polygon']
        self.buildings.to_file(f'shpFiles/buildings_{self.name}.shp', driver='ESRI Shapefile')
        self.buildings.to_file(f'geoJsonFiles/buildings_{self.name}.geojson', driver='GeoJSON')

    def download_waterway_data(self):
        print("Downloading waterways..")
        self.waterways = self.dataDownloader.download_with_retry(tags={'waterway': True})
        self.waterways = self.waterways[self.waterways.geometry.type == 'LineString']
        self.waterways.to_file(f'shpFiles/waterways_{self.name}.shp', driver='ESRI Shapefile')
        self.waterways.to_file(f'geoJsonFiles/waterways_{self.name}.geojson', driver='GeoJSON') 
    
    def add_buildings_tooltips(self, buildings, buildings_fg, styler, extra_data=None):
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
        #TODO: make the heatmap height and width change to the infrastructural data loaded to save space
        """Renders altitude heatmap of the area"""
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

        # TODO: find more efficient way to do this
        #convert heatmap to geodataframe to save as geojson
        # print("Creating heatmap gdf")
        # self.elevation_heatmap_geometry = [Point(lon, lat) for lat, lon, intensity in self.heatmap_data]
        # self.gdf_elevation_heatmap = gpd.GeoDataFrame(self.heatmap_data, geometry=self.elevation_heatmap_geometry, columns=['Latitude', 'Longitude', 'Intensity'])
        # self.gdf_elevation_heatmap.to_file(f'geoJsonFiles/elevation_heatmap_{self.name}.geojson', driver='GeoJSON')
        # print(f"Heatmap creaated and also saved as GeoJSON as geoJsonFiles/elevation_heatmap_{self.name}.geojson ")

    def render_buffer_area_road(self):
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

    def render_buffer_areas(self, water_buffer=True, road_buffer=True, weather_report=True):
        self.utm_zone = int((self.longitude + 180) // 6) + 1
        self.is_northern_hemisphere = self.latitude >= 0
        self.epsg_code = 32600 + self.utm_zone if self.is_northern_hemisphere else 32700 + self.utm_zone

        if water_buffer==True:
            self.render_buffer_area_water()
        if road_buffer==True:
            self.render_buffer_area_road()

    def save_map(self, interactive_marker=True, camera_simulation=True, weather_report=True):
        """Saves barebones map with static info"""
        self.m.save(self.map_name)

        # these NEED to take place AFTER saving the base html with static info
        if interactive_marker == True:
            self.javaScriptInjector.inject_interactive_marker(self.map_name)
        if camera_simulation == True:
            # TODO: get this from test to definitive:
            self.javaScriptInjector.inject_camera_simulation_script(self.map_name, camera_latitude=51.176858, camera_longitude=5.882079, direction=-60, width=94, reach=200, camera_name='camera 1 red', video_source='https://www.youtube.com/embed/4qOxFyZLcl0?si=VO9YbHXW7mDSENHO', cone_outline_color='red', cone_fill_color='lightred', camera_outline_color='blue', camera_fill_color='lightblue')
            self.javaScriptInjector.inject_camera_simulation_script(self.map_name, camera_latitude=51.179512, camera_longitude=5.878201, direction=180, width=94, reach=200, camera_name='camera 2 blue', video_source='https://www.youtube.com/embed/4qOxFyZLcl0?si=VO9YbHXW7mDSENHO', cone_outline_color='blue', cone_fill_color='lightblue', camera_outline_color='red', camera_fill_color='lightred')
            self.javaScriptInjector.inject_camera_simulation_script(self.map_name, camera_latitude=51.184346, camera_longitude=5.876827, direction=278, width=137, reach=800, camera_name='camera 3 green', video_source='https://www.youtube.com/embed/lffpBLDQqqc?si=H6um6OemAf8UQc56', cone_outline_color='green', cone_fill_color='lightgreen', camera_outline_color='purple', camera_fill_color='lightpurple')
        if weather_report == True:
            # Should be changed to a more secure way of storing the API key
            self.api_key_openweathermap = "d0160058812e1e5f9b9bdfb04c5ffca9"
            self.javaScriptInjector.inject_weather_report_script(self.map_name, self.latitude, self.longitude, self.api_key_openweathermap)
    
        return self.map_name

    def create_detailed_map(self):
        #download data with downloader
        self.download_building_data()
        self.download_road_network_data()
        self.download_waterway_data()
        
        #read saved files
        self.roads = gpd.read_file(f'shpFiles/roads_{self.name}.shp')
        self.all_buildings = gpd.read_file(f'shpFiles/buildings_{self.name}.shp')
        self.waterways = gpd.read_file(f'shpFiles/waterways_{self.name}.shp')
        
        # add roads to a featuregroup
        self.roads_fg = folium.FeatureGroup(name='Roads')
        folium.GeoJson(self.roads,style_function=self.mapStyler.style_roads).add_to(self.roads_fg)
        self.roads_fg.add_to(self.m)

        # add waterways to a featuregroup
        self.waterways_fg = folium.FeatureGroup(name='Waterways')
        folium.GeoJson(self.waterways,style_function=self.mapStyler.style_waterways).add_to(self.waterways_fg)
        self.waterways_fg.add_to(self.m)

        # add all buildings to featuregroup
        self.all_buildings_fg = folium.FeatureGroup(name="All buildings")
        folium.GeoJson(self.all_buildings, style_function=self.mapStyler.style_buildings).add_to(self.all_buildings_fg)
        self.all_buildings_fg = self.add_buildings_tooltips(self.all_buildings, self.all_buildings_fg, styler=self.mapStyler.style_buildings, extra_data = {'Digital Twin Name': self.name, 'Building Type': 'general'})
        self.all_buildings_fg.add_to(self.m)
        
        #render buffer areas, change the variables to include or not
        self.render_buffer_areas(water_buffer=True, road_buffer=True)
        #render altitude heatmap, BE CAUTIOUS, at large area options this will use a LOT of storage
        self.render_altitude_heatmap()

        # add layer control
        folium.LayerControl(collapsed=False, draggable=True).add_to(self.m)
        
        # save map, its converted to a static html
        
        self.save_map()
        
        saved_map_name = f'maps/map_{self.name}.html'
        print(f"Map saved under {saved_map_name} in the static folder.")

        return saved_map_name
    
# callng the stuff
# map_creator_1 = MapCreator(51.1797305,5.8812762,"Boschmolenplas", 1500, 150, 20)
# map_creator_1.create_detailed_map()