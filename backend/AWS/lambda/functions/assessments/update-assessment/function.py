import json
import logging
from typing import Dict, Any
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

        # Get assessment_id from path parameters
        path_params = event.get('pathParameters') or {}
        assessment_id = path_params.get('assessment_id')
        
        if not assessment_id:
            logger.error("Assessment ID not provided")
            return msg_helper.error_response('Assessment ID is required', 400)

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
        
        # Keep illnesses as list for FrailScale to preserve individual selections
        # The schema now handles both list and integer formats
        
        if assessment_type == FrailtyScoreTypeEnum.FRAIL_SCALE.value:
            new_assessment = FrailScale(**assessment_data)
        elif assessment_type == FrailtyScoreTypeEnum.ROCKWOOD_MITNITSKI.value:
            new_assessment = RockwoodMitnitski(**assessment_data)

        # Initialize DocumentManager
        doc_manager = DocumentManager()
        logger.info(f"Initialize DocumentManager success!")

        # Get existing assessment from db
        resp = doc_manager.get_document(user_id, 'ASSESSMENT', assessment_id)
        if not resp['success']:
            return msg_helper.error_response(resp.get('error', f'Failed to get assessment with assessment id:{assessment_id}'), 400)
        
        logger.info(f"response :{resp}")
        
        # Check if assessment_data exists
        assessment_data_from_db = resp['data'].get('assessment_data')
        if not assessment_data_from_db:
            return msg_helper.error_response('No assessment data found in existing assessment', 400)
        
        if assessment_type == FrailtyScoreTypeEnum.FRAIL_SCALE.value:
            old_assessment = FrailScale(**assessment_data_from_db)
        elif assessment_type == FrailtyScoreTypeEnum.ROCKWOOD_MITNITSKI.value:
            old_assessment = RockwoodMitnitski(**assessment_data_from_db)
        
        logger.info(f"Assessment retrieved successfully for user_id: {user_id}")
        logger.info(f"Assessment Record: {old_assessment}")

        # Merge old assessment data with new assessment data
        old_data = old_assessment.dict()
        for key, value in new_assessment.dict().items():
            if value is not None:  # Only update non-null values
                logger.info(f"new assess - Key: {key}, Value: {value}")
                logger.info(f"old assess - Key: {key}, Value: {old_data.get(key)}")
                old_data[key] = value
        
        if assessment_type == FrailtyScoreTypeEnum.FRAIL_SCALE.value:
            latest_assessment = FrailScale(**old_data)
        elif assessment_type == FrailtyScoreTypeEnum.ROCKWOOD_MITNITSKI.value:
            latest_assessment = RockwoodMitnitski(**old_data)

        score = AssessmentUtils.calculate_score(assessment_type, latest_assessment.dict())
        logger.info(f"Score: {score}")
        interpret_score = AssessmentUtils.interpret_score(assessment_type, score)
        logger.info(f"Interpret Score: {interpret_score}")
        
        # Create Frailty Assessment History with metadata
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

        logger.info(f"FrailtyAssessmentHistory updated with ID: {fah.assessment_id}")

        # Update assessment document
        result = doc_manager.save_assessment(user_id, assessment_id, fah)
        logger.info("update_assessment call completed")
        
        if result['success']:
            logger.info(f"Assessment updated successfully for user_id: {user_id}")
            return msg_helper.success_response({
                'message': "Assessment updated successfully",
                'assessment_id': result['assessment_id'],
                'assessment_result' : interpret_score
            })
        else:
            return msg_helper.error_response(result.get('error', 'Failed to update assessment'), 400)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return msg_helper.error_response(str(e), 500)