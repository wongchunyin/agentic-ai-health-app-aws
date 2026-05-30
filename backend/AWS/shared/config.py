import os
from os import environ
import boto3 
from pathlib import Path

class Config:
    AWS_REGION = environ.get('AWS_REGION', 'us-east-1')
    AWS_PROFILE = environ.get('AWS_PROFILE', 'account2')  # Default profile name
    LAMBDA_REGION = environ.get('LAMBDA_REGION', 'us-east-1') 


    # Get the absolute path of this config file
    CONFIG_PATH = Path(__file__).resolve()

    # Project root is 3 levels up from shared/config.py
    # backend/AWS/shared/config.py -> backend/AWS/shared -> backend/AWS -> backend/
    PROJECT_ROOT = CONFIG_PATH.parent.parent.parent

    # Define base paths
    AWS_ROOT = CONFIG_PATH.parent.parent  # backend/AWS
    DYNAMODB_ROOT = AWS_ROOT / "dynamodb"
    S3_ROOT = AWS_ROOT / "S3"
    IAM_ROOT = AWS_ROOT / "iam"
    COGNITO_ROOT = AWS_ROOT / "cognito"
    LAMBDA_ROOT = AWS_ROOT / "lambda"
    LAYERS_ROOT = LAMBDA_ROOT / "layers"
    FUNCTIONS_ROOT = LAMBDA_ROOT / "functions"

    @classmethod
    def get_lambda_layer_path(cls, layer_name: str) -> Path:
        """Get the path to a specific layer"""
        return cls.LAYERS_ROOT / layer_name
    @classmethod
    def get_lambda_function_path(cls, function_name: str) -> Path:
        """Get the path to a specific function"""
        return cls.FUNCTIONS_ROOT / function_name
    @classmethod
    def get_lambda_function_zip_path(cls, function_name: str) -> Path:
        """Get the path to a specific function's zip file"""
        return cls.FUNCTIONS_ROOT / f"{cls, function_name}.zip"
    @classmethod
    def get_lambda_layer_zip_path(cls, layer_name: str, deploy_dir: Path = None) -> Path:
        """Get the zip path for a layer"""
        if deploy_dir is None:
            deploy_dir = cls.CONFIG_PATH.parent  # shared directory by default
        
        return deploy_dir / f"{layer_name.replace('_', '-')}-layer.zip"


    @classmethod
    def get_client(cls, service, region_name: str = None):
        """Initialize client with profile if specified"""
        session = boto3.Session(
            region_name=cls.AWS_REGION or region_name, # Use provided region or default
            profile_name=cls.AWS_PROFILE  # Use your pre-defined profile name
        )
        return session.client(service)
    
    @classmethod
    def get_account_id(cls):
        """Get AWS Account ID using STS"""
        sts_client = cls.get_client('sts')
        return sts_client.get_caller_identity()['Account']
    



    # Cognito Configuration
    
    # User Pool
    USER_POOL_NAME = os.getenv('USER_POOL_NAME', 'LiveWellAuthPool')
    
    # Email Configuration
    EMAIL_FROM = os.getenv('EMAIL_FROM', 'livewell-b@tutamail.com')  # Default sender email, may need to be verified in SES
    EMAIL_REPLY_TO = os.getenv('EMAIL_REPLY_TO', 'livewell-b@tutamail.com')
    
    # Platform-Specific Configs
    CLIENTS = {
        'web': {
            'name': 'WebClient',
            'callback_urls': [
                os.getenv('WEB_CALLBACK_URL', 'http://localhost:3000/auth/callback'),
                'https://yourdomain.com/auth/callback'  # Production
            ],
            'logout_urls': [
                os.getenv('WEB_LOGOUT_URL', 'http://localhost:3000'),
                'https://yourdomain.com'  # Production
            ],
            'token_config': {
                'AccessTokenValidity': 60,  # minutes
                'IdTokenValidity': 60,
                'RefreshTokenValidity': 30   # days
            }
        },
        'mobile': {
            'name': 'MobileClient',
            'callback_urls': [
                os.getenv('MOBILE_CALLBACK_URL', 'yourapp://auth'),
                'yourprodapp://auth'  # Production app scheme
            ],
            'logout_urls': [
                'yourapp://logout'
            ],
            'token_config': {
                'AccessTokenValidity': 1440,  # 24 hours
                'IdTokenValidity': 1440,
                'RefreshTokenValidity': 90    # days
            }
        }
    }

    # S3 bucket configuration
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'livewell-bucket')
    S3_REGION = os.getenv('S3_REGION', 'us-east-1')
    

    # DynamoDB configuration
    DB_REGION = os.getenv('DB_REGION', 'us-east-1')
    DB_TABLE_NAME = os.getenv('DB_TABLE_NAME', 'livewell')