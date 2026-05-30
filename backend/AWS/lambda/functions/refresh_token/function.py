import json
import logging
import urllib.request
import urllib.parse
from typing import Dict, Any

# Import from layers
try:
    from message_helper import MsgHelper, handle_cors
    from cognito_helper import authenticate
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/message/python'))
    from message_helper import MsgHelper, handle_cors
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/aws/python'))
    from cognito_helper import authenticate

logger = logging.getLogger()
logger.setLevel(logging.INFO)

from cognito_helper import authenticate

@authenticate
@handle_cors
def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda function to refresh Cognito access token using refresh token
    """
    msg_helper = MsgHelper()
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        refresh_token = body.get('refresh_token')
        
        if not refresh_token:
            return msg_helper.error_response('refresh_token is required', 400)
        
        # Cognito configuration
        COGNITO_DOMAIN = 'livewell.auth.us-east-1.amazoncognito.com'
        CLIENT_ID = '485ta0gjm4esu25dc4s3v377nu'
        
        # Prepare request data
        data = urllib.parse.urlencode({
            'grant_type': 'refresh_token',
            'client_id': CLIENT_ID,
            'refresh_token': refresh_token
        }).encode('utf-8')
        
        # Make request to Cognito
        req = urllib.request.Request(
            f"https://{COGNITO_DOMAIN}/oauth2/token",
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        with urllib.request.urlopen(req) as response:
            tokens = json.loads(response.read().decode('utf-8'))
            
            return msg_helper.format_api_gateway_response(200, {
                'access_token': tokens.get('access_token'),
                'expires_in': tokens.get('expires_in', 3600)
            })
            
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return msg_helper.error_response(str(e), 500)