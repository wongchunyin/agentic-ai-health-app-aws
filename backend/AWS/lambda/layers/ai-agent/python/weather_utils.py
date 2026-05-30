import urllib.request
from datetime import date, timedelta, datetime
import json
from typing import Optional, Dict
try:
    from .api_client import GoogleWeatherClient
    from .datetime_utils import DateTimeHandler
except ImportError:
    # Fallback for direct execution
    from api_client import GoogleWeatherClient
    from datetime_utils import DateTimeHandler

# static dictionary to map weather codes to descriptions
CODE_TO_WEATHER = {
                0: "Clear sky",
                1: "Mainly clear",
                2: "Partly cloudy",
                3: "Overcast",
                45: "Fog",
                48: "Depositing rime fog",
                51: "Light drizzle",
                53: "Moderate drizzle",
                55: "Dense drizzle",
                56: "Light freezing drizzle",
                57: "Dense freezing drizzle",
                61: "Slight rain",
                63: "Moderate rain",
                65: "Heavy rain",
                66: "Light freezing rain",
                67: "Heavy freezing rain",
                71: "Slight snow fall",
                73: "Moderate snow fall",
                75: "Heavy snow fall",
                77: "Snow grains",
                80: "Slight rain showers",
                81: "Moderate rain showers",
                82: "Violent rain showers",
                85: "Slight snow showers",
                86: "Heavy snow showers",
                95: "Thunderstorm",
                96: "Thunderstorm with slight hail",
                99: "Thunderstorm with heavy hail"
            }

class WeatherUtils():
    def __init__(self, location: str = None):
        if location == None:
            raise ValueError("Cannot get weather data without location. Please set a location for WeatherUtils")
        self.apiClient = GoogleWeatherClient()
        self.dtHandler = DateTimeHandler()
        self.gps = self.apiClient.get_gps_by_location(location)
        self.weatherData = self.apiClient.get_weather_forecast(self.gps['coordinates']['lat'], self.gps['coordinates']['lng'])
    
    def _extract_from_forecast(self, weather_data: dict, target_iso: str) -> Optional[dict]:
        """Extract weather from forecast data"""
        target_date = target_iso.split('T')[0]
        
        for day in weather_data['forecast']['days']:
            if day.get('date') == target_date:
                # Check hourly data if available
                if 'hours' in day:
                    for hour_data in day['hours']:
                        hour_time = hour_data.get('time')
                        if hour_time and self._times_match(hour_time, target_iso):
                            return hour_data
                return day  # Return daily data if no hourly match
        
        return None
    
    def _extract_from_hourly(self, weather_data: dict, target_iso: str, duration: int) -> Optional[dict]:
        """Extract weather from hourly data"""
        if 'hourly' not in weather_data or 'time' not in weather_data['hourly']:
            return None
            
        times = weather_data['hourly']['time']
        target_time = target_iso.split('T')[0] + 'T' + target_iso.split('T')[1][:5]  # Format: YYYY-MM-DDTHH:MM
        
        # Calculate end_time = target_time + duration (hours)
        target_dt = datetime.fromisoformat(target_time)
        end_dt = target_dt + timedelta(hours=duration)
        # end_time = end_dt.strftime('%Y-%m-%dT%H:%M')
        

        try:
            # Find all data within target_dt and end_dt
            indices = []
            for i, time_str in enumerate(times):
                time_dt = datetime.fromisoformat(time_str)
                if target_dt <= time_dt <= end_dt:
                    indices.append(i)
            
            if not indices:
                return None
                
            return {
                'time': [times[i] for i in indices],
                'temperature_2m': [weather_data['hourly']['temperature_2m'][i] for i in indices],
                'precipitation': [weather_data['hourly']['precipitation'][i] for i in indices],
                'weathercode': [weather_data['hourly']['weathercode'][i] for i in indices]
            }
        except (ValueError, IndexError):
            return None
    
    def _times_match(self, time1: str, time2: str, tolerance_minutes: int = 30) -> bool:
        """Check if two ISO times are within tolerance"""
        try:
            from datetime import datetime
            dt1 = datetime.fromisoformat(time1.replace('Z', '+00:00'))
            dt2 = datetime.fromisoformat(time2.replace('Z', '+00:00'))
            
            time_diff = abs((dt1 - dt2).total_seconds())
            return time_diff <= (tolerance_minutes * 60)
            
        except ValueError:
            return False
        
    
    
    def get_weather_by_specific_period(self, month: int, day: int, hour: int, minute: int, year: int = None, duration: int = 1) -> dict:
        """Get weather forecast for a specific period"""
        if year is None:
            year = datetime.now().year
        
        # Construct datetime string to match weather API format
        target_datetime = f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:00"
        
        # Convert to ISO format
        iso_datetime = self.dtHandler.to_iso_format(target_datetime)
        if not iso_datetime:
            raise ValueError("Invalid datetime parameters")
        
        if iso_datetime < datetime.now().isoformat():
            raise ValueError("Cannot get weather data for past dates.")


        # Extract weather for specific datetime
        weather_result = self.extract_weather_by_datetime(target_datetime=iso_datetime, duration=duration)
        
        if not weather_result:
            raise ValueError(f"No weather data found for {target_datetime}")
        
        return weather_result

   
    def extract_weather_by_datetime(self, 
                                   target_datetime: str,
                                   duration: int = 1,
                                   timezone_str: str = 'UTC') -> Optional[Dict]:
        """
        Extract weather for a specific datetime from weather API response
        Handles both current and forecast data structures
        """
        try:
            target_iso = self.dtHandler.to_iso_format(target_datetime, timezone_str)
            if not target_iso:
                return None
            
            # Check if response has forecast data
            if 'forecast' in self.weatherData and 'days' in self.weatherData['forecast']:
                return self._extract_from_forecast(self.weatherData, target_iso)
            
            # Check if response has hourly data
            elif 'hourly' in self.weatherData:
                return self._extract_from_hourly(self.weatherData, target_iso, duration)
            
            # For current weather, check if timestamp matches
            elif 'current' in self.weatherData:
                current_time = self.weatherData['current'].get('time')
                if current_time and self._times_match(current_time, target_iso):
                    return self.weatherData['current']
            
            return None
            
        except Exception:
            return None


    @staticmethod
    def is_suitable(forecast) -> tuple:
        """Check if weather is suitable for outdoor activities"""
        if not forecast:
            raise ValueError("Forecast data is empty.")
        
        # Handle both list and dict formats
        if isinstance(forecast, dict):
            # Dictionary format from filter_forecast_by_datetime_range
            temperatures = forecast.get("temperature_2m", [])
            precipitations = forecast.get("precipitation", [])
            weathercodes = forecast.get("weathercode", [])
            
            # Handle single values or lists
            if not isinstance(temperatures, list):
                temperatures = [temperatures]
            if not isinstance(precipitations, list):
                precipitations = [precipitations]
            if not isinstance(weathercodes, list):
                weathercodes = [weathercodes]
            
            for i in range(len(temperatures)):
                temp = temperatures[i]
                precip = precipitations[i]
                weathercode = weathercodes[i]
                
                if temp < 10 or temp > 30:
                    return False, "Temperature out of range (10-30°C)"
                if precip > 0:
                    return False, "Precipitation detected"
                if weathercode not in [0, 1, 2, 3]:  # Clear or partly cloudy
                    return False, f"Unsuitable weather: {CODE_TO_WEATHER.get(weathercode)}"
        else:
            # List format from extract_specific_forecast_by_datetime
            for entry in forecast:
                temp = entry["temperature_2m"]
                precip = entry["precipitation"]
                weathercode = entry["weathercode"]
                
                if temp < 10 or temp > 30:
                    return False, "Temperature out of range (10-30°C)"
                if precip > 0:
                    return False, "Precipitation detected"
                if weathercode not in [0, 1, 2, 3]:  # Clear or partly cloudy
                    return False, f"Unsuitable weather: {CODE_TO_WEATHER.get(weathercode)}"
            
        return True, "Weather suitable for outdoor activities"
    
    def get_nearest_weather(self, target_datetime: str, timezone_str: str = 'UTC') -> Optional[dict]:
        """
        Get the nearest weather data to the target datetime
        """
        target_iso = self.dtHandler.to_iso_format(target_datetime, timezone_str)
        if not target_iso:
            return None
        
        # For hourly data, find the closest timestamp
        if 'hourly' in self.weatherData and 'time' in self.weatherData['hourly']:
            times = self.weatherData['hourly']['time']
            target_time = target_iso.split('T')[0] + 'T' + target_iso.split('T')[1][:5]
            
            # Find closest time
            closest_index = 0
            min_diff = float('inf')
            
            for i, time_str in enumerate(times):
                try:
                    time_dt = datetime.fromisoformat(time_str)
                    target_dt = datetime.fromisoformat(target_time)
                    diff = abs((time_dt - target_dt).total_seconds())
                    if diff < min_diff:
                        min_diff = diff
                        closest_index = i
                except ValueError:
                    continue
            
            return {
                'time': times[closest_index],
                'temperature_2m': self.weatherData['hourly']['temperature_2m'][closest_index],
                'precipitation': self.weatherData['hourly']['precipitation'][closest_index],
                'weathercode': self.weatherData['hourly']['weathercode'][closest_index]
            }
        
        return None


    @staticmethod
    def weather_code_to_string(code):
        """Convert weather code(s) to string description(s)"""
        if isinstance(code, list):
            str_list = []
            for c in code:
                if c not in CODE_TO_WEATHER:
                    str_list.append("Unknown")
                else:
                    str_list.append(CODE_TO_WEATHER[c])
            return str_list
        else:
            # Handle single integer
            if code not in CODE_TO_WEATHER:
                return "Unknown"
            else:
                return CODE_TO_WEATHER[code]



def get_weather_forecast(location: str="Australia", time: str = None):
    """Get weather forecast for a location"""
    try:
        if time and time != 'today' and time != 'tomorrow':
            raise ValueError("Invalid time parameter. Use 'today' or 'tomorrow' or None.")
        
        weather_utils = WeatherUtils(location)
        weather_data = weather_utils.weatherData
        
        today_date = datetime.now().strftime('%Y-%m-%d')
        tomorrow_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        if time == 'today':
            # Calculate duration in days
            # duration = (datetime.strptime(tomorrow_date, '%Y-%m-%d') - datetime.strptime(today_date, '%Y-%m-%d')).days   
            forecast_result = weather_utils.extract_weather_by_datetime(today_date, duration=24)
        elif time == 'tomorrow':
            forecast_result = weather_utils.extract_weather_by_datetime(tomorrow_date, duration=24)
        else:
            forecast_result = weather_data
            
        # convert the weather code
        if 'hourly' in forecast_result and 'weathercode' in forecast_result['hourly']:
            forecast_result['hourly']['weather_code'] = WeatherUtils.weather_code_to_string(forecast_result['hourly']['weathercode'])
            del forecast_result['hourly']['weathercode']  # Remove original field

        return {
            "location": location,
            "weather_data": forecast_result
        }
            
    except Exception as e:
        raise Exception(f"Weather forecast error: {str(e)}")
        


def check_outdoor_weather(location, year=None, month=None, day=None, hour=None, duration=1):
    """Check if weather is suitable for outdoor activities"""
    try:
        if year is None:
            year = datetime.now().year
            
        weather_utils = WeatherUtils(location)
            
        try:
            weather_data = weather_utils.get_weather_by_specific_period(
                month=month, day=day, hour=hour, minute=0, year=year, duration=duration
            )
        except TypeError:
            weather_data = weather_utils.get_weather_by_specific_period(
                month=month, day=day, hour=hour, minute=0, year=year
            )
        
        suitable, message = WeatherUtils.is_suitable(weather_data)
            
        return {
            "location": location,
            "suitable": suitable,
            "message": message,
            "weather_data": weather_data
        }
            
    except Exception as e:
        if "No results found for location" in str(e):
             return check_outdoor_weather("Australia", year, month, day, hour, duration)
        raise Exception(f"Outdoor weather check error: {str(e)}")
    



if __name__ == "__main__":

    weatherUtils = WeatherUtils("SA5063")
    # print(weatherUtils.weatherData)
    filtered_data = weatherUtils.get_weather_by_specific_period(month=9,day=2,hour=10,minute=20, duration=2)
    print(filtered_data)


