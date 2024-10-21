from mapGenerator import MapCreator

class SystemTestGenerator:
    def system_test(self, lat, long, name, radius, water_buffer_size, road_buffer_size, cameras, passage_points):
        """Returns the name of the map, the completeness of the map should be inspected visually"""
        map_creator = MapCreator(lat, long, name, radius, water_buffer_size, road_buffer_size, cameras, passage_points)
        return map_creator.create_detailed_map()

systemTestGenerator = SystemTestGenerator()

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

#Test 1, Rotterdam
try:
    name1 = systemTestGenerator.system_test(51.9225,4.47917,"Rotterdam", 1000, 100, 20, cameras, passage_points)
    print("Test 1 succeeded")
except Exception as e:
    print("Test 1 failed: ", e)

# Test 2, Utrecht
try:
    name2 = systemTestGenerator.system_test(52.090737,5.121420,"Utrecht", 1000, 100, 20, cameras, passage_points)
    print("Test 2 succeeded")
except Exception as e:
    print("Test 2 failed: ", e)

# Test 3, Amsterdam
try:
    name3 = systemTestGenerator.system_test(52.3676,4.9041,"Amsterdam", 1000, 100, 20, cameras, passage_points)
    print("Test 3 succeeded")
except Exception as e:
    print("Test 2 failed: ", e)

# Test 4, Maastricht
try:
    name4 = systemTestGenerator.system_test(50.851368,5.690972,"Maastricht", 1000, 100, 20, cameras, passage_points)
    print("Test 4 succeeded")
except Exception as e:
    print("Test 2 failed: ", e)

# Test 5, Boschmolenplas
try:
    name5 = systemTestGenerator.system_test(51.1797305,5.8812762,"Boschmolenplas", 1000, 100, 20, cameras, passage_points)
    print("Test 5 succeeded")
except Exception as e:
    print("Test 2 failed: ", e)

# Test 6, Maasterp_ohe_en_laak
try:
    name6 = systemTestGenerator.system_test(51.114697,5.8301484,"Maasterp_ohe_en_laak", 1000, 100, 20, cameras, passage_points)
    print("Test 6 succeeded")
except Exception as e:
    print("Test 2 failed: ", e)

# Test 7, Eindhoven
try:
    name7 = systemTestGenerator.system_test(51.4416,5.4697,"Eindhoven", 1000, 100, 20, cameras, passage_points)
    print("Test 7 succeeded")
except Exception as e:
    print("Test 7 failed: ", e)

# Test 8, Breda
try:
    name8 = systemTestGenerator.system_test(51.5864,4.7759,"Breda", 1000, 100, 20, cameras, passage_points)
    print("Test 8 succeeded")
except Exception as e:
    print("Test 8 failed: ", e)

# Test 9, Tilburg
try:
    name9 = systemTestGenerator.system_test(51.5590,5.0913,"Tilburg", 1000, 100, 20, cameras, passage_points)
    print("Test 9 succeeded")
except Exception as e:
    print("Test 9 failed: ", e)

# Test 10, Den Bosch
try:
    name10 = systemTestGenerator.system_test(51.6978,5.3037,"Den Bosch", 1000, 100, 20, cameras, passage_points)
    print("Test 10 succeeded")
except Exception as e:
    print("Test 10 failed: ", e)

print("system tests completed successfully")
print("The names of the maps are: ", name1, name2, name3, name4, name5, name6, name7, name8, name9, name10)


