import requests
import config

def get_coordinates(address: str) -> dict:
    """Get GPS coordinates from address using Google Geocoding API"""
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": config.GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data["status"] == "OK" and data["results"]:
            location = data["results"][0]["geometry"]["location"]
            return {
                "success": True,
                "latitude": location["lat"],
                "longitude": location["lng"],
                "formatted_address": data["results"][0]["formatted_address"]
            }
        else:
            return {"success": False, "error": f"Geocoding failed: {data.get('status', 'Unknown error')}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_address(lat: float, lng: float) -> dict:
    """Get address from GPS coordinates using Google Reverse Geocoding API"""
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "latlng": f"{lat},{lng}",
        "key": config.GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data["status"] == "OK" and data["results"]:
            return {
                "success": True,
                "address": data["results"][0]["formatted_address"],
                "components": data["results"][0]["address_components"]
            }
        else:
            return {"success": False, "error": f"Reverse geocoding failed: {data.get('status', 'Unknown error')}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}