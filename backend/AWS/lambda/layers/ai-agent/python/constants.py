# Constants for the Livewell application

# DynamoDB Table Names
LIVEWELL_TABLE = 'livewell'

# S3 Bucket Names
LIVEWELL_PLANS_BUCKET = 'livewell-plans'

# Action Types
ACTION_TYPES = {
    'AACTT_PLAN': 'aactt_plan',
    'USER_PROFILE': 'user_profile',
    'HEALTH_ASSESSMENT': 'health_assessment'
}

# Status Values
STATUS = {
    'ACTIVE': 'active',
    'INACTIVE': 'inactive',
    'PENDING': 'pending',
    'COMPLETED': 'completed'
}