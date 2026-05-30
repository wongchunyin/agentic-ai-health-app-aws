import json
import logging
from typing import Dict, Any

# Import from layers
try:
    from dynamodb_helper import DynamoDBHelper
    from message_helper import MsgHelper
    from config import config
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/aws/python'))
    from dynamodb_helper import DynamoDBHelper
    from config import config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda function to retrieve leaderboard data from DynamoDB
    Returns list of users with country, score, city, username
    """
    msg_helper = MsgHelper()
    
    try:
        # Initialize DynamoDB helper
        db = DynamoDBHelper(config.DYNAMODB_TABLE_NAME)
        
        # Scan for all PROFILE items
        scan_result = db.scan_items(
            filter_expression="SK = :sk",
            expression_attribute_values={":sk": "PROFILE"}
        )
        
        if not scan_result['success']:
            return msg_helper.error_response('Failed to retrieve leaderboard data', 500)
        
        # Extract required fields and sort by score
        leaderboard = []
        for item in scan_result['data']:
            user_data = {
                'username': item.get('username', 'Anonymous'),
                'country': item.get('country', 'Unknown'),
                'city': item.get('city', 'Unknown'),
                'score': item.get('score', 0) or 0
            }
            leaderboard.append(user_data)
        
        # Sort by score descending
        leaderboard.sort(key=lambda x: x['score'], reverse=True)
        
        logger.info(f"Retrieved {len(leaderboard)} users for leaderboard")
        return msg_helper.success_response(data={'leaderboard': leaderboard})
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return msg_helper.error_response(str(e), 500)