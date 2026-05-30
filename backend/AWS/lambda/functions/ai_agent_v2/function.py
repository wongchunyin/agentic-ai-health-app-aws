import json
import os
import logging
import uuid
from datetime import datetime
try:
    from message_helper import MsgHelper
    from config import config
    from ai_agent import GeminiAIAgent
    from cognito_helper import extract_token_from_event
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/aws/python'))
    from config import config
    from cognito_helper import extract_token_from_event
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/ai_agent/python'))
    from ai_agent import GeminiAIAgent


# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):
    """
    AWS Lambda function handler for AI Agent
    """
    try:
        msg_helper = MsgHelper()


        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        if not user_id:
            logger.error("User not authenticated")           
            return msg_helper.error_response('User not authenticated', 401)
        
        # Extract JWT token for login info functionality
        jwt_token = extract_token_from_event(event)
        
        body = event.get("body")
        if isinstance(body, str):
            data = json.loads(body)

        chat_session_id = data.get('chat_session_id')
        # if not chat_session_id, create new one by uuid
        if not chat_session_id:
            chat_session_id = str(uuid.uuid4())
            
        chat_session_name = data.get('chat_session_name')
        if not chat_session_name:
            chat_session_name = "new_chat" + str(datetime.now().isoformat())

        # Initialize and run agent
        agent = GeminiAIAgent(user_id=user_id, chat_session_id=chat_session_id, chat_session_name=chat_session_name, token=jwt_token)

        # Run agent and get structured response
        agent_result = agent.run(data['query'])
        
        # Silent preference extraction in background
        try:
            logger.info(f"Starting silent preference extraction for user: {user_id}")
            from preference_tools import extract_user_preferences_silently, set_user_context
            set_user_context(user_id)
            result = extract_user_preferences_silently(data['query'], async_mode=False)
            logger.info(f"Silent preference extraction result: {result}")
        except Exception as e:
            logger.error(f"Silent preference extraction failed: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
        
        logger.info(f"Agent result keys: {list(agent_result.keys())}")
        logger.info(f"Tools used: {agent_result.get('tools_used', [])}")
        logger.info(f"Function responses: {agent_result.get('function_responses', {})}")
        
        response = agent_result["response"]
        tools_used = agent_result["tools_used"]
        function_responses = agent_result.get("function_responses", {})
        
        # Determine response type based on actual tools used
        if "generate_plan" in tools_used:
            response_type = "plan"
        elif "get_weather_forecast" in tools_used and "get_current_time" in tools_used:
            response_type = "mixed"
        elif "get_weather_forecast" in tools_used:
            response_type = "weather"
        elif "get_current_time" in tools_used:
            response_type = "time"
        else:
            response_type = "chat"
        
        
        
        logger.info(f"Final response - tools_used: {tools_used}, function_responses: {function_responses}")
        logger.debug(f"Response type determined: {response_type}")
        
        return msg_helper.success_response({
            'response': response,
            'query': data['query'],
            'response_type': response_type,
            'tools_used': tools_used,
            'function_responses': function_responses,
            'steps_count': agent_result["steps_count"],
            'user_id': user_id,
            'chat_session_id': chat_session_id
        }, methods='POST,OPTIONS')
    
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return msg_helper.error_response(f'Internal server error: {str(e)}', 500)