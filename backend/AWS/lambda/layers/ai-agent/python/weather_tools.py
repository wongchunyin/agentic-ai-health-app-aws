from langchain_core.tools import tool
from weather_utils import get_weather_forecast

def get_weather_today_forecast(location):
    """Today weather forecast using local weather utils"""
    try:
        from weather_utils import WeatherUtils
        result = get_weather_forecast(location, "today")
        
        if isinstance(result, dict) and "weather_data" in result:
            weather_data = result["weather_data"]
            if "hourly" in weather_data and "weathercode" in weather_data["hourly"]:
                weather_codes = weather_data["hourly"]["weathercode"]
                weather_data["hourly"]["weather_description"] = WeatherUtils.weather_code_to_string(weather_codes)
        
        return result
    except Exception as e:
        return f"Weather forecast error: {str(e)}"

def get_weather_tomorrow_forecast(location):
    """Tomorrow weather forecast using local weather utils"""
    try:
        from weather_utils import WeatherUtils
        result = get_weather_forecast(location, "tomorrow")
        
        if isinstance(result, dict) and "weather_data" in result:
            weather_data = result["weather_data"]
            if "hourly" in weather_data and "weathercode" in weather_data["hourly"]:
                weather_codes = weather_data["hourly"]["weathercode"]
                weather_data["hourly"]["weather_description"] = WeatherUtils.weather_code_to_string(weather_codes)
        
        return result
    except Exception as e:
        return f"Weather forecast error: {str(e)}"

@tool
def get_weather_today(location: str) -> dict:
    """Get today's weather forecast for outdoor activity planning."""
    try:
        forecast_data = get_weather_today_forecast(location)
        if isinstance(forecast_data, str) and "error" in forecast_data.lower():
            return {
                "success": False,
                "location": location,
                "forecast": None,
                "error": forecast_data
            }
        return {
            "success": True,
            "location": location,
            "forecast": forecast_data,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "location": location,
            "forecast": None,
            "error": str(e)
        }

@tool
def get_weather_tomorrow(location: str) -> dict:
    """Get tomorrow's weather forecast for planning ahead."""
    try:
        forecast_data = get_weather_tomorrow_forecast(location)
        if isinstance(forecast_data, str) and "error" in forecast_data.lower():
            return {
                "success": False,
                "location": location,
                "forecast": None,
                "error": forecast_data
            }
        return {
            "success": True,
            "location": location,
            "forecast": forecast_data,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "location": location,
            "forecast": None,
            "error": str(e)
        }

def get_weather_tools():
    """Get all weather-related tools"""
    return [
        get_weather_today,
        get_weather_tomorrow
    ]