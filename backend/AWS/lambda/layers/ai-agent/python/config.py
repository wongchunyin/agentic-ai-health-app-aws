import os

# DynamoDB Configuration
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'livewell')

# S3 Configuration
S3_CHAT_HISTORY_BUCKET = os.environ.get('S3_CHAT_HISTORY_BUCKET', 'livewell-chathistory')
S3_PROFILES_BUCKET = os.environ.get('S3_PROFILES_BUCKET', 'livewell-profiles')
S3_PLANS_BUCKET = os.environ.get('S3_PLANS_BUCKET', 'livewell-plans')

# Document Types
DOC_TYPE_PROFILE = 'profile'
DOC_TYPE_PLAN = 'plan'
DOC_TYPE_ASSESSMENT = 'assessment'

# AWS Region
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# OpenSearch Configuration
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT', 'https://search-livewell-medical-search.us-east-1.es.amazonaws.com')

# Google API Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')