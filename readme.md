# Geospatial Search Script

This script performs a geospatial search for Wikipedia and OpenStreetMap (OSM) data around a specified center point (latitude and longitude). It incrementally increases the search radius until it finds a minimum number of Wikipedia results. The script concurrently fetches data from both Wikipedia and OSM, computes distances, and saves the results in a CSV file.

## Features

- Geospatial search for Wikipedia articles and OpenStreetMap features
- Concurrent data fetching for improved performance
- Incremental radius increase to find a minimum number of results
- Distance calculation using the Haversine formula
- CSV output with timestamp for easy data analysis

## Requirements

- Python 3.x
- Required libraries: requests, haversine, shapely, mwclient

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/geo2wiki-osm.git
   cd geo2wiki-osm
   ```

2. Install the required libraries:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Open `geo2wiki-osm.py` and modify the following parameters if needed:
   - `center_lat` and `center_lon`: The center point for the search
   - `initial_radius`, `max_radius`, `radius_increment`: Search radius parameters
   - `min_results`, `max_results`: Result count parameters

2. Run the script:
   ```
   python geo2wiki-osm.py
   ```

3. The script will output progress information and save the results in a CSV file with a timestamp in the filename.

## Script Overview

The script consists of the following main components:

1. **Wikipedia API Functions**: Fetch Wikipedia URLs and perform geosearch
2. **OSM API Functions**: Fetch administrative info and nearby features from OpenStreetMap
3. **Geometry Functions**: Calculate centroids for polygon features
4. **Main Script Logic**: Coordinate the data fetching, processing, and CSV output

## Functions

### Wikipedia API Functions

- `get_wikipedia_url(title)`: Generates the full URL for a Wikipedia page given its title
- `get_wikipedia_geosearch(lat, lon, radius, limit)`: Performs a geosearch for Wikipedia articles

### OSM API Functions

- `get_osm_administrative_info(lat, lon)`: Fetches administrative information from OSM
- `get_osm_nearby_features(lat, lon, radius)`: Fetches nearby features from OSM using the Overpass API

### Geometry Functions

- `calculate_centroid(geometry)`: Calculates the centroid of a set of geographical coordinates

## Output

The script generates a CSV file with the following columns:
1. Source (Wikipedia or OSM)
2. Name
3. Latitude
4. Longitude
5. Distance (in meters)
6. URL

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Wikipedia API
- OpenStreetMap and Overpass API
- Haversine formula for distance calculations
- Shapely library for geometry operations
