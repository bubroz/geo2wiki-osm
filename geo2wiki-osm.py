import requests
import math
import concurrent.futures
import csv
import datetime
import time
from haversine import haversine, Unit
from shapely.geometry import Polygon
import mwclient
from urllib.parse import quote


def get_wikipedia_url(title):
    base_url = "https://en.wikipedia.org/wiki/"
    return base_url + quote(title.replace(" ", "_"))


def get_wikipedia_geosearch(lat, lon, radius, limit):
    endpoint = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "geosearch",
        "gscoord": f"{lat}|{lon}",
        "gsradius": radius,
        "gslimit": limit,
        "format": "json",
    }
    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        data = response.json()
        return [
            {"title": item["title"], "lat": item["lat"], "lon": item["lon"]}
            for item in data["query"]["geosearch"]
        ]
    else:
        print(f"Error fetching Wikipedia geosearch data: {response.status_code}")
        return []


def get_osm_administrative_info(lat, lon):
    endpoint = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "format": "json",
        "lat": lat,
        "lon": lon,
        "zoom": 10,
        "addressdetails": 1,
    }
    headers = {"User-Agent": "YourAppName/1.0 (your_email@example.com)"}
    response = requests.get(endpoint, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching OSM data: {response.status_code}")
        return None

def get_osm_nearby_features(lat, lon, radius):
    overpass_url = "https://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node(around:{radius},{lat},{lon})[amenity];
      way(around:{radius},{lat},{lon})[building];
    );
    out body geom;
    """
    headers = {"User-Agent": "YourAppName/1.0 (your_email@example.com)"}
    response = requests.get(overpass_url, params={"data": overpass_query}, headers=headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        print("Rate limit hit, sleeping for 1 minute")
        time.sleep(60)
        return get_osm_nearby_features(lat, lon, radius)
    else:
        print(f"Error fetching OSM features: {response.status_code}")
        return None

def calculate_centroid(geometry):
    if not geometry:
        return None, None
    polygon = Polygon([(node['lon'], node['lat']) for node in geometry])
    centroid = polygon.centroid
    return centroid.y, centroid.x

# Define the endpoint and initial parameters
center_lat, center_lon = (38.897685330838804, -77.03653317988284)  # The White House
initial_radius = 500
max_radius = 10000
radius_increment = 500
min_results = 5
max_results = 20

current_radius = initial_radius
wiki_results = []
osm_admin_data = None
osm_features_data = []

# Concurrently fetch Wikipedia geosearch and OSM data
while current_radius <= max_radius and len(wiki_results) < min_results:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_wiki = executor.submit(get_wikipedia_geosearch, center_lat, center_lon, current_radius, max_results)
        future_osm_admin = executor.submit(get_osm_administrative_info, center_lat, center_lon)
        future_osm_features = executor.submit(get_osm_nearby_features, center_lat, center_lon, current_radius)

        wiki_results = future_wiki.result()
        if not osm_admin_data:
            osm_admin_data = future_osm_admin.result()
        osm_features = future_osm_features.result()

        if osm_features and "elements" in osm_features:
            osm_features_data.extend(osm_features["elements"])

        if wiki_results:
            print(f"Found {len(wiki_results)} Wikipedia results with radius: {current_radius} meters")
            if len(wiki_results) >= min_results:
                break
        else:
            print(f"No Wikipedia results found with radius: {current_radius} meters. Increasing radius.")
        current_radius += radius_increment

# Prepare results for CSV
csv_data = []

# Add Wikipedia results to CSV data
if wiki_results:
    for place in wiki_results[:max_results]:
        distance = haversine((center_lat, center_lon), (place['lat'], place['lon']), unit=Unit.METERS)
        url = get_wikipedia_url(place['title'])
        csv_data.append(["Wikipedia", place['title'], place['lat'], place['lon'], distance, url])
else:
    csv_data.append(["Wikipedia", "No results found", "", "", "", ""])

# Add OSM administrative information to CSV data
if osm_admin_data:
    csv_data.append([
        "OSM",
        osm_admin_data["display_name"],
        center_lat,
        center_lon,
        0,
        f"https://www.openstreetmap.org/?mlat={center_lat}&mlon={center_lon}#map=10/{center_lat}/{center_lon}",
    ])
else:
    csv_data.append(["OSM", "No administrative info found", "", "", "", "null"])

# Filter OSM nearby features and add to CSV data
filtered_osm_features = [
    element for element in osm_features_data
    if "tags" in element and element["tags"].get("name")
]

if filtered_osm_features:
    for element in filtered_osm_features:
        name = element["tags"].get("name", "Unnamed")
        if element["type"] == "node":
            lat, lon = element["lat"], element["lon"]
        elif element["type"] == "way":
            lat, lon = calculate_centroid(element["geometry"])
        else:
            lat, lon = None, None
        if lat and lon:
            distance = haversine((center_lat, center_lon), (lat, lon), unit=Unit.METERS)
            url = f"https://www.openstreetmap.org/{element['type']}/{element['id']}"
            csv_data.append(["OSM", name, lat, lon, distance, url])
    print(f"Found {len(filtered_osm_features)} OSM features with radius: {current_radius} meters")
else:
    csv_data.append(["OSM", "No nearby features found", "", "", "", "null"])
    print(f"No OSM features found with radius: {current_radius} meters")

# Get current date and time for the filename
now = datetime.datetime.now()
filename = now.strftime("results %d %b %Y_%H-%M-%S.csv")

# Write results to CSV file
with open(filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Source", "Name", "Latitude", "Longitude", "Distance (meters)", "URL"])
    writer.writerows(csv_data)

print(f"Results saved to {filename}")
print(f"Final radius used: {current_radius} meters")
print(f"Total Wikipedia results found: {len(wiki_results)}")
print(f"Total OSM features found: {len(filtered_osm_features)}")
