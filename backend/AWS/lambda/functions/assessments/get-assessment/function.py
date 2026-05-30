import json
import logging
from typing import Dict, Any
import uuid
from datetime import datetime
# Import from layers
try:
    from message_helper import MsgHelper
    from schemas import FrailtyScoreTypeEnum, AssessmentStatusEnum, FrailScale, FrailtyAssessmentHistory, Metadata, Metadata
    from document_manager import DocumentManager
    from assessment_utils import AssessmentUtils
    from utils import isEmptyStr
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../layers/message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../layers/livewell-core/python'))
    from schemas import FrailtyScoreTypeEnum
    from document_manager import DocumentManager, FrailScale, AssessmentStatusEnum 
    from utils import isEmptyStr
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../layers/ai-agent/python'))
    from assessment_utils import AssessmentUtils


logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    try:
        msg_helper = MsgHelper()
        # Initialize DocumentManager
        doc_manager = DocumentManager()
        logger.info(f"Initialize DocumentManager success!")

        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        if not user_id:
            logger.error("User not authenticated")           
            return msg_helper.error_response('User not authenticated', 401)

        # Get assessment_id from path parameters - required for single assessment
        path_params = event.get('pathParameters') or {}
        assessment_id = path_params.get('assessment_id')
        
        if not assessment_id:
            return msg_helper.error_response('Assessment ID is required', 400)

        # Get single assessment using get_document method
        resp = doc_manager.get_document(user_id, 'ASSESSMENT', assessment_id)
    
        if not resp['success']:
            return msg_helper.error_response(resp.get('error', f'Failed to get assessment with assessment id:{assessment_id}'), 400)
        else:
            return msg_helper.success_response(resp['data'])
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return msg_helper.error_response(str(e), 500)