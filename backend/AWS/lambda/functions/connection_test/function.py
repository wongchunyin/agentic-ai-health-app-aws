import json
import urllib.request
import urllib.parse
import boto3
import os
import logging
import base64
import hmac
import hashlib
from datetime import datetime, timedelta, date
from decimal import Decimal
import logging
try:
    from message_helper import MsgHelper
    from cognito_helper import jwt_validation
    from config import config
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/aws/python'))
    from cognito_helper import jwt_validation
    from config import config
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/message/python'))
    from message_helper import MsgHelper

# Configure logging
logger = logging.getLogger()
logger.setLevel(config.LOGGER_LEVEL)

msg_helper = MsgHelper()

def lambda_handler(event, context):
    api_key = os.environ.get('API_KEY')
    logger.info(f"api_key encode test {api_key}")
    logger.info("Lambda handler started")
    logger.info(f"HTTP Method: {event.get('httpMethod')}")
    logger.info(f"Event keys: {list(event.keys())}")
    
    # Handle CORS preflight requests
    if event.get("httpMethod") == "OPTIONS":
        logger.info("Handling CORS preflight request - returning early")
        return msg_helper.success_response("") 
    
    # Log actual request details for POST requests
    if event.get("httpMethod") == "POST":
        logger.info("POST request received - processing")
        logger.info(f"Headers: {event.get('headers', {})}")
        logger.info(f"Body present: {bool(event.get('body'))}")
    else:
        logger.info(f"Non-POST request received: {event.get('httpMethod')}")
    
    try:
        logger.info("Starting jwt validation")
        authenticated_user = jwt_validation(event)
        if authenticated_user:
            return msg_helper.success_response(f"{authenticated_user} - API call is success.")
        return msg_helper.success_response("API call is success.")
    except Exception as e:
        logger.error(f"Error during authentication: {e}")
        return msg_helper.error_response(f"API call is failed. reason:{e}", 401)