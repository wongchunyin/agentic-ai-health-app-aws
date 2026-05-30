import json
import os
from datetime import datetime
import uuid

try:
    from message_layer import MsgHelper
    from gemini_helper import GeminiHelper
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/gemini/python'))
    from gemini_helper import GeminiHelper



def lambda_handler(event, context):

    try:
        # Handle both API Gateway (body field) and direct invocation
        if "body" in event and event["body"]:
            body = event["body"]
            if isinstance(body, str):
                body = json.loads(body)
        else:
            # Direct invocation - event is the body
            body = event
            
        if not body:
            raise ValueError("Body is empty")

        user_id = body.get("user_id")
        if not user_id:
            raise ValueError("Missing user_id")
    
        session_id = generate_user_session_id(user_id)
        
        # Get API key from body or environment
        api_key = body.get("api_key") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("API key is required. Provide api_key in request or set GEMINI_API_KEY environment variable.")
            
        gemini_helper = GeminiHelper(api_key=api_key)
        message = gemini_helper.create_session(session_id=session_id, user_id=user_id, max_history=999)

        msg_helper = MsgHelper()
        return msg_helper.success_response(message)
    except Exception as e:
        msg_helper = MsgHelper()
        return msg_helper.error_response(500, f"An error occurred: {str(e)}")

def generate_user_session_id(user_id):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_part = str(uuid.uuid4())[:8]
    return f"{user_id}_{timestamp}_{unique_part}"


