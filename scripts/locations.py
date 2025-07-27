import requests

def get_lat_lon(city_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": city_name,
        "format": "json",
        "limit": 1
    }
    
    try:
        response = requests.get(url, params=params, headers={"User-Agent": "MyApp"})
        response.raise_for_status()
        results = response.json()
        if results:
            lat = results[0]["lat"]
            lon = results[0]["lon"]
            return float(lat), float(lon)
        else:
            print("City not found.")
            return None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None

if __name__ == "__main__":
    city = input("Enter city name: ")
    lat, lon = get_lat_lon(city)
    if lat and lon:
        print(f"Coordinates of {city}:")
        print(f"Latitude: {lat}")
        print(f"Longitude: {lon}")
