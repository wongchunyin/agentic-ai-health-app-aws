import json
import base64
from datetime import datetime
import logging
from typing import Dict, Optional
import os
from functools import wraps
from config import Config

# Import message_helper with fallback
try:
    from message_helper import MsgHelper
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../message/python'))
    from message_helper import MsgHelper


# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class CognitoJWTError(Exception):
    """Custom exception for Cognito JWT validation errors"""
    pass

class CognitoHelper:
    """Helper class for Cognito operations"""
    
    def __init__(self):
        pass
    
    def get_user_login_info(self, user_id: str, token: str = None) -> Dict:
        """Get user login information from JWT token auth_time"""
        try:
            if not token:
                return {
                    "success": False,
                    "error": "No token provided"
                }
            
            # Extract auth_time from token
            user_info = get_user_from_token(token)
            auth_time = user_info.get('auth_time', 0)
            
            if auth_time > 0:
                last_login = datetime.fromtimestamp(auth_time)
                hours_since_login = (datetime.utcnow() - last_login).total_seconds() / 3600
                
                result = {
                    "success": True,
                    "user_id": user_id,
                    "hours_since_login": round(hours_since_login, 1)
                }
                
                # Only include engagement message for inactive users (72+ hours)
                if hours_since_login > 168:  # 7+ days
                    result["message"] = "Welcome back! Your health journey is important - let's make this a regular habit."
                elif hours_since_login > 72:  # 3+ days
                    result["message"] = "I've missed you! Regular check-ins help maintain your wellness journey."
                
                return result
            else:
                return {
                    "success": False,
                    "error": "Invalid auth_time in token"
                }
                
        except Exception as e:
            logger.error(f"Error getting user login info: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

def extract_token_from_event(event: Dict) -> Optional[str]:
    """Extract JWT token from Lambda event"""
    headers = event.get('headers', {})
    
    # Handle case-insensitive headers
    for key, value in headers.items():
        if key.lower() == 'authorization':
            if value.startswith('Bearer '):
                return value[7:]
            return value
    
    # Try query string parameters
    query_params = event.get('queryStringParameters') or {}
    return query_params.get('token')

def validate_cognito_token(token: str, region: str = None, user_pool_id: str = None) -> Dict:
    """Basic JWT token validation without signature verification"""
    try:
        # Split token into parts
        parts = token.split('.')
        if len(parts) != 3:
            raise CognitoJWTError("Invalid token format")
        
        # Decode payload
        payload_b64 = parts[1]
        # Add padding if needed
        payload_b64 += '=' * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        
        logger.info(f"Raw token parts count: {len(parts)}")
        logger.info(f"Token payload keys: {list(payload.keys())}")
        logger.info(f"Token payload: {payload}")
        
        # Basic validations
        current_time = datetime.utcnow().timestamp()
        
        # Check expiration with detailed logging
        token_exp = payload.get('exp', 0)
        
        # Handle invalid expiration timestamps
        if token_exp <= 0:
            logger.error(f"Token missing exp field. Available fields: {list(payload.keys())}")
            raise CognitoJWTError("Invalid token: Missing or invalid expiration time")
            
        logger.info(f"Token expiration: {token_exp} ({datetime.fromtimestamp(token_exp)})")
        logger.info(f"Current time: {current_time} ({datetime.fromtimestamp(current_time)})")
        logger.info(f"Time difference: {token_exp - current_time} seconds")
        
        if token_exp < current_time:
            raise CognitoJWTError(f"Token has expired. Exp: {datetime.fromtimestamp(token_exp)}, Now: {datetime.fromtimestamp(current_time)}")
        
        # Check issuer
        _region = region or Config.COGNITO_REGION
        _user_pool_id = user_pool_id or Config.COGNITO_USER_POOL_ID
        expected_iss = f"https://cognito-idp.{_region}.amazonaws.com/{_user_pool_id}"
        actual_iss = payload.get('iss')
        
        logger.info(f"Expected issuer: {expected_iss}")
        logger.info(f"Actual issuer: {actual_iss}")
        
        if actual_iss != expected_iss:
            raise CognitoJWTError(f"Invalid issuer. Expected: {expected_iss}, Got: {actual_iss}")
        
        # Check token use
        if payload.get('token_use') not in ['access', 'id']:
            raise CognitoJWTError("Invalid token use")
        
        logger.info(f"Token validated successfully for user: {payload.get('username', 'unknown')}")
        logger.info(f"Token valid for {int((token_exp - current_time) / 60)} more minutes")
        logger.info(f"Token issuer validation passed")
        logger.info(f"Full token payload: {payload}")
        return payload
        
    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}")
        raise CognitoJWTError(f"Token validation failed: {str(e)}")

def get_user_from_token(token: str, region: str = None, user_pool_id: str = None) -> Dict:
    """Extract user information from Cognito JWT token"""
    claims = validate_cognito_token(token, region, user_pool_id)
    
    return {
        'username': claims.get('username', ''),
        'sub': claims.get('sub', ''),
        'email': claims.get('email', ''),
        'email_verified': claims.get('email_verified', False),
        'groups': claims.get('cognito:groups', []),
        'token_use': claims.get('token_use', ''),
        'client_id': claims.get('client_id', ''),
        'exp': claims.get('exp', 0),
        'iat': claims.get('iat', 0),
        'auth_time': claims.get('auth_time', 0)
    }

def jwt_validation(event: Dict):
    try:
        logger.info("Starting JWT validation")
        logger.info(f"Event headers: {event.get('headers', {})}")
        logger.info(f"Event method: {event.get('httpMethod')}")
        logger.info(f"Full event keys: {list(event.keys())}")

        # Extract and validate JWT token
        jwt_token = extract_token_from_event(event)
        logger.info(f"Token extraction result: {'Found' if jwt_token else 'Not found'}")
        if jwt_token:
            logger.info(f"Token length: {len(jwt_token)}")
            logger.info(f"Token starts with: {jwt_token[:50]}...")
        
        if not jwt_token:
            logger.error("JWT token extraction failed")
            logger.error(f"Available headers: {list(event.get('headers', {}).keys())}")
            logger.error(f"Header values: {event.get('headers', {})}")
            raise CognitoJWTError("JWT token not found in request")
        
        logger.info(f"JWT token extracted, length: {len(jwt_token)}")


                # Get user info from token (includes validation)
        try:
            user_info = get_user_from_token(jwt_token)
            authenticated_user = user_info.get('username', 'unknown')
            logger.info(f"Authenticated user: {authenticated_user}")
            logger.info("JWT validation completed successfully")

            return authenticated_user
        except CognitoJWTError as e:
            logger.error(f"JWT validation failed: {str(e)}")
            raise ValueError(f"Invalid token: {str(e)}")

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        raise CognitoJWTError("Invalid JSON format")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise CognitoJWTError(f"An error occurred: {str(e)}")



def authenticate(func):
    """Decorator to handle authentication and request logging"""
    @wraps(func)
    def wrapper(event, context):
        msg_helper = MsgHelper()
        
        # Log request details
        method = event.get("httpMethod")
        logger.info(f"{method} request received - processing")
        logger.info(f"Headers: {event.get('headers', {})}")
        logger.info(f"Body present: {bool(event.get('body'))}")
        logger.info(f"Raw body: {event.get('body')}")
        logger.info(f"Query params: {event.get('queryStringParameters')}")
        logger.info(f"Path params: {event.get('pathParameters')}")
        logger.info(f"Full event structure: {json.dumps(event, default=str, indent=2)}")
        # logger.info(f"Path Parameters: {event.get('pathParameters', {})}")
        
        # Skip authentication for OPTIONS requests (CORS preflight)
        if method == "OPTIONS":
            logger.info("Skipping authentication for OPTIONS request")
            return func(event, context)
        
        # Handle authentication for all other requests
        try:
            authenticated_user = jwt_validation(event)
            if not authenticated_user:
                return msg_helper.error_response('Unauthorized', 401)
            # Add user to event for use in function
            event['authenticated_user'] = authenticated_user
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return msg_helper.error_response('Unauthorized', 401)
        
        return func(event, context)
    return wrapper
