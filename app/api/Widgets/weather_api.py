import requests
import json
import os
from flask import request
from . import widgets_bp 
from ...services.Widgets.location_getter import get_lat_lon

# File to persist city data
from ...core.config import Config
from pathlib import Path

# File to persist city data
STORAGE_FILE = Path(Config.STORAGE_FILE_JSON) / "city_data.json"




@widgets_bp.route("/weather", methods=["POST"])
def set_city():
    data = request.get_json()
    if not data or "city" not in data:
        return {"error": "Missing city in request"}, 400
    
    city = data["city"]
    lat, lon = get_lat_lon(city)

    if lat is None or lon is None:
        return {"error": "Could not find location"}, 404
    
    # Save to file
    save_location_to_file(city, lat, lon)

    return {"message": f"Location saved for {city}"}, 200


@widgets_bp.route("/weather", methods=["GET"])
def get_weather():
    stored_location = load_location_from_file()

    if not stored_location["lat"] or not stored_location["lon"]:
        return {"error": "No city stored. Please POST a city first."}, 400

    latitude = stored_location["lat"]
    longitude = stored_location["lon"]
    location_name = stored_location["city"]

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={latitude}&longitude={longitude}"
        f"&current=temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m"
        f"&timezone=auto"
    )

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        current = data.get("current", {})

        weather_code = current.get("weather_code", -1)
        weather_desc = map_weather_code(weather_code)

        return {
            "temperature": f"{current.get('temperature_2m', 'N/A')}°C",
            "condition": weather_desc,
            "location": location_name,
            "humidity": f"{current.get('relative_humidity_2m', 'N/A')}%",
        }

    except Exception as e:
        return {"error": str(e)}, 500



# Handle Save/Load Json
def save_location_to_file(city, lat, lon):
    # Ensure parent directories exist
    STORAGE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump({"city": city, "lat": lat, "lon": lon}, f)



def load_location_from_file():
    if not os.path.exists(STORAGE_FILE):
        return {"city": None, "lat": None, "lon": None}
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


#Handle Weather Code 
def map_weather_code(code):
    weather_codes = {
        0: "Clear",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Cloudy",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        95: "Thunderstorm",
        99: "Thunderstorm with hail"
    }
    return weather_codes.get(code, "Unknown")
