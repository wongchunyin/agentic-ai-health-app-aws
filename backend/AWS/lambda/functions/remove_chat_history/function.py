import json
import logging
from typing import Dict, Any
from datetime import datetime
# Import from layers

try:
    from message_helper import MsgHelper
    from chat_history_manager import ChatHistoryManager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/livewell-core/python'))
    from chat_history_manager import ChatHistoryManager

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    try:
        
        logger.info(f"Event: {event}")
        msg_helper = MsgHelper()
       
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        if not user_id:
            logger.error("User not authenticated")           
            return msg_helper.error_response('User not authenticated', 401)

        # Get chat_session_id from query parameters (more appropriate for DELETE)
        query_params = event.get('queryStringParameters') or {}
        chat_session_id = query_params.get('chat_session_id')
        
        # Fallback to body if not in query params (for backward compatibility)
        if not chat_session_id:
            body = json.loads(event.get('body', '{}'))
            chat_session_id = body.get('chat_session_id')
        
        if not chat_session_id:
            logger.error("Chat session ID not provided")
            return msg_helper.error_response('Chat session ID not provided', 400)
        
        # remove the chat history
        chat_history_manager = ChatHistoryManager()
        resp = chat_history_manager.remove_conversation(user_id, chat_session_id)
        
        logger.info(f"Remove conversation response: {resp}")
        
        if resp is None:
            logger.error("remove_conversation returned None")
            return msg_helper.error_response('Failed to remove chat history', 500)
            
        if not isinstance(resp, dict):
            logger.error(f"remove_conversation returned non-dict: {type(resp)}")
            return msg_helper.error_response('Invalid response from chat history manager', 500)
            
        if not resp.get('success', False):
            error_msg = resp.get('error', 'Unknown error')
            logger.error(f"Failed to remove chat history: {error_msg}")
            return msg_helper.error_response(error_msg, 400)
        
        return msg_helper.success_response("Chat history removed successfully")
        
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        return MsgHelper().error_response("Invalid event format", 400)