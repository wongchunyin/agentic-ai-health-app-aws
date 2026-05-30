import json
import logging
from datetime import date, timedelta, datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    from weather_utils import get_weather_forecast
    from message_helper import MsgHelper
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/ai-agent/python'))
    from weather_utils import get_weather_forecast
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/message/python'))
    from message_helper import MsgHelper

msg_helper = MsgHelper()


def lambda_handler(event, context):
    try:
        logger.info(f"Event received: {json.dumps(event)}")
        
        # Extract parameters from query string (GET method)
        query_params = event.get('queryStringParameters') or {}
        location = query_params.get('location', "Australia")
        time = query_params.get('time', None)
        
        logger.info(f"Parameters - location: {location}, time: {time}")

        data = get_weather_forecast(location, time)
        logger.info(f"Weather data retrieved: {data}")

        return msg_helper.success_response(data)

    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return msg_helper.error_response(str(e), 400)
        


# For direct testing without API Gateway
if __name__ == "__main__":
    # local testing
    logger.info("testing")