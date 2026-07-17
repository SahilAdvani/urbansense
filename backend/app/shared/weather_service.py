import urllib.request
import urllib.parse
import json
from typing import Dict, Any, Optional

def get_real_air_pollution(lat: float, lon: float, api_key: str) -> Optional[Dict[str, Any]]:
    """Fetch current air pollution metrics from OpenWeatherMap."""
    try:
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
        req = urllib.request.Request(url, headers={"User-Agent": "UrbanSense-AQI/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if "list" in data and len(data["list"]) > 0:
                return data["list"][0]
    except Exception as e:
        print(f"Error fetching live air pollution from OWM: {e}")
    return None

def get_historical_air_pollution(lat: float, lon: float, start: int, end: int, api_key: str) -> Optional[list]:
    """Fetch historical hourly air pollution metrics from OpenWeatherMap."""
    try:
        url = f"http://api.openweathermap.org/data/2.5/air_pollution/history?lat={lat}&lon={lon}&start={start}&end={end}&appid={api_key}"
        req = urllib.request.Request(url, headers={"User-Agent": "UrbanSense-AQI/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            if "list" in data:
                return data["list"]
    except Exception as e:
        print(f"Error fetching historical air pollution from OWM: {e}")
    return None

def get_real_weather(lat: float, lon: float, api_key: str) -> Optional[Dict[str, Any]]:
    """Fetch current weather parameters from OpenWeatherMap."""
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={api_key}"
        req = urllib.request.Request(url, headers={"User-Agent": "UrbanSense-AQI/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching live weather from OWM: {e}")
    return None

def calculate_sub_index(value: float, breakpoints: list) -> float:
    """Helper to interpolate sub-index based on linear CPCB breakpoints."""
    for bp in breakpoints:
        c_low, c_high, i_low, i_high = bp
        if c_low <= value <= c_high:
            return i_low + (value - c_low) * (i_high - i_low) / (c_high - c_low)
    # Beyond highest breakpoint, default to max scale proportional
    last_bp = breakpoints[-1]
    return last_bp[3]

def calculate_indian_aqi(pm25: float, pm10: float, no2: float, co: float, so2: float, o3: float) -> int:
    """
    Calculate Indian CPCB Air Quality Index (AQI).
    Returns the maximum sub-index of the active pollutant parameters.
    Reference: CPCB Guidelines 2014.
    """
    # Breakpoints format: [conc_min, conc_max, index_min, index_max]
    pm25_bp = [[0, 30, 0, 50], [30.1, 60, 51, 100], [60.1, 90, 101, 200], [90.1, 120, 201, 300], [120.1, 250, 301, 400], [250.1, 9999, 401, 500]]
    pm10_bp = [[0, 50, 0, 50], [50.1, 100, 51, 100], [100.1, 250, 101, 200], [250.1, 350, 201, 300], [350.1, 430, 301, 400], [430.1, 9999, 401, 500]]
    no2_bp = [[0, 40, 0, 50], [40.1, 80, 51, 100], [80.1, 180, 101, 200], [180.1, 280, 201, 300], [280.1, 400, 301, 400], [400.1, 9999, 401, 500]]
    co_bp = [[0, 1.0, 0, 50], [1.01, 2.0, 51, 100], [2.01, 10.0, 101, 200], [10.01, 17.0, 201, 300], [17.01, 34.0, 301, 400], [34.01, 9999, 401, 500]]
    so2_bp = [[0, 40, 0, 50], [40.1, 80, 51, 100], [80.1, 380, 101, 200], [380.1, 800, 201, 300], [800.1, 1600, 301, 400], [1600.1, 9999, 401, 500]]
    o3_bp = [[0, 50, 0, 50], [50.1, 100, 51, 100], [100.1, 168, 101, 200], [168.1, 208, 201, 300], [208.1, 748, 301, 400], [748.1, 9999, 401, 500]]

    sub_indices = []
    if pm25 is not None and pm25 > 0:
        sub_indices.append(calculate_sub_index(pm25, pm25_bp))
    if pm10 is not None and pm10 > 0:
        sub_indices.append(calculate_sub_index(pm10, pm10_bp))
    if no2 is not None and no2 > 0:
        sub_indices.append(calculate_sub_index(no2, no2_bp))
    if co is not None and co > 0:
        sub_indices.append(calculate_sub_index(co, co_bp))
    if so2 is not None and so2 > 0:
        sub_indices.append(calculate_sub_index(so2, so2_bp))
    if o3 is not None and o3 > 0:
        sub_indices.append(calculate_sub_index(o3, o3_bp))

    if not sub_indices:
        return 0

    return int(max(sub_indices))
