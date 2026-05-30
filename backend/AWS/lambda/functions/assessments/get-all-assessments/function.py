import json
import logging
from message_helper import MsgHelper
from document_manager import DocumentManager

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        msg_helper = MsgHelper()
        doc_manager = DocumentManager()
        
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        if not user_id:
            logger.error("User not authenticated")
            return msg_helper.error_response('User not authenticated', 401)
        
        # Get status filter from query parameters
        query_params = event.get('queryStringParameters') or {}
        status = query_params.get('status', 'ALL')
        
        # Validate status parameter - use enum values from schemas (case-insensitive)
        from schemas import AssessmentStatusEnum
        valid_statuses = ['ALL'] + [e.value for e in AssessmentStatusEnum]
        
        # Convert to lowercase for validation and DynamoDB query
        if status.upper() == 'ALL':
            status = 'ALL'
        elif status.lower() in [e.value for e in AssessmentStatusEnum]:
            status = status.lower()
        else:
            return msg_helper.error_response(f'Invalid status. Must be one of: {valid_statuses}', 400)
        
        result = doc_manager.get_multiple_assessments(user_id, status)
        
        if result['success']:
            return msg_helper.success_response(result['data'])
        else:
            return msg_helper.error_response(result.get('error', 'Failed to get assessments'), 400)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return msg_helper.error_response(str(e), 500)