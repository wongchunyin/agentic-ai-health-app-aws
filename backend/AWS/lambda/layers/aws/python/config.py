"""
Shared Configuration for AWS Lambda Layers
==========================================

This module provides centralized configuration management for all AWS Lambda layers.
Environment variables are loaded with fallback defaults.

Usage:
    from config import Config
    
    config = Config()
    region = config.AWS_REGION
    user_pool_id = config.COGNITO_USER_POOL_ID
"""

import os
from typing import Optional
import logging

class Config:
    """Centralized configuration for AWS Lambda layers"""

    # AWS Configuration
    AWS_REGION: str = os.getenv('AWS_REGION', 'us-east-1')
    AWS_ACCOUNT_ID: Optional[str] = os.getenv('AWS_ACCOUNT_ID')
    
    # Cognito Configuration
    COGNITO_REGION: str = os.getenv('COGNITO_REGION', AWS_REGION)
    COGNITO_USER_POOL_ID: str = os.getenv('COGNITO_USER_POOL_ID', 'us-east-1_tjhTbNShM')
    COGNITO_CLIENT_ID: Optional[str] = os.getenv('COGNITO_CLIENT_ID')
    
    # DynamoDB Configuration
    DYNAMODB_TABLE_NAME: str = os.getenv('DYNAMODB_TABLE_NAME', 'livewell')
    DYNAMODB_REGION: str = os.getenv('DYNAMODB_REGION', AWS_REGION)
    
    # S3 Configuration
    S3_BUCKET_NAME: str = os.getenv('S3_BUCKET_NAME', 'livewell-bucket')
    S3_CHAT_HISTORY_BUCKET: str = os.getenv('S3_CHAT_HISTORY_BUCKET', 'livewell-chathistory')
    S3_AUDIO_BUCKET: str = os.getenv('S3_AUDIO_BUCKET', 'livewell-audio-bucket')
    S3_REGION: str = os.getenv('S3_REGION', AWS_REGION)
    
    # Gemini API Configuration
    GEMINI_API_KEY: Optional[str] = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL: str = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
    
    # Application Configuration
    # LOGGER_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOGGER_LEVEL: str = os.getenv('LOGGER_LEVEL', logging.DEBUG)
    # ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'dev')
    
    @classmethod
    def get_cognito_config(cls) -> dict:
        """Get Cognito configuration as dictionary"""
        return {
            'region': cls.COGNITO_REGION,
            'user_pool_id': cls.COGNITO_USER_POOL_ID,
            'client_id': cls.COGNITO_CLIENT_ID
        }
    
    @classmethod
    def get_dynamodb_config(cls) -> dict:
        """Get DynamoDB configuration as dictionary"""
        return {
            'table_name': cls.DYNAMODB_TABLE_NAME,
            'region': cls.DYNAMODB_REGION
        }
    
    @classmethod
    def get_s3_config(cls) -> dict:
        """Get S3 configuration as dictionary"""
        return {
            'bucket_name': cls.S3_BUCKET_NAME,
            'chat_history_bucket': cls.S3_CHAT_HISTORY_BUCKET,
            'audio_bucket': cls.S3_AUDIO_BUCKET,
            'region': cls.S3_REGION
        }
    
    @classmethod
    def get_gemini_config(cls) -> dict:
        """Get Gemini API configuration as dictionary"""
        return {
            'api_key': cls.GEMINI_API_KEY,
            'model': cls.GEMINI_MODEL
        }


# Global config instance
config = Config()