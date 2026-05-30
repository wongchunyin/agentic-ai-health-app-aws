import json
import logging
from typing import Dict, Any
# Import from layers
try:
    from message_helper import MsgHelper
    from document_manager import DocumentManager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../layers/message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../layers/livewell-core/python'))
    from document_manager import DocumentManager

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    try:
        msg_helper = MsgHelper()
        
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        if not user_id:
            logger.error("User not authenticated")           
            return msg_helper.error_response('User not authenticated', 401)

        # Get assessment_id from path parameters
        path_params = event.get('pathParameters') or {}
        assessment_id = path_params.get('assessment_id')
        
        if not assessment_id:
            logger.error("Assessment ID not provided")
            return msg_helper.error_response('Assessment ID is required', 400)

        # Initialize DocumentManager
        doc_manager = DocumentManager()
        logger.info(f"Initialize DocumentManager success!")

        # Delete assessment using delete_document method
        result = doc_manager.delete_document(user_id, 'ASSESSMENT', assessment_id)
        logger.info("delete_document call completed")
        
        if result.get('success'):
            logger.info(f"Assessment deleted successfully for user_id: {user_id}, assessment_id: {assessment_id}")
            return msg_helper.success_response({
                'message': "Assessment deleted successfully",
                'assessment_id': assessment_id
            })
        else:
            return msg_helper.error_response(result.get('error', 'Failed to delete assessment'), 400)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return msg_helper.error_response(str(e), 500)