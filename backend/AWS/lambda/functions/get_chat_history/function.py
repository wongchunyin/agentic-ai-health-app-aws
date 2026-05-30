import json
import os
import logging

try:
    from message_helper import MsgHelper
    from chat_history_manager import ChatHistoryManager
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/livewell-core/python'))
    from chat_history_manager import ChatHistoryManager

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

msg_helper = MsgHelper()
chat_manager = ChatHistoryManager()

def lambda_handler(event, context):
    try:
        user_id = event['requestContext']['authorizer']['claims']['sub']
        if not user_id:
            return msg_helper.error_response("User authentication failed", 401, methods='GET, OPTIONS')

        # Get chat_session_id from query string parameters
        query_params = event.get("queryStringParameters") or {}
        chat_session_id = query_params.get("chat_session_id")
        
        if chat_session_id:
            # Get specific conversation
            result = chat_manager.get_formatted_history(user_id, chat_session_id)
        else:
            # Get all conversations for user
            result = chat_manager.get_all_user_conversations(user_id)
        
        if result['success']:
            return msg_helper.success_response(result, methods='GET, OPTIONS')
        else:
            return msg_helper.error_response(result.get('error', 'Failed to get chat history'), 500, methods='GET, OPTIONS')

    except Exception as e:
        logger.error(f"Error in get_chat_history: {str(e)}")
        return msg_helper.error_response(str(e), 500, methods='GET, OPTIONS')
    

