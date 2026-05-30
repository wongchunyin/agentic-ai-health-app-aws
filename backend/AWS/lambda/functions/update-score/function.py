import json
import logging
from typing import Dict, Any

# Import from layers
try:
    from document_manager import DocumentManager
    from message_helper import MsgHelper
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/livewell-core/python'))
    from document_manager import DocumentManager

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda function to increase/decrease scores in user profile
    Query parameters: score_type, operation, amount
    """
    msg_helper = MsgHelper()
    
    try:
        # Get user_id from Cognito authorizer claims
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        if not user_id:
            return msg_helper.error_response('User not authenticated', 401)
        
        # Get query parameters
        query_params = event.get('queryStringParameters') or {}
        score_type = query_params.get('score_type')  # 'activity_score' or 'frailty_score'
        operation = query_params.get('operation')    # 'increase' or 'decrease'
        amount = query_params.get('amount', '1')     # default 1
        
        # Validate parameters
        if not score_type or score_type != 'activity_score':
            return msg_helper.error_response('Invalid score_type. Must be activity_score', 400)
        
        if not operation or operation not in ['increase', 'decrease']:
            return msg_helper.error_response('Invalid operation. Must be increase or decrease', 400)
        
        try:
            amount = int(amount)
        except ValueError:
            return msg_helper.error_response('Amount must be a valid integer', 400)
        
        # Initialize DocumentManager
        doc_manager = DocumentManager()
        
        # Update score
        result = doc_manager.update_score(user_id, score_type, operation, amount)
        
        if result['success']:
            logger.info(f"Score {operation}d successfully for user_id: {user_id}")
            return msg_helper.success_response(data=result)
        else:
            return msg_helper.error_response(result.get('error', 'Failed to update score'), 400)
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return msg_helper.error_response(str(e), 500)