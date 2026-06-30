import os
import ast
import osrm
from dotenv import load_dotenv

load_dotenv()
MAP_LOCATION = os.getenv("MAP_LOCATION")

# Initialize the python binding
osrm_py = osrm.OSRM(
    storage_config=MAP_LOCATION,
    algorithm='CH',
    # This must be false since it was built for shared_memory
    use_shared_memory = False,
    max_locations_distance_table = 5000,
    max_locations_trip = 500,
    # Must set to true to avoid loading the entire map to ram.
    use_mmap = True
)

# Coordinates are constructed using tuple with [lon, lat]

###
# Calculating the OD Cost Matrix
###
route_params = osrm.TableParameters(
    coordinates = [
        [-77.4688, 39.6225],  # Cunningham Falls State Park, Catoctin Mountains
        [-75.4408, 38.1294],  # Pocomoke River State Park, Lower Eastern Shore
        [-75.1372, 38.2375],  # Assateague State Park, Atlantic Coast
        [-77.2492, 39.1509],  # Seneca Creek State Park, Montgomery County
    ],
    sources=[0,1],
    destinations=[1,2],
    # duration is in seconds and distance is in meters
    annotations=["duration", "distance"]
)
# Pass it into the osrm_py instance
table_result = osrm_py.Table(route_params)
# The result returned from the osrm_py instance is a custom object that needs to be converted to a dict for easier handling.  The string representation of the object is in single quoted json format, so we can use ast.literal_eval to convert it to a dict.
table_result = ast.literal_eval(str(table_result)) if table_result else None
print(table_result)
# Refers to the api.md for other road network calculations

