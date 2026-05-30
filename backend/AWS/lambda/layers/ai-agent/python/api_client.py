"""API client layer for Google Weather API"""

import os
import urllib.request
import urllib.parse
import json
from typing import Dict, Any
from datetime import datetime, timedelta


class GoogleWeatherClient:
    """Client for Google Weather API"""

    GOOGLE_API_KEY="***REMOVED***"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or self.GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("Google API key is required")

    def get_gps_by_location(self, location: str)-> Dict:
        """
        Get complete location data including GPS coordinates
        from Google Weather API
        """
        encoded_location = urllib.parse.quote(location)
        print(encoded_location)
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_location}&key={self.api_key}"
        
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                
                if 'error' in data:
                    raise Exception(f"API Error: {data['error']['message']}")
            
                return self._extract_location_info(data, location)
                
        except Exception as e:
            raise Exception(f"Failed to get {location} data: {str(e)}")

    def _extract_location_info(self, data: Dict, location: str) -> Dict:
        """Extract location information from geocoding response"""
        if data['status'] != 'OK' or not data['results']:
            raise Exception(f"No results found for location: {location}")
        
        result = data['results'][0]
        geometry = result['geometry']['location']
        
        return {
            'location': location,
            'formatted_address': result['formatted_address'],
            'coordinates': {
                'lat': geometry['lat'],
                'lng': geometry['lng']
            }
        }

    
    def filter_forecast_by_datetime_range(self, data: Dict, start_time: str, end_time: str) -> Dict[str, Any]:
        """Filter forecast data by datetime range"""
        filtered_data = []  

        for hour in data['forecast']['hours']:
            if start_time <= hour['time'] <= end_time:
                filtered_data.append(hour)
                print(hour['time'])

        return filtered_data


    def get_weather_forecast(self, lat: float, lon: float) -> dict:
        if not lat or not lon:
            raise ValueError("Latitude and Longitude must be provided.")

        base_url = "https://api.open-meteo.com/v1/forecast"
        
        # Get tomorrow's date
        current_date = datetime.now().date().isoformat()
        tomorrow = (datetime.now().date() + timedelta(days=1)).isoformat()


        params = {
            "latitude": str(lat),
            "longitude": str(lon),
            "hourly": "temperature_2m,precipitation,rain,weathercode",
            "temperature_unit": "celsius",
            "timezone": "auto",
            "start_date": current_date,
            "end_date":tomorrow
        }
        
        # Properly encode parameters
        query_string = urllib.parse.urlencode(params)
        url = f"{base_url}?{query_string}"
        
        print(f"Request URL: {url}")
        
        try:
            with urllib.request.urlopen(url) as response:
                weather_data = json.loads(response.read().decode())
                return weather_data
        except urllib.error.HTTPError as e:
            raise Exception(f"HTTP Error {e.code}: {e.reason}")
        except Exception as e:
            raise Exception(f"Failed to fetch weather data: {str(e)}")

        
        
if __name__ == "__main__":
    client = GoogleWeatherClient()
    gps = client.get_gps_by_location("SA5063")
    print(gps)
    lat, lon = gps['coordinates']['lat'], gps['coordinates']['lng']
    data = client.get_weather_forecast(lat, lon)
    print(data)

