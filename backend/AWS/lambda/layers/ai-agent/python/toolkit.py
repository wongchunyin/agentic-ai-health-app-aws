import json
import boto3
import base64
import os
import time
import uuid
from datetime import datetime, timedelta
import urllib.request
import socket
import logging
import uuid
try:
    from s3_helper import S3Helper
    from message_helper import MsgHelper
    from gemini_simple import GeminiSimple
    from dynamodb_helper import DynamoDBHelper
    from config import config
    from schemas import ActionTypeEnum
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../aws/python'))
    from s3_helper import S3Helper
    from dynamodb_helper import DynamoDBHelper
    from config import config
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../livewell-core/python'))
    from schemas import ActionTypeEnum
    from gemini_simple import GeminiSimple

# Import utils from local files
from aactt_utils import AACTTUtils
from weather_utils import WeatherUtils
from search_engine import SearchEngine

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class Toolkit:
    def __init__(self, user_id, chat_session_id):
        self.user_id = user_id
        self.chat_session_id = chat_session_id
        self.msg_helper = MsgHelper()
        self.livewell_table = DynamoDBHelper("livewell")
        self.transcribe = boto3.client('transcribe')
        # Removed lambda_client as we're calling AACTTUtils directly
        
    
 
    def get_weather_forecast(self, location="Australia"):
        """Get weather forecast for a location"""
        try:
            weather_utils = WeatherUtils(location)
            weather_data = weather_utils.weatherData
            
            # convert the weather code
            if 'hourly' in weather_data and 'weathercode' in weather_data['hourly']:
                weather_data['hourly']['weather_code'] = weather_utils.weather_code_to_string(weather_data['hourly']['weathercode'])
                del weather_data['hourly']['weathercode']  # Remove original field


            return {
                "location": location,
                "weather_data": weather_data
            }
            
        except Exception as e:
            raise Exception(f"Weather forecast error: {str(e)}")
    
    def check_outdoor_weather(self, location, year=None, month=None, day=None, hour=None, duration=1):
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
                return self.check_outdoor_weather("Australia", year, month, day, hour, duration)
            raise Exception(f"Outdoor weather check error: {str(e)}")
    


    def web_search(self, query):
        """Search web and return results using SearchEngine"""
        print(f"🔍 TOOLKIT_SEARCH_START: Initiating web search for query: '{query}'")
        try:
            search_engine = SearchEngine()
            results = search_engine.search(query)
            
            response = {
                "query": query,
                "results": results,
                "total_results": len(results)
            }
            
            print(f"✅ TOOLKIT_SEARCH_SUCCESS: Returning {len(results)} results to Gemini")
            print(f"📊 TOOLKIT_SEARCH_SUMMARY: Query='{query}', Results={len(results)}")
            
            return response
            
        except Exception as e:
            print(f"❌ TOOLKIT_SEARCH_ERROR: Search failed for query '{query}': {str(e)}")
            raise Exception(f"Google search error: {str(e)}")
    
    
    # def save_plan(self, plan_id: str, plan: dict):
    #     try:
    #         # saving the plan to dynamodb & S3
    #         key = {
    #             "pk" : f"{config.PK_PREFIX_USER}{self.user_id}",
    #             "sk" : f"{config.SK_PREFIX_AACTT_PLAN}{plan_id}"
    #         }

    #         resp = self.livewell_table.get_item(key)

    #         if resp.get('success') and 'data' in resp:
    #             # update the plan
    #             self.livewell_table.update_item(key)
    #         else:
    #             key["plan"] 
    #             self.livewell_table.create_item()
            
    #         bucket = S3Helper("livewell-aactt-bucket")
    #     except Exception as e:
    #         raise Exception(f"Plan saving error: {str(e)}")





# Global config instance
toolkit = Toolkit()

