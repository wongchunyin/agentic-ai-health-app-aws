import json
from datetime import date, timedelta, datetime

try:
    from weather_utils import check_outdoor_weather
    from message_helper import MsgHelper
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/ai-agent/python'))
    from weather_utils import check_outdoor_weather
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/message/python'))
    from message_helper import MsgHelper

msg_helper = MsgHelper()


def lambda_handler(event, context):
    try:
        # Extract parameters from query string (GET method)
        query_params = event.get('queryStringParameters') or {}
        location = query_params.get('location')
        year = int(query_params.get('year', datetime.now().year))
        month = int(query_params.get('month'))
        day = int(query_params.get('day'))
        hour = int(query_params.get('hour'))
        duration = int(query_params.get('duration', 1))

        result = check_outdoor_weather(location, year, month, day, hour, duration)
        
        return msg_helper.success_response(result)

    except Exception as e:
        return msg_helper.error_response(str(e), 400)
        


# For direct testing without API Gateway
if __name__ == "__main__":
    # for local testing
    test_event = { 
    "location": "SA 5000",
    "year": 2025,
    "month": 9,
    "day": 2,
    "hour": 10,
    "duration": 2
}
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))


