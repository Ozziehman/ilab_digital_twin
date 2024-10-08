from mapGenerator import MapCreator

class SystemTestGenerator:
    def system_test(self, lat, long, name, radius, water_buffer_size, road_buffer_size):
        """Returns the name of the map, the completeness of the map should be inspected visually"""
        map_creator = MapCreator(lat, long, name, radius, water_buffer_size, road_buffer_size)
        return map_creator.create_detailed_map()

systemTestGenerator = SystemTestGenerator()

# locations in the netherlands

#Test 1, Rotterdam
try:
    name1 = systemTestGenerator.system_test(51.9225,4.47917,"Rotterdam", 1000, 100, 20)
    print("Test 1 succeeded")
except Exception as e:
    print("Test 1 failed: ", e)

# Test 2, Utrecht
try:
    name2 = systemTestGenerator.system_test(52.090737,5.121420,"Utrecht", 1000, 100, 20)
    print("Test 2 succeeded")
except Exception as e:
    print("Test 2 failed: ", e)

# Test 3, Amsterdam
try:
    name3 = systemTestGenerator.system_test(52.3676,4.9041,"Amsterdam", 1000, 100, 20)
    print("Test 3 succeeded")
except Exception as e:
    print("Test 2 failed: ", e)

# Test 4, Maastricht
try:
    name4 = systemTestGenerator.system_test(50.851368,5.690972,"Maastricht", 1000, 100, 20)
    print("Test 4 succeeded")
except Exception as e:
    print("Test 2 failed: ", e)

# Test 5, Boschmolenplas
try:
    name5 = systemTestGenerator.system_test(51.1797305,5.8812762,"Boschmolenplas", 1000, 100, 20)
    print("Test 5 succeeded")
except Exception as e:
    print("Test 2 failed: ", e)

# Test 6, Maasterp_ohe_en_laak
try:
    name6 = systemTestGenerator.system_test(51.114697,5.8301484,"Maasterp_ohe_en_laak", 1000, 100, 20)
    print("Test 6 succeeded")
except Exception as e:
    print("Test 2 failed: ", e)

# Test 7, Eindhoven
try:
    name7 = systemTestGenerator.system_test(51.4416,5.4697,"Eindhoven", 1000, 100, 20)
    print("Test 7 succeeded")
except Exception as e:
    print("Test 7 failed: ", e)

# Test 8, Breda
try:
    name8 = systemTestGenerator.system_test(51.5864,4.7759,"Breda", 1000, 100, 20)
    print("Test 8 succeeded")
except Exception as e:
    print("Test 8 failed: ", e)

# Test 9, Tilburg
try:
    name9 = systemTestGenerator.system_test(51.5590,5.0913,"Tilburg", 1000, 100, 20)
    print("Test 9 succeeded")
except Exception as e:
    print("Test 9 failed: ", e)

# Test 10, Den Bosch
try:
    name10 = systemTestGenerator.system_test(51.6978,5.3037,"Den Bosch", 1000, 100, 20)
    print("Test 10 succeeded")
except Exception as e:
    print("Test 10 failed: ", e)

print("system tests completed successfully")
print("The names of the maps are: ", name1, name2, name3, name4, name5, name6, name7, name8, name9, name10)


