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
        self.m = folium.Map(location=[self.latitude, self.longitude], zoom_start=12)

    def download_road_network_data(self):
        print("Downloading road network..")
        G = ox.graph_from_point(self.point, dist=self.load_dist, network_type='all')

        print("Converting road network to GeoDataFrame, getting the roads all prepared")
        self.gdf_roads = ox.graph_to_gdfs(G, nodes=False)
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
    
    def add_buildings_tooltips(self, buildings, buildings_fg, styler):
        for _, building in buildings.iterrows():
            geometry = building.geometry 
            properties = building.drop('geometry').to_dict() # gets properties

            tooltip_content = "<br>".join([f"{key}: {value}" for key, value in properties.items() if value is not None and value is not np.nan]) #lists all data not None in popup/tooltip
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
        self.lat_min = min(self.buildings.geometry.bounds.miny.min(), self.roads.geometry.bounds.miny.min(), self.waterways.geometry.bounds.miny.min())
        self.lat_max = max(self.buildings.geometry.bounds.maxy.max(), self.roads.geometry.bounds.maxy.max(), self.waterways.geometry.bounds.maxy.max())
        self.lon_min = min(self.buildings.geometry.bounds.minx.min(), self.roads.geometry.bounds.minx.min(), self.waterways.geometry.bounds.minx.min())
        self.lon_max = max(self.buildings.geometry.bounds.maxx.max(), self.roads.geometry.bounds.maxx.max(), self.waterways.geometry.bounds.maxx.max())

        self.heatmap_data = []
        for lat in np.arange(self.lat_min, self.lat_max, 0.00005):
            for lon in np.arange(self.lon_min, self.lon_max, 0.00005):
                altitude = self.elevation_data.get_elevation(lat, lon)
                if altitude is not None:
                    self.heatmap_data.append([lat, lon, altitude])

        gradient = {0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'}
        self.heatmap = HeatMap(self.heatmap_data, min_opacity=0.05, radius=15, blur=10, max_zoom=1, gradient=gradient)
        
        self.elevation_heatmap = folium.FeatureGroup(name="Elevation heatmap")
        self.heatmap.add_to(self.elevation_heatmap)
        self.elevation_heatmap.add_to(self.m)

        #convert heatmap to geodataframe to save as geojson
        print("Creating heatmap gdf")
        self.elevation_heatmap_geometry = [Point(lon, lat) for lat, lon, intensity in self.heatmap_data]
        self.gdf_elevation_heatmap = gpd.GeoDataFrame(self.heatmap_data, geometry=self.elevation_heatmap_geometry, columns=['Latitude', 'Longitude', 'Intensity'])
        self.gdf_elevation_heatmap.to_file(f'geoJsonFiles/elevation_heatmap_{self.name}.geojson', driver='GeoJSON')
        print(f"Heatmap creaated and also saved as GeoJSON as geoJsonFiles/elevation_heatmap_{self.name}.geojson ")

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
        self.nearby_buildings_road_fg = self.add_buildings_tooltips(self.nearby_buildings_road, self.nearby_buildings_road_fg, styler=self.mapStyler.style_nearby_buildings_road)
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
        self.nearby_buildings_water_fg = self.add_buildings_tooltips(self.nearby_buildings_water, self.nearby_buildings_water_fg, styler=self.mapStyler.style_nearby_buildings_water)
        self.nearby_buildings_water_fg.add_to(self.m)

    def render_buffer_areas(self, water_buffer=True, road_buffer=True):
        self.utm_zone = int((self.longitude + 180) // 6) + 1
        self.is_northern_hemisphere = self.latitude >= 0
        self.epsg_code = 32600 + self.utm_zone if self.is_northern_hemisphere else 32700 + self.utm_zone

        if water_buffer==True:
            self.render_buffer_area_water()
        if road_buffer==True:
            self.render_buffer_area_road()

    def save_map(self, interactive_marker=True):
        """Saves barebones map with static info"""
        self.map_name = f'static/maps/map_{self.name}.html'
        self.m.save(self.map_name)

        if interactive_marker == True:
            self.inject_interactive_marker(self.map_name)

        return self.map_name
    
    def inject_interactive_marker(self, map_file):
        """Injects live update js into the html"""
        with open(map_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        self.interactive_marker = """
<script>
    console.log("js injected");
    var mapDiv = document.querySelector('.folium-map');
    var mapDivId = mapDiv.id;
    var mapObject = window[mapDivId];
    
    mapObject.on('click', function(e) {
        var lat = e.latlng.lat;
        var lng = e.latlng.lng;
        var marker = L.marker([lat, lng]).addTo(mapObject);
        marker.bindPopup("Lat: " + lat.toFixed(6) + ", Lon: " + lng.toFixed(6)).openPopup();
    });

    //live update test
    //function updateMarker() {
    //    var lat = {{ latitude }} + (Math.random() - 0.5) * 0.001;
    //    var lng = {{ longitude }} + (Math.random() - 0.5) * 0.001;
    //    marker.setLatLng([lat, lng]);
    //}

    //setInterval(updateMarker, 1000);
</script>
        """
        # inject marker js into correct spot
        self.interactive_marker = self.interactive_marker.replace("{{ latitude }}", str(self.latitude)).replace("{{ longitude }}", str(self.longitude)) #replace string values with python vars
        modified_html = html_content.replace("</html>", self.interactive_marker + "\n</html>") #modify the html by 

        # save modified html back
        with open(map_file, 'w') as f:
            f.write(modified_html)
        
        print(f"interactive marker js injected and map saved back as {map_file}")

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
        self.all_buildings_fg = self.add_buildings_tooltips(self.all_buildings, self.all_buildings_fg, styler=self.mapStyler.style_buildings)
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
map_creator_1 = MapCreator(51.1797305,5.8812762,"Boschmolenplas", 500, 150, 20)
map_creator_1.create_detailed_map()