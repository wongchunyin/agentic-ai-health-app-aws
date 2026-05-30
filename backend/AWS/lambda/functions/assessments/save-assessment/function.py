import json
import logging
from typing import Dict, Any
import uuid
from datetime import datetime
# Import from layers
try:
    from message_helper import MsgHelper
    from schemas import FrailtyScoreTypeEnum, AssessmentStatusEnum, FrailScale, FrailtyAssessmentHistory, RockwoodMitnitski
    from document_manager import DocumentManager
    from assessment_utils import AssessmentUtils
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../layers/message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../layers/livewell-core/python'))
    from schemas import FrailtyScoreTypeEnum, RockwoodMitnitski
    from document_manager import DocumentManager, FrailScale, AssessmentStatusEnum 
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../../layers/ai-agent/python'))
    from assessment_utils import AssessmentUtils

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    try:
        msg_helper = MsgHelper()
       
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        if not user_id:
            logger.error("User not authenticated")           
            return msg_helper.error_response('User not authenticated', 401)

        body = json.loads(event.get('body', '{}'))

        # Create assessment object with validation
        assessment_type = body.get('assessment_type')
        valid_types = [e.value for e in FrailtyScoreTypeEnum]
        if assessment_type not in valid_types:
            raise ValueError(f"Invalid assessment_type: {assessment_type}. Valid types: {valid_types}")
        logger.info(f"Received Assessment Type: {assessment_type}")
        
        assessment_data = body.get('assessment_data')
        logger.info(f"Received Assessment: {assessment_data}")
        if not assessment_data:
            return msg_helper.error_response('Assessment data is required', 400)
        if assessment_type == FrailtyScoreTypeEnum.FRAIL_SCALE.value:
            new_assessment = FrailScale(**assessment_data)
        elif assessment_type == FrailtyScoreTypeEnum.ROCKWOOD_MITNITSKI.value:
            new_assessment = RockwoodMitnitski(**assessment_data)

        # Initialize DocumentManager
        doc_manager = DocumentManager()
        logger.info(f"Initialize DocumentManager success!")

        # Generate new assessment ID for new assessment
        assessment_id = str(uuid.uuid4())  
        logger.info(f"Generating new assessment ID: {assessment_id}")
        latest_assessment = new_assessment

        score = AssessmentUtils.calculate_score(assessment_type, latest_assessment.dict())
        logger.info(f"Score: {score}")
        interpret_score = AssessmentUtils.interpret_score(assessment_type, score)
        logger.info(f"Interpret Score: {interpret_score}")
        logger.info(f"")
        # create Frailty Assessment History with metadata
        fah_json = {
            'assessment_id': assessment_id,
            'timestamp': datetime.utcnow().isoformat(),
            'assessment_type': assessment_type,
            'score': score,
            'assessment_data': latest_assessment.dict()
        }
        # Validate with FrailtyAssessmentHistory
        fah = FrailtyAssessmentHistory(**fah_json)

        # Set assessment_result based on status
        if fah.status == AssessmentStatusEnum.COMPLETED.value:
            fah.assessment_result = interpret_score
        else:
            fah.assessment_result = None
            interpret_score = {'message': 'Result is not ready.', 'reason': 'assessment incomplete.'}

        logger.info(f"FrailtyAssessmentHistory created with ID: {fah.assessment_id}")

        # Create assessment document - use raw JSON to avoid Pydantic serialization issues
        result = doc_manager.save_assessment(user_id, assessment_id, fah)
        logger.info("save_assessment call completed")
        
        if result['success']:
            logger.info(f"Assessment saved successfully for user_id: {user_id}")
            return msg_helper.success_response({
                'message': "Assessment created successfully",
                'assessment_id': result['assessment_id'],
                'assessment_result' : interpret_score
            })
        else:
            return msg_helper.error_response(result.get('error', 'Failed to save assessment'), 400)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return msg_helper.error_response(str(e), 500)