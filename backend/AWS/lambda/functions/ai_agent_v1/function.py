import json
import boto3
import os
import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
import uuid

try:

    from gemini_chatbot import GeminiChatbot
    from dynamodb_helper import DynamoDBHelper
    from s3_helper import S3Helper
    from toolkit import Toolkit
    from message_helper import MsgHelper
    from config import config
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/gemini/python'))
    from gemini_chatbot import GeminiChatbot
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/aws/python'))
    from dynamodb_helper import DynamoDBHelper
    from s3_helper import S3Helper
    from config import config
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/toolkit/python'))
    from toolkit import Toolkit
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/message/python'))
    from message_helper import MsgHelper


# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Global AWS clients
msg_helper = MsgHelper()

# boto3_session = boto3.session.Session()
# lambda_client = boto3_session.client('lambda', region_name='us-east-1')

def lambda_handler(event, context):
    logger.info("Lambda handler started")
    
    try:
        # Get user_id from API Gateway context (Cognito provides this)
        user_id = event['requestContext']['authorizer']['claims']['sub']
        body = event.get("body")
        if isinstance(body, str):
            data = json.loads(body)
            
        API_KEY = data.get("api_key", os.environ.get("GEMINI_API_KEY", None)) 
        session_id = data.get("session_id")
        message = data.get("message")

        # Debug API key and user_id
        logger.debug(f"API Key received: {API_KEY[:10] if API_KEY else 'None'}...")
        logger.info(f"Authenticated user: '{user_id}'")
        logger.info(f"Received Session ID: '{session_id}'")
        
        # if no session_id, create new one 
        if not session_id or session_id == "":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_part = str(uuid.uuid4())[:8]
            session_id = f"{user_id}_{timestamp}_{unique_part}"
            logger.info(f"New session ID created: '{session_id}'")

        
        logger.info(f"Processing message for user {user_id}, session {session_id}")

        # Initialize the chatbot with the provided API key
        logger.info("Initializing GeminiChatbot")


        chatbot = GeminiChatbot(API_KEY, user_id=user_id, session_id=session_id)
        
        logger.info("Calling chatbot.chat")
        ai_message = chatbot.chat(user_message=message)
        
        logger.info(f"Successfully processed message for user {user_id}")
        return msg_helper.success_response({"response": {"session_id": session_id, "message": ai_message}}, methods='POST,OPTIONS')
    
    

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return msg_helper.error_response("Invalid JSON format", 400, methods='POST,OPTIONS')
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return msg_helper.error_response(str(e), 400, methods='POST,OPTIONS')
    except (KeyError, TypeError) as auth_error:
        logger.error(f"Authentication error: {auth_error}")
        return msg_helper.error_response("Authentication failed", 401, methods='POST,OPTIONS')
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return msg_helper.error_response(f"An error occurred: {str(e)}", 500, methods='POST,OPTIONS')

# def save_history_path_in_dynamo(user_id: str, session_id: str, path: str):
#     # Validate inputs
#     if not user_id or not session_id:
#         logger.error(f"Invalid inputs - user_id: '{user_id}', session_id: '{session_id}'")
#         return False
        
#     pk = "USER#" + str(user_id).strip()
#     sk = "CHAT_HISTORY#" + str(session_id).strip()
    
#     logger.info(f"Saving to DynamoDB - PK: '{pk}', SK: '{sk}', Path: '{path}'")
    
#     resp = dynamoTable.get_item({'PK': pk, 'SK': sk})

#     cnt_new_content = 0
#     # check item 
#     if resp and resp.get('statusCode') == 200:
#         logger.info(f"Chat history Path already exists, not update create required")

#         # get the cnt_new_content from resp
#         cnt_new_content = resp['data'].get('cnt_new_content', 0)

#     # create new item
#     item = {
#         "PK": pk,
#         "SK": sk,
#         "chat_history_path": path,
#         "chat_summary_path": path,
#         "cnt_new_content" : cnt_new_content
#     }


#     result = dynamoTable.create_item(item, 'attribute_not_exists(PK) AND attribute_not_exists(SK)')
#     if result['success']:
#         return True
#     elif 'ConditionalCheckFailedException' in str(result.get('error', '')):
#         # Record already exists, which is fine - just update the path
#         logger.info(f"Chat history Path already exists, not update create required")
#         return True
#     else:
#         return False


# def save_history_in_s3(history: dict, user_id: str, session_id: str):
#     try:
#         # create file name
#         file_name = f"{session_id}.json"
#         path = f"{user_id}/{file_name}"
#         logger.info(f"Saving history to S3: {path}")
#         logger.debug(f"History data: {history}")

#         # Upload the actual history data to S3
#         resp = chat_history_bucket.upload_json(key=path, data=history)
#         logger.info(f"S3 upload response: {resp}")
        
#         if resp and resp.get('statusCode') == 200:
#             logger.info(f"Successfully saved history to S3: {path}")
#             return True, path
#         else:
#             logger.error(f"Failed to save history to S3. Response: {resp}")
#             return False, None
    
#     except Exception as e:
#         logger.error(f"Error saving chat history in S3: {e}")
#         import traceback
#         logger.error(f"Traceback: {traceback.format_exc()}")
#         return False, None
    

# def lambda_call(function_name, payload):
    # try:
    #     response = lambda_client.invoke(
    #         FunctionName=function_name,
    #         InvocationType='RequestResponse',  # Use 'Event' for async
    #         Payload=json.dumps(payload)
    #     )
    #     response_payload = response['Payload'].read()
    #     logger.debug(f"Response body: {response_payload}")
    #     return json.loads(response_payload)
    # except Exception as e:
    #     print(f"Error invoking Lambda function: {e}")
    #     return json.dumps({
    #         "payload": payload,
    #         "error": f"Failed to retrieve weather from service: {e}"
    #     })
    

# def get_current_time():
#     """
#     Get the current time for a given timezone.

#     Args:
#         timezone (str): The timezone, e.g., 'America/Los_Angeles'.
#     """
#     # This is a placeholder.
#     # print(f"**Function call requested: get_current_time(timezone='{timezone}')**")
#     return json.dumps({"time": datetime.now().strftime("%H:%M:%S") })


# Now using GeminiChatbot from layers/gemini/python/gemini_chatbot.py

