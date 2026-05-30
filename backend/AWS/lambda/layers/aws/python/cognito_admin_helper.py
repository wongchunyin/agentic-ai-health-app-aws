import boto3
import logging
import json
from datetime import datetime
from typing import Dict, Optional, List
from config import config, Config

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class CognitoAdminHelper:
    """Helper class for Cognito admin operations"""
    
    def __init__(self, region: str = None, user_pool_id: str = None):
        self.region = region or config.COGNITO_REGION
        self.user_pool_id = user_pool_id or config.COGNITO_USER_POOL_ID
        self.client = boto3.client('cognito-idp', region_name=self.region)
    
    def create_oauth_user(self, email: str, name: str = None, provider: str = 'oauth') -> Dict:
        """Create an OAuth user in Cognito User Pool (Google, Facebook, Apple, etc.)"""
        try:
            response = self.client.admin_create_user(
                UserPoolId=self.user_pool_id,
                Username=email,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'email_verified', 'Value': 'true'},
                    {'Name': 'name', 'Value': name or email}
                ],
                MessageAction='SUPPRESS',  # Don't send welcome email
                TemporaryPassword='TempPass123!' + str(datetime.now().microsecond)
            )
            
            logger.info(f"Successfully created {provider} user: {email}")
            return {
                'success': True,
                'message': 'User created successfully',
                'username': email,
                'data': response
            }
            
        except self.client.exceptions.UsernameExistsException:
            logger.info(f"User already exists: {email}")
            return {
                'success': True,
                'message': 'User already exists',
                'username': email
            }
            
        except Exception as e:
            logger.error(f"Error creating {provider} user: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to create user: {str(e)}',
                'error': str(e)
            }
    
    def get_user(self, username: str) -> Dict:
        """Get user details from Cognito"""
        try:
            response = self.client.admin_get_user(
                UserPoolId=self.user_pool_id,
                Username=username
            )
            
            return {
                'success': True,
                'data': response
            }
            
        except self.client.exceptions.UserNotFoundException:
            return {
                'success': False,
                'message': 'User not found'
            }
            
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to get user: {str(e)}',
                'error': str(e)
            }
    
    def delete_user(self, username: str) -> Dict:
        """Delete user from Cognito"""
        try:
            self.client.admin_delete_user(
                UserPoolId=self.user_pool_id,
                Username=username
            )
            
            logger.info(f"Successfully deleted user: {username}")
            return {
                'success': True,
                'message': 'User deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to delete user: {str(e)}',
                'error': str(e)
            }
    
    def list_users(self, limit: int = 10) -> Dict:
        """List users in the User Pool"""
        try:
            response = self.client.list_users(
                UserPoolId=self.user_pool_id,
                Limit=limit
            )
            
            return {
                'success': True,
                'data': response
            }
            
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to list users: {str(e)}',
                'error': str(e)
            }
    
    def generate_token_for_oauth_user(self, email: str, provider: str = 'oauth') -> Dict:
        """Generate JWT token for OAuth users (Google, Facebook, Apple, etc.)"""
        try:
            import time
            import base64
            import hmac
            import hashlib
            
            # Create a simple JWT-like token for Google users
            header = {
                "alg": "HS256",
                "typ": "JWT"
            }
            
            payload = {
                "sub": email,
                "username": email,
                "email": email,
                "loginType": provider,
                "iss": f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}",
                "iat": int(time.time()),
                "exp": int(time.time()) + 3600,  # 1 hour expiry
                "token_use": "access",
                "client_id": config.COGNITO_CLIENT_ID or f"{provider}-client"
            }
            
            # Encode header and payload
            header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
            payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
            
            # Get JWT secret from environment variable
            import os
            secret = os.environ.get('JWT_SECRET', 'fallback_secret_key_change_in_production')
            if secret == 'fallback_secret_key_change_in_production':
                logger.warning('Using fallback JWT secret - set JWT_SECRET environment variable')
            signature_input = f"{header_b64}.{payload_b64}"
            signature = base64.urlsafe_b64encode(
                hmac.new(secret.encode(), signature_input.encode(), hashlib.sha256).digest()
            ).decode().rstrip('=')
            
            # Combine to create JWT
            jwt_token = f"{header_b64}.{payload_b64}.{signature}"
            
            logger.info(f"Generated token for {provider} user: {email}")
            return {
                'success': True,
                'access_token': jwt_token,
                'token_type': 'Bearer',
                'expires_in': 3600,
                'username': email
            }
            
        except Exception as e:
            logger.error(f"Error generating token for {provider} user: {str(e)}")
            return {
                'success': False,
                'message': f'Failed to generate token: {str(e)}',
                'error': str(e)
            }