import json
import logging
from typing import Dict, Any
import os
from twilio.rest import Client

try:
    from message_helper import MsgHelper
    from document_manager import DocumentManager
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/livewell-core/python'))
    from document_manager import DocumentManager

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    msg_helper = MsgHelper()
    
    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return msg_helper.success_response('', methods='POST,OPTIONS')
    
    try:
        # Get user_id from Cognito authorizer
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        if not user_id:
            return msg_helper.error_response('User not authenticated', 401, methods='POST,OPTIONS')

        body = json.loads(event.get('body', '{}'))
        
        # Extract required fields
        phone_number = body.get('phone_number')
        message = body.get('message')
        
        if not message:
            return msg_helper.error_response('message is required', 400, methods='POST,OPTIONS')

        # Check user SMS permission
        # doc_manager = DocumentManager()
        # profile_result = doc_manager.get_user_profile(user_id)
        
        # if not profile_result['success']:
        #     return msg_helper.error_response('User profile not found', 404, methods='POST,OPTIONS')
            
        # profile = profile_result['data']
        # if not profile.get('allowSMS', False) and not profile.get('sms_permission', False):
        #     return msg_helper.error_response('SMS notifications not permitted for this user', 403, methods='POST,OPTIONS')

        # Initialize Twilio client
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        from_number = os.environ.get('TWILIO_PHONE_NUMBER')
        
        if not all([account_sid, auth_token, from_number]):
            return msg_helper.error_response('Twilio configuration missing', 500, methods='POST,OPTIONS')

        client = Client(account_sid, auth_token)
        
        # Send SMS - always use template with message as variable {{1}}
        sms = client.messages.create(
            content_sid='HX978ad8c3cdea0479b3702721e3f36979',
            content_variables=json.dumps({"1": message}),
            from_=from_number,
            to=phone_number
        )
        
        logger.info(f"SMS sent successfully. SID: {sms.sid}")
        
        return msg_helper.success_response({
            'message': 'SMS sent successfully',
            'sms_sid': sms.sid,
            'status': sms.status
        }, methods='POST,OPTIONS')
        
    except Exception as e:
        logger.error(f"Error sending SMS: {str(e)}")
        return msg_helper.error_response(f"Failed to send SMS: {str(e)}", 500, methods='POST,OPTIONS')