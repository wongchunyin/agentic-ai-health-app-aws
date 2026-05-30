import os
import json
import urllib.request
from datetime import datetime
import logging
from typing import Dict, Any

try:
    from gemini_helper import GeminiHelper
    from dynamodb_helper import DynamoDBHelper
    from s3_helper import S3Helper
    from toolkit import Toolkit
    from config import config
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../gemini/python'))
    from gemini_helper import GeminiHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../aws/python'))
    from dynamodb_helper import DynamoDBHelper
    from s3_helper import S3Helper
    from config import config
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../toolkit/python'))
    from toolkit import Toolkit


# Create a logger instance
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class GeminiChatbot:
    """
    A class to manage a chat session with the Google Gemini API, including tool use and
    persistent chat history.
    """
    
    # Class-level constant for the API endpoint
    API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    def __init__(self, api_key: str, user_id: str, session_id: str):
        """
        Initializes the GeminiChatbot.
        
        Args:
            api_key: The API key for the Gemini API.
            user_id: A unique identifier for the user.
            session_id: A unique identifier for the chat session.
        
        Raises:
            ValueError: If api_key, user_id, or session_id is not provided.
        """
        logger.info("Initializing GeminiChatbot...")
        
        # 1. Validation of required parameters
        if not all([user_id, session_id]):
            raise ValueError("user_id, and session_id must be provided.")
        
        # 2. Instance attributes
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", None)
        self.user_id = user_id
        self.session_id = session_id
        
        self.is_new_chat = True # default as new chat
        self.full_chat_history = None  # Full history from S3, including metadata
        
        # 3. define S3, DynamoDb and Toolkit first
        self.chat_history_bucket = S3Helper(config.S3_CHAT_HISTORY_BUCKET)
        self.dynamo_tb_livewell = DynamoDBHelper(config.DYNAMODB_TABLE_NAME)
        self.toolkit = Toolkit(user_id, session_id)
        
        # 4. Load tools and available functions (after toolkit is initialized)
        self.tools = self._load_tools_from_file('tools_desc.json')
        logger.debug(f"Loaded tools: {self.tools}")
        self.available_functions = {
            "get_current_time": self._get_current_time,
            "speech_to_text": self.toolkit.speech_to_text,
            "generate_aactt_plan": self.toolkit.generate_aactt_plan,
            "get_weather_forecast": self.toolkit.get_weather_forecast,
            "check_outdoor_weather": self.toolkit.check_outdoor_weather,
            "web_search": self.toolkit.web_search
        }


        # 5. Attempt to find and load existing chat history
        self._find_chat_history()


    def _load_tools_from_file(self, file_path: str = "tools_desc.json"):
        """
        Loads tools from a JSON file and formats them for the Gemini API.
        
        Returns:
            A list of tools formatted for the Gemini API.
        """
        try:
            # Construct a more robust file path
            current_directory = os.path.dirname(os.path.abspath(__file__))
            json_file_path = os.path.join(current_directory, file_path)
            
            with open(json_file_path, 'r') as f:
                tools_data = json.load(f)
            
            function_declarations = [
                {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
                for tool in tools_data.get('tools', [])
            ]
            
            logger.info(f"Successfully loaded {len(function_declarations)} tools.")
            return [{"function_declarations": function_declarations}]
        
        except FileNotFoundError:
            logger.error(f"Tools file not found at: {json_file_path}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON format in {json_file_path}")
        except Exception as e:
            logger.error(f"Error loading tools: {e}")
        
        # Fallback to a default tool if an error occurs
        logger.warning("Loading fallback tools due to an error.")
        return [{
            "function_declarations": [{
                "name": "get_current_time",
                "description": "Get the current time for a given timezone",
                "parameters": {
                    "type": "object",
                    "properties": {"timezone": {"type": "string"}},
                    "required": ["timezone"]
                }
            }]
        }]

    def _find_chat_history(self):
        """Attempts to retrieve and load the chat history from S3 via DynamoDB."""
        try:
            chat_history_file_path = self._get_chat_history_path()
            if not chat_history_file_path:
                logger.info(f"No chat history path found for session {self.session_id}. Starting new chat.")
                return

            loaded_history = self.chat_history_bucket.download_json(key=chat_history_file_path)
            logger.debug(f"Loaded chat history from S3: {loaded_history}")
            
            # Check if loaded successfully and has proper structure
            if not loaded_history or not loaded_history.get('success'):
                logger.warning("Failed to load chat history from S3. Starting a new chat.")
                return
                
            # Extract the actual chat data from the nested structure
            chat_data = loaded_history.get('data', {}).get('content', {})
            if not chat_data or "contents" not in chat_data:
                logger.warning("Chat history is empty or malformed. Starting a new chat.")
                return

            self.full_chat_history = chat_data
            self.is_new_chat = False
            
            # Log loaded history details
            total_entries = len(chat_data.get("contents", []))
            logger.info(f"📂 CHAT_HISTORY_LOADED: Successfully loaded {total_entries} entries for session {self.session_id}")
            logger.debug(f"📂 CHAT_HISTORY_METADATA: {chat_data.get('metadata', {})}")
            logger.info(f"Successfully loaded chat history for session {self.session_id}.")
            
        except Exception as e:
            logger.error(f"Error loading chat history from S3: {e}. Starting a new chat.")

    def _get_chat_history_path(self):
        """Retrieves the chat history file path from DynamoDB."""
        pk = f"USER#{self.user_id}"
        sk = f"CHAT_HISTORY#{self.session_id}"
        logger.debug(f"Querying DynamoDB with PK: {pk}, SK: {sk}")
        
        try:
            # Assuming dynamoTable.get_item returns a dict
            result = self.dynamo_tb_livewell.get_item({'PK': pk, 'SK': sk})
            if result.get('success'):
                logger.info("Chat history path found in DynamoDB.")
                return result.get('data', {}).get('chat_history_path')
            return None
        except Exception as e:
            logger.error(f"DynamoDB retrieval failed: {e}")
            return None

    def chat(self, user_message: str):
        """
        Sends a message to the Gemini API and manages the response.
        
        Args:
            user_message: The user's message as a string.
        
        Returns:
            The model's response as a string.
        """
        # Initialize history if it's a new chat or if not loaded correctly
        if self.is_new_chat:
            self._initialize_new_chat_history()
            
        # Validate user message, allow empty message only when the creating new chat
        if not user_message and not self.is_new_chat:
            raise ValueError("User message must be provided.")
        
        logger.info(f"💬 CHAT_INPUT: User message received - Length: {len(user_message) if user_message else 0}")
        if user_message:  # Only add non-empty messages
            self._add_history(self._create_user_content(message=user_message))
        
        try:
            # Build filtered history fresh from full history for Gemini API
            filtered_history = [
                item["content"] for item in self.full_chat_history["contents"]
                if not item.get("filtered_required", False)
            ]
            response_data = self._send_to_gemini(filtered_history)
            
            if "candidates" not in response_data or not response_data["candidates"]:
                raise ValueError("No candidates found in the response.")
            
            candidate = response_data["candidates"][0]
            finish_reason = candidate.get("finishReason", "STOP")
            parts = candidate["content"].get("parts", [])
            
            logger.debug(f"Gemini finish reason: {finish_reason}")
            
            if not parts:
                return "The model did not return any content."
            
            for part in parts:
                if "functionCall" in part:
                    return self._handle_function_call(part["functionCall"])
                elif "text" in part:
                    model_response = part["text"]
                    logger.info(f"🤖 CHAT_RESPONSE: AI response generated - Length: {len(model_response)}")
                    self._add_history(self._create_model_content(message=model_response))
                    
                    # Check if response is just planning without action
                    # planning_keywords = [
                    #     "let me", "i'll", "i will", "first i'll", "then i'll", "let me check", "i'll find",
                    #     "i need to", "first, i", "i should", "i'm going to", "allow me to", "i can help by",
                    #     "let me search", "i'll look", "first let me", "i'll get", "let me get"
                    # ]
                    # if any(keyword in model_response.lower() for keyword in planning_keywords):
                    #     logger.info("🔄 DETECTED_PLANNING: Response contains planning language, sending follow-up")
                    #     # Add follow-up message to continue
                    #     self._add_history(self._create_user_content(message="Please proceed with that plan now."))
                    #     # Make another request to Gemini
                    #     return self._continue_conversation()
                    
                    return model_response
            
            return "I received your message but couldn't generate a proper response."
            
        except urllib.error.HTTPError as http_err:
            logger.error(f"HTTP Error {http_err.code}: {http_err.reason}")
            return f"An error occurred: HTTP Error {http_err.code}: {http_err.reason}"
        except Exception as e:
            logger.error(f"Unexpected error in chat method: {e}")
            return f"An unexpected error occurred: {e}"
        finally:
            # Save the updated history regardless of success
            resp = self._save_chat_history()
            if resp and resp.get("success"):
                logger.info("Chat history saved successfully.")
            else:
                logger.error(f"Failed to save chat history: {resp}")
                
            
    def _send_to_gemini(self, contents: list):
        """Sends a request to the Gemini API and returns the response data."""
        request_body = {"contents": contents, "tools": self.tools}
        url = f"{self.API_URL}?key={self.api_key}"
        
        logger.info(f"🔧 GEMINI_REQUEST: Sending {len(contents)} messages with {len(self.tools)} tool groups to Gemini")
        logger.debug(f"🔧 TOOLS_SENT: {json.dumps(self.tools, indent=2)}")
        logger.debug(f"Sending request to Gemini API. Payload: {json.dumps(request_body, indent=2)}")
        
        req = urllib.request.Request(
            url,
            data=json.dumps(request_body).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))

    def _handle_function_call(self, function_call: dict):
        """Executes a function call and re-sends the conversation to Gemini."""
        function_name = function_call.get("name")
        function_args = function_call.get("args", {})
        
        if function_name not in self.available_functions:
            logger.error(f"Function '{function_name}' not available.")
            return "I'm sorry, I can't perform that action at the moment."
            
        try:
            logger.info(f"Executing function: {function_name} with args: {function_args}")
            function_to_call = self.available_functions[function_name]
            function_response = function_to_call(**function_args)
            logger.info(f"Function response: {function_response}")
            
            # Add function call and response to history
            self._add_history(self._create_func_call_content(function_name, function_args))
            self._add_history(self._create_tools_response_content(function_name, function_response))
            
            # Re-send the updated conversation including function call/response
            filtered_history = [
                item["content"] for item in self.full_chat_history["contents"]
                if not item.get("filtered_required", False)
            ]
            second_response_data = self._send_to_gemini(filtered_history)
            second_candidate = second_response_data["candidates"][0]
            final_text = "".join(p["text"] for p in second_candidate["content"].get("parts", []) if "text" in p)
            
            if final_text:
                logger.info(f"🔧 CHAT_FUNCTION_RESPONSE: Function call completed, adding final response - Length: {len(final_text)}")
                self._add_history(self._create_model_content(message=final_text))
                
                # Return combined response with function data and model response
                return {
                    "message": final_text,
                    "function_call": {
                        "name": function_name,
                        "args": function_args,
                        "response": function_response
                    }
                }
            
            return "I called a tool but couldn't generate a final response."
        
        except Exception as e:
            logger.error(f"Error executing function call: {e}")
            return f"An error occurred while calling a tool: {e}"
            
    def _save_chat_history(self) -> Dict[str, Any]:
        """Saves the current chat history to S3 and its path to DynamoDB."""
        if not self.full_chat_history:
            logger.warning("No chat history to save.")
            return {"success": False, "error": "No chat history to save"}
            
        try:
            path = f"{self.user_id}/{self.session_id}/chat_history.json"
            resp = self.chat_history_bucket.upload_json(key=path, data=self.full_chat_history)

            # save the path in the DynamoDb if the chat history successfully save in S3
            if resp and resp.get("success"):
                logger.info(f"Successfully saved history to S3: {path}")

                # prepare the pk and sk 
                pk = "USER#" + str(self.user_id).strip()
                sk = "CHAT_HISTORY#" + str(self.session_id).strip()
                logger.debug(f"PK: {pk}, SK: {sk}")
                keys = {"PK": pk, "SK": sk}
                # check if the item exist 
                get_item_resp = self.dynamo_tb_livewell.get_item(key=keys)

                # if the item exist, update it
                if get_item_resp and get_item_resp.get("success"):
                    # update the item
                    update_item_resp = self.dynamo_tb_livewell.update_item(
                        key=keys,
                        update_expression="SET chat_history_path = :path, updated_at = :updated_at",
                        expression_attribute_values={
                            ":path": path,
                            ":updated_at": datetime.now().isoformat()
                        }
                    )

                    if update_item_resp and update_item_resp.get("success"):
                        logger.info(f"Successfully updated item in DynamoDB: {keys}")
                        return update_item_resp
                    else:
                        logger.error(f"Failed to update item in DynamoDB: {keys}")
                        return {"success": False, "error": "Failed to update DynamoDB item"}
                else:
                    # Item doesn't exist, create it
                    item = {
                        "PK": pk,
                        "SK": sk,
                        "chat_history_path": path,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                    create_resp = self.dynamo_tb_livewell.create_item(item)
                    if create_resp and create_resp.get("success"):
                        logger.info(f"Successfully created item in DynamoDB: {keys}")
                        return create_resp
                    else:
                        logger.error(f"Failed to create item in DynamoDB: {keys}")
                        return {"success": False, "error": "Failed to create DynamoDB item"}
            
            return {"success": False, "error": "Failed to save to S3"}
                    
        except Exception as e:
            logger.error(f"Failed to save chat history: {e}")
            return {"success": False, "error": str(e)}

    def _initialize_new_chat_history(self):
        """Creates the initial structure for a new chat session."""
        logger.info(f"🆕 CHAT_HISTORY_INIT: Initializing new chat history for session {self.session_id}")
        
        self.full_chat_history = {
            "metadata": {
                "session_id": self.session_id,
                "user_id": self.user_id,
                "start_time": datetime.now().isoformat(),
                "last_update_time": datetime.now().isoformat()
            },
            "contents": []
        }
        
        logger.info(f"📊 CHAT_HISTORY_STRUCTURE: Created empty structure with metadata: {self.full_chat_history['metadata']}")

        # add the first content 
        DEFAULT_STARTING_PROMPT = "You are a helpful health and wellness assistant for older people. You have access to several tools to support users: web_search for real-time information, weather tools for outdoor activity planning, speech_to_text for audio processing, and generate_aactt_plan for creating personalized health plans. Use web_search whenever you need current information, recent news, or up-to-date data. Always use these tools to provide the best assistance and remember to cite source if any when using search results. Now, start with a warm greeting. Rule for communications: 1. Do not directly mention the tools names you have except function call. 2. If user requests somethings that you cannot do, always suggest a new approach. 3. Always use the tool 'generate_aactt_plan' for different kind of plan generation."
        self._add_history(self._create_user_content(message=DEFAULT_STARTING_PROMPT))
        self.is_new_chat = False
        logger.info("✅ CHAT_HISTORY_INIT: New chat history structure created and initialized.")

    def _add_history(self, content: dict, filter_required: bool = False):
        """
        Append a new content to the full chat history and updates the filtered history.
        
        Args:
            content: The content dictionary for the chat entry.
            filter_required: True if the content should be included in the filtered history
                             sent to the API.
        """
        new_entry = {
            "datetime": datetime.now().isoformat(),
            "content": content,
            "filtered_required": filter_required,
            "summarized": False # You might want to update this later
        }
        
        # Log the change before adding
        logger.info(f"📝 CHAT_HISTORY_CHANGE: Adding new entry - Role: {content.get('role', 'unknown')}, Filter: {filter_required}")
        logger.debug(f"📝 CHAT_HISTORY_CONTENT: {json.dumps(content, indent=2)}")
        
        self.full_chat_history["contents"].append(new_entry)
        self.full_chat_history["metadata"]["last_update_time"] = datetime.now().isoformat()
        
        # Log the current state
        total_entries = len(self.full_chat_history["contents"])
        logger.info(f"📊 CHAT_HISTORY_STATE: Total entries: {total_entries}, Session: {self.session_id}")
        
        logger.debug(f"Added new history entry. Filtered: {filter_required}. Full history: {self.full_chat_history['contents']}")

    @staticmethod
    def _create_user_content(message: str) -> dict:
        """Creates a user history content object."""
        return {"role": "user", "parts": [{"text": message}]}

    @staticmethod
    def _create_model_content(message: str) -> dict:
        """Creates a model history content object."""
        return {"role": "model", "parts": [{"text": message}]}

    @staticmethod
    def _create_func_call_content(function_name: str, function_args: dict) -> dict:
        """Creates a function call history content object."""
        return {
            "role": "model",
            "parts": [{"functionCall": {"name": function_name, "args": function_args}}]
        }
    
    @staticmethod
    def _create_tools_response_content(function_name: str, function_response: Any) -> dict:
        """Creates a tool response history content object."""
        return {
            "role": "tool",
            "parts": [{"functionResponse": {"name": function_name, "response": function_response}}]
        }
    
    # def _continue_conversation(self):
    #     """Continue conversation after detecting planning response"""
    #     try:
    #         filtered_history = [
    #             item["content"] for item in self.full_chat_history["contents"]
    #             if not item.get("filtered_required", False)
    #         ]
    #         response_data = self._send_to_gemini(filtered_history)
            
    #         if "candidates" not in response_data or not response_data["candidates"]:
    #             return "I planned to help but couldn't continue."
            
    #         candidate = response_data["candidates"][0]
    #         parts = candidate["content"].get("parts", [])
            
    #         for part in parts:
    #             if "functionCall" in part:
    #                 return self._handle_function_call(part["functionCall"])
    #             elif "text" in part:
    #                 final_response = part["text"]
    #                 self._add_history(self._create_model_content(message=final_response))
    #                 return final_response
            
    #         return "I planned to help but couldn't execute the plan."
            
    #     except Exception as e:
    #         logger.error(f"Error continuing conversation: {e}")
    #         return "I planned to help but encountered an error."
    


    def _get_current_time(self):
        return datetime.now().isoformat()