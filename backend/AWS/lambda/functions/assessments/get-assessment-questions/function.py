import logging
from typing import Dict, Any
from datetime import datetime
# Import from layers
try:
    from message_helper import MsgHelper
    from assessment_utils import AssessmentUtils
    from schemas import FrailtyScoreTypeEnum
except ImportError as e:
    print(f"Import error in try block: {e}")
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../layers/message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../layers/ai-agent/python'))
    from assessment_utils import AssessmentUtils
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../layers/livewell-core/python'))
    from schemas import FrailtyScoreTypeEnum
    print("Imports successful in except block")
    

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    try:
        logger.info(f"Event: {event}")
        msg_helper = MsgHelper()
        logger.info("MsgHelper initialized")
        
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        logger.info(f"User ID: {user_id}")
        
        if not user_id:
            logger.error("User not authenticated")           
            return msg_helper.error_response('User not authenticated', 401)
        
        # Get assessment type from path parameters
        assessment_type = event.get('pathParameters', {}).get('type')
        logger.info(f"Assessment type from path: {assessment_type}")
        
        if not assessment_type:
            logger.error("Assessment type not provided")
            return msg_helper.error_response('Assessment type is required', 400)
        
        # Get survey based on type
        logger.info(f"Comparing {assessment_type.upper()} with {FrailtyScoreTypeEnum.FRAIL_SCALE.value}")
        
        if assessment_type.upper() == FrailtyScoreTypeEnum.FRAIL_SCALE.value:
            logger.info("Getting FRAIL survey")
            survey = AssessmentUtils.get_FRAIL_survey()
        elif assessment_type.upper() == FrailtyScoreTypeEnum.ROCKWOOD_MITNITSKI.value:
            logger.info("Getting Rockwood-Mitnitski survey")
            survey = AssessmentUtils.get_rockwood_mitnitski_survey()
        else:
            logger.error(f"Unsupported assessment type: {assessment_type}")
            return msg_helper.error_response(f'Unsupported assessment type: {assessment_type}', 400)
        
        if not survey:
            logger.error("Survey not found")
            return msg_helper.error_response('Survey not found', 404)
        
        return msg_helper.success_response(survey, methods='GET, OPTIONS')
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return msg_helper.error_response(str(e), 500)