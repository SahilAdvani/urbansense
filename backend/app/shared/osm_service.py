import urllib.request
import urllib.parse
import json
from typing import List, Dict, Any

def fetch_city_suburbs(lat: float, lon: float, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch actual suburb and neighborhood names and coordinates in a city
    using the public OpenStreetMap Overpass API.
    """
    # Overpass QL query to fetch major suburbs in a 15km radius (optimized to prevent timeouts)
    query = f"""
    [out:json][timeout:10];
    node["place"="suburb"](around:15000, {lat}, {lon});
    out body {limit};
    """
    
    mirrors = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.osm.ch/api/interpreter"
    ]
    
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    
    for url in mirrors:
        try:
            print(f"[OSM] Querying Overpass mirror: {url}")
            req = urllib.request.Request(
                url, 
                data=data,
                headers={"User-Agent": "UrbanSense-AQI-Dashboard/1.0 (India)"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                suburbs = []
                if "elements" in result:
                    for element in result["elements"]:
                        name = element.get("tags", {}).get("name")
                        if name and element.get("lat") and element.get("lon"):
                            suburbs.append({
                                "name": name,
                                "latitude": float(element["lat"]),
                                "longitude": float(element["lon"])
                            })
                # Remove duplicate names if any
                seen = set()
                unique_suburbs = []
                for s in suburbs:
                    if s["name"] not in seen:
                        seen.add(s["name"])
                        unique_suburbs.append(s)
                
                if unique_suburbs:
                    return unique_suburbs[:limit]
        except Exception as e:
            print(f"[OSM] Mirror {url} failed: {e}")
            continue
    
    return []

def generate_suburb_geojson(lat: float, lon: float, name: str) -> dict:
    """
    Generate a small, clean rectangular bounding polygon around coordinates
    representing the suburb area on Leaflet maps.
    """
    # Offset of 0.01 degrees is roughly 1km
    offset = 0.012
    coords = [
        [lon - offset, lat - offset],
        [lon + offset, lat - offset],
        [lon + offset, lat + offset],
        [lon - offset, lat + offset],
        [lon - offset, lat - offset]
    ]
    return {
        "type": "Feature",
        "properties": {"name": name},
        "geometry": {
            "type": "Polygon",
            "coordinates": [coords]
        }
    }
