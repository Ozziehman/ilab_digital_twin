import osmnx as ox
import geopandas as gpd
import folium
import time
import os 


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
        # region (subregion) download road network and convert to geodataframe
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

    def save_map(self):
        """Saves barebones map with static info"""
        self.map_name = f'static/maps/map_{self.name}.html'
        self.m.save(self.map_name)

        return self.map_name

    def create_detailed_map(self):
        #download data with downloader
        self.download_building_data()
        self.download_road_network_data()
        self.download_waterway_data()
        
        self.roads = gpd.read_file(f'shpFiles/roads_{self.name}.shp')
        
        self.buildings = gpd.read_file(f'shpFiles/buildings_{self.name}.shp')
        
        self.waterways = gpd.read_file(f'shpFiles/waterways_{self.name}.shp')
        
        #_______________________________________________
        # region ADD ALL SEPERATE ELEMENTS TO FOLIUM MAP

        # region (subregion) add roads folium map
        # add roads
        self.roads_fg = folium.FeatureGroup(name='Roads')
        folium.GeoJson(self.roads,style_function=self.mapStyler.style_roads).add_to(self.roads_fg)
        self.roads_fg.add_to(self.m)
        # endregion

        # region (subregion) add waterways to map
        # add water bodies
        self.waterways_fg = folium.FeatureGroup(name='Waterways')
        folium.GeoJson(self.waterways,style_function=self.mapStyler.style_waterways).add_to(self.waterways_fg)
        self.waterways_fg.add_to(self.m)
        # endregion    

        # region (subregion) add all buildings to folium map
        self.all_buildings = self.buildings
        # add all buildings
        self.all_buildings_fg = folium.FeatureGroup(name="All buildings")
        folium.GeoJson(self.all_buildings, style_function=self.mapStyler.style_buildings).add_to(self.all_buildings_fg)
        self.all_buildings_fg.add_to(self.m)
        # endregion

        # endregion
        #_______________________________________________

        #_______________________________________________
        # region ADD FULL AREA COVERAGES TO FOLIUM MAP

        # region (subregion) getting CRS to map areas to
        # get CRS for projected area, this is used for projecting the buffer area
        self.utm_zone = int((self.longitude + 180) // 6) + 1
        self.is_northern_hemisphere = self.latitude >= 0
        self.epsg_code = 32600 + self.utm_zone if self.is_northern_hemisphere else 32700 + self.utm_zone
        # endregion
        
        # region (subregion) water buffer area, display buildings within the water bufer
        # BUILDINGS WITHIN WATER BUFFER
        # re-project water bodies to the projected CRS
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
        self.nearby_buildings_water_fg.add_to(self.m)
        #endregion

        # region (subregion) water buffer area, display buildings within the water bufer
        # BUILDINGS WITHIN ROAD BUFFER
        # re-project raods to the projected CRS
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
        self.nearby_buildings_road_fg.add_to(self.m)
        # endregion
        # endregion
        #_______________________________________________

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