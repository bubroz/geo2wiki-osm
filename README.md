# README.md

## Geospatial Search Script

This script performs a geospatial search for Wikipedia and OpenStreetMap (OSM) data around a specified center point (latitude and longitude). It incrementally increases the search radius until it finds a minimum number of Wikipedia results. The script concurrently fetches data from both Wikipedia and OSM, computes distances, and saves the results in a CSV file.

### Requirements

- Python 3.x
- `requests` library

### Installation

Install the required library using pip:

```sh
pip install requests
```

### Script Overview

The script consists of the following main components:

1. **Haversine Distance Function**
2. **Wikipedia API Functions**
3. **OSM API Functions**
4. **Main Script Logic**

### Functions

#### 1. Haversine Distance Function

Calculates the distance between two points on the Earth's surface given their latitude and longitude using the Haversine formula.

```python
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(R * c)
```

#### 2. Wikipedia API Functions

- **Get Wikipedia URL by Title**: Fetches the full URL of a Wikipedia page given its title.

```python
def get_wikipedia_url(title):
    endpoint = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": title,
        "prop": "info",
        "inprop": "url",
        "format": "json",
    }
    response = requests.get(endpoint, params=params)
    if response.status_code == 200:
        data = response.json()
        page = next(iter(data["query"]["pages"].values()))
        return page["fullurl"]
    else:
        print(f"Error fetching URL for {title}: {response.status_code}")
        return None
```

- **Get Wikipedia Geosearch**: Searches for Wikipedia articles near a specified latitude and longitude within a given radius and limit.

```python
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
        return response.json()
    else:
        print(f"Error fetching Wikipedia geosearch data: {response.status_code}")
        return None
```

#### 3. OSM API Functions

**Note**: You need to replace the OSM headers in `get_osm_administrative_info` and `get_osm_nearby_features` with your email or app information.

- **Get OSM Administrative Info**: Fetches administrative information from OSM given latitude and longitude.

```python
def get_osm_administrative_info(lat, lon):
    endpoint = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "format": "json",
        "lat": lat,
        "lon": lon,
        "zoom": 10,
        "addressdetails": 1,
    }
    headers = {"User-Agent": "geo2wiki-osm (your_email@example.com)"}
    response = requests.get(endpoint, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching OSM data: {response.status_code}")
        return None
```

- **Get OSM Nearby Features**: Fetches nearby features (nodes and ways) from OSM using the Overpass API.

```python
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
    response = requests.get(
        overpass_url, params={"data": overpass_query}, headers=headers
    )
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 429:
        print("Rate limit hit, sleeping for 1 minute")
        time.sleep(60)
        return get_osm_nearby_features(lat, lon, radius)
    else:
        print(f"Error fetching OSM features: {response.status_code}")
        return None
```

- **Calculate Centroid**: Calculates the centroid of a set of geographical coordinates.

```python
def calculate_centroid(geometry):
    if not geometry:
        return None, None
    lat = sum([node["lat"] for node in geometry]) / len(geometry)
    lon = sum([node["lon"] for node in geometry]) / len(geometry)
    return lat, lon
```

#### 4. Main Script Logic

- **Define Parameters**: Set the center coordinates, initial radius, maximum radius, radius increment, minimum and maximum results. Default center_lat and center_lon is SpaceX Starbase

- **Fetch Data Concurrently**: Use `concurrent.futures.ThreadPoolExecutor` to fetch Wikipedia and OSM data concurrently.

- **Prepare CSV Data**: Collect and format data for writing to the CSV file.

- **Write to CSV**: Save the results to a CSV file with a timestamp in the filename.

```python
# Define the endpoint and initial parameters
center_lat, center_lon = (38.89777476492068, -77.03654524519337)  # The White House
initial_radius = 500
max_radius = 10000  # Max radius for Wikipedia is capped at 10000
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
        future_wiki = executor.submit(
            get_wikipedia_geosearch, center_lat, center_lon, current_radius, max_results
        )
        future_osm_admin = executor.submit(
            get_osm_administrative_info, center_lat, center_lon
        )
        future_osm_features = executor.submit(
            get_osm_nearby_features, center_lat, center_lon, current_radius
        )

        wiki_data = future_wiki.result()
        if not osm_admin_data:
            osm_admin_data = future_osm_admin.result()
        osm_features = future_osm_features.result()

        if osm_features and "elements" in osm_features:
            osm_features_data.extend(osm_features["elements"])

        if wiki_data and "query" in wiki_data and wiki_data["query"]["geosearch"]:
            wiki_results = wiki_data["query"]["geosearch"]
            if len(wiki_results) >= min_results:
                print(
                    f"Found {len(wiki_results)} Wikipedia results with radius: {current_radius} meters"
                )
            else:
                print(
                    f"Found {len(wiki_results)} Wikipedia results with radius: {current_radius} meters. Increasing radius."
                )
                current_radius += radius_increment
        else:
            print(
                f"No Wikipedia results found with radius: {current_radius} meters. Increasing radius."
            )
            current_radius += radius_increment

# Prepare results for CSV
csv_data = []

# Add Wikipedia results to CSV data
if len(wiki_results) >= 1:
    for place in wiki_results[:max_results]:
        distance = haversine_distance(
            center_lat, center_lon, place["lat"], place["lon"]
        )
        url = get_wikipedia_url(place["title"])
        csv_data.append(
            ["Wikipedia", place["title"], place["lat"], place["lon"], distance, url]
        )
else:
    csv_data.append(["Wikipedia", "No results found", "", "", "", ""])

# Add OSM administrative information to CSV data
if osm_admin_data:
    csv_data.append(
        [
            "OSM",
            osm_admin_data["display_name"],
            center_lat,
            center_lon,
            0,
            f"https://www.openstreetmap.org/?mlat={center_lat}&mlon={center_lon}#map=10/{center_lat}/{center_lon}",
        ]
    )
else:
    csv_data.append(["OSM", "No administrative info found", "", "", "", "null"])

# Filter OSM nearby features and add to CSV data
filtered_osm_features = [
    element
    for element in osm_features_data
    if "tags" in element and element["tags"].get("name")
]

if filtered_osm_features:
    for element in filtered_osm_features:
        name = element["tags"].get("name", "Unnamed")

### LICENSE
This project is licensed under the MIT License - see the LICENSE file for details.