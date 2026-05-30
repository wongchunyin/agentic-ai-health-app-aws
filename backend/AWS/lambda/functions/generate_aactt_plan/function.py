try:
    from aactt_utils import AACTTUtils, generate_aactt_plan
    from message_helper import MsgHelper
    from config import config
    from schemas import ActionTypeEnum
    from document_manager import DocumentManager
    from assessment_manager import AssessmentManager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/livewell-core/python'))
    from schemas import ActionTypeEnum
    from document_manager import DocumentManager
    from assessment_manager import AssessmentManager
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/ai-agent/python'))
    from aactt_utils import AACTTUtils, generate_aactt_plan
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/aws/python'))
    from config import config

import json
import logging
    
# Configure logging
logger = logging.getLogger()
logger.setLevel(config.LOGGER_LEVEL)

def lambda_handler(event, context):
    logger.info(f"Event: {json.dumps(event)}")
    
    # Initialize MsgHelper first for error handling
    msgHelper = MsgHelper()
    
    try:
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        if not user_id:
            logger.error("User not authenticated")           
            return msgHelper.error_response('User not authenticated', 401)

        body = json.loads(event.get('body', '{}'))

        # Handle both API Gateway (body field) and direct invocation
        logger.info("Checking for body in event...")
        if "body" in event and event["body"]:
            logger.info(f"Body found: {event['body']}")
            body = event["body"]
            if isinstance(body, str):
                logger.info("Parsing JSON body...")
                body = json.loads(body)
            logger.info(f"Parsed body: {body}")

            logger.info("Checking for action_type...")
            if "action_type" not in body:
                logger.error("Action type missing!")
                return msgHelper.error_response(400, "Missing action type in HTTP body")
            logger.info(f"Action type found: {body['action_type']}")
            
            action_type = body["action_type"].lower()
            target = body.get("target")  # Optional target from user
            logger.info(f"Target: {target}")
            
            # check action type with ActionTypeEnum
            if action_type in [e.value for e in ActionTypeEnum]:
                logger.info(f"Action type valid: {action_type}")
                
            
            if  body["action_type"] == "medical":
                return msgHelper.error_response(400, "Medical plan generation not ready yet.")

     
            # Get real user profile data
            doc_manager = DocumentManager()
            profile_result = doc_manager.get_user_profile(user_id)
            user_profile = profile_result.get('data') if profile_result.get('success') else None
            logger.info(f"User profile retrieved: {bool(user_profile)}")
            
            # Get assessment data for personalization
            try:
                assessment_manager = AssessmentManager()
                assessment_data = assessment_manager.get_assessment_history(user_id, limit=2)
                logger.info(f"Assessment data retrieved: {bool(assessment_data)}")
            except Exception as e:
                logger.warning(f"Could not get assessment data: {str(e)}")
                assessment_data = None
            
            # Get existing plans to avoid duplicates
            existing_plans_result = doc_manager.get_user_plans(user_id)
            existing_plans = existing_plans_result.get('data', []) if existing_plans_result.get('success') else []
            logger.info(f"Found {len(existing_plans)} existing plans")
            
            logger.info("Generating personalized plan...")
            result = generate_aactt_plan(action_type, target, user_profile, assessment_data, existing_plans)
            return msgHelper.success_response(result)

        else:
            raise ValueError("No body found in the event")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return msgHelper.error_response(500, f"An error occurred: {str(e)}")





if __name__ == "__main__":
    aacttUtils = AACTTUtils()