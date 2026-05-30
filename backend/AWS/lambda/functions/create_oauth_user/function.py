import json
import logging
from datetime import datetime



try:
    from message_helper import MsgHelper
    from cognito_admin_helper import CognitoAdminHelper
    from config import config
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/aws/python'))
    from cognito_admin_helper import CognitoAdminHelper
    from config import config


# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

msg_helper = MsgHelper()
cognito_helper = CognitoAdminHelper()

def verify_google_token(access_token):
    """Verify Google access token and return user info"""
    try:
        import urllib.request
        import urllib.parse
        
        # Call Google's userinfo API to verify token
        url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
        
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                user_data = json.loads(response.read().decode('utf-8'))
                logger.info(f"Google token verified for user: {user_data.get('email')}")
                return user_data
            else:
                logger.error(f"Google token verification failed: {response.status}")
                return None
                
    except Exception as e:
        logger.error(f"Error verifying Google token: {str(e)}")
        return None

def lambda_handler(event, context):
    logger.info("Create OAuth User Lambda started")
    
    # Handle CORS preflight requests
    if event.get("httpMethod") == "OPTIONS":
        return msg_helper.handle_options_request('POST,OPTIONS')
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        email = body.get('email')
        name = body.get('name')
        provider = body.get('provider', 'oauth')
        google_access_token = body.get('google_access_token')  # Required for security
        
        if not email:
            return msg_helper.error_response("Email is required", 400)
            
        if not google_access_token:
            return msg_helper.error_response("Google access token is required", 400)
            
        # Verify Google token and extract user info
        google_user_info = verify_google_token(google_access_token)
        if not google_user_info:
            return msg_helper.error_response("Invalid Google access token", 401)
            
        # Ensure email matches Google token
        if google_user_info.get('email') != email:
            return msg_helper.error_response("Email mismatch with Google token", 403)
        
        # Create user using helper (with optimization for existing users)
        result = cognito_helper.create_oauth_user(email, name, provider)
        
        if result['success']:
            # Generate token for the created/existing user
            token_result = cognito_helper.generate_token_for_oauth_user(email, provider)
            
            if token_result['success']:
                return msg_helper.success_response({
                    "message": result['message'],
                    "username": result['username'],
                    "access_token": token_result['access_token'],
                    "token_type": token_result['token_type'],
                    "expires_in": token_result['expires_in']
                })
            else:
                # User created but token generation failed
                return msg_helper.success_response({
                    "message": result['message'],
                    "username": result['username'],
                    "warning": "User created but token generation failed"
                })
        else:
            return msg_helper.error_response(result['message'], 500)
        
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return msg_helper.error_response(f"Failed to create user: {str(e)}", 500)