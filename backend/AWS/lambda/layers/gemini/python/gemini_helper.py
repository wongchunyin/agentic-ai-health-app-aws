"""
Gemini API Helper Library for AWS Lambda Layer
==============================================

This module provides communication with Google's Gemini-1.5-flash model.
Designed to be used as a Lambda layer and imported by other Lambda functions.

Usage in Lambda functions:
    from gemini_helper import GeminiHelper
    
    gemini = GeminiHelper(api_key='your-api-key')
    result = gemini.generate_text('Hello, how are you?')
"""

import json
import logging
import base64
import os
from typing import Dict, List, Optional, Any, Union
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class GeminiHelper:
    """
    A helper class for communicating with Google's Gemini API in AWS Lambda functions.
    
    This class provides methods for text generation, multimodal conversations,
    session management, and various AI-powered operations using Gemini-1.5-flash.
    """
    
    def __init__(self, api_key: str = None, model: str = "gemini-1.5-flash", 
                 session_storage=None):
        """
        Initialize the Gemini helper.
        
        Args:
            api_key (str, optional): Google AI API key. If not provided, tries to get from environment
            model (str): Model name to use (default: gemini-1.5-flash)
            session_storage: Storage backend for sessions (DynamoDBHelper instance, dict, etc.)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("API key is required. Set GEMINI_API_KEY environment variable or pass api_key parameter.")
        
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.session_storage = session_storage
        self.session_cache = {}  # In-memory cache for current execution
        
        # Default generation config
        self.default_config = {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 8192,
            "stopSequences": []
        }
        
        # Default safety settings
        self.default_safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        logger.info(f"GeminiHelper initialized with model: {model}")

    def create_session(self, session_id: str, user_id: str = None, 
                      metadata: Dict[str, Any] = None, 
                      max_history: int = 50) -> Dict[str, Any]:
        """
        Create a new conversation session.
        
        Args:
            session_id (str): Unique session identifier
            user_id (str, optional): User identifier
            metadata (Dict, optional): Additional session metadata
            max_history (int): Maximum number of messages to keep in history
            
        Returns:
            Dict: Session creation result
        """
        try:
            from datetime import datetime
            
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'messages': [],
                'metadata': metadata or {},
                'max_history': max_history,
                'message_count': 0
            }
            
            # Store in session storage if available
            if self.session_storage:
                if hasattr(self.session_storage, 'create_item'):
                    # DynamoDB storage
                    result = self.session_storage.create_item(session_data)
                    if not result['success']:
                        return result
                elif isinstance(self.session_storage, dict):
                    # Dict storage
                    self.session_storage[session_id] = session_data
            
            # Cache in memory
            self.session_cache[session_id] = session_data
            
            logger.info(f"Session created: {session_id}")
            
            return {
                'statusCode': 200,
                'success': True,
                'message': 'Session created successfully',
                'data': {
                    'session_id': session_id,
                    'user_id': user_id,
                    'created_at': session_data['created_at']
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'SessionCreationError',
                'message': str(e)
            }

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve a conversation session.
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            Dict: Session data or error
        """
        try:
            # Check memory cache first
            if session_id in self.session_cache:
                return {
                    'statusCode': 200,
                    'success': True,
                    'data': self.session_cache[session_id]
                }
            
            # Check persistent storage
            if self.session_storage:
                if hasattr(self.session_storage, 'get_item'):
                    # DynamoDB storage
                    result = self.session_storage.get_item({'session_id': session_id})
                    if result['success']:
                        # Cache the session
                        self.session_cache[session_id] = result['data']
                        return result
                    elif result['statusCode'] == 404:
                        return {
                            'statusCode': 404,
                            'success': False,
                            'message': 'Session not found'
                        }
                    else:
                        return result
                elif isinstance(self.session_storage, dict):
                    # Dict storage
                    if session_id in self.session_storage:
                        session_data = self.session_storage[session_id]
                        self.session_cache[session_id] = session_data
                        return {
                            'statusCode': 200,
                            'success': True,
                            'data': session_data
                        }
            
            return {
                'statusCode': 404,
                'success': False,
                'message': 'Session not found'
            }
            
        except Exception as e:
            logger.error(f"Failed to get session: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'SessionRetrievalError',
                'message': str(e)
            }

    def update_session(self, session_id: str, message: Dict[str, str]) -> Dict[str, Any]:
        """
        Update session with a new message.
        
        Args:
            session_id (str): Session identifier
            message (Dict): Message with 'role' and 'content' keys
            
        Returns:
            Dict: Update result
        """
        try:
            from datetime import datetime
            
            # Get current session
            session_result = self.get_session(session_id)
            if not session_result['success']:
                return session_result
            
            session_data = session_result['data']
            
            # Add timestamp to message
            message_with_timestamp = {
                'role': message['role'],
                'content': message['content'],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Add message to history
            session_data['messages'].append(message_with_timestamp)
            session_data['message_count'] += 1
            session_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Trim history if needed
            max_history = session_data.get('max_history', 50)
            if len(session_data['messages']) > max_history:
                session_data['messages'] = session_data['messages'][-max_history:]
            
            # Update storage
            if self.session_storage:
                if hasattr(self.session_storage, 'update_item'):
                    # DynamoDB storage
                    update_expression = "SET messages = :messages, message_count = :count, updated_at = :updated"
                    expression_values = {
                        ':messages': session_data['messages'],
                        ':count': session_data['message_count'],
                        ':updated': session_data['updated_at']
                    }
                    
                    result = self.session_storage.update_item(
                        {'session_id': session_id},
                        update_expression,
                        expression_values
                    )
                    if not result['success']:
                        return result
                elif isinstance(self.session_storage, dict):
                    # Dict storage
                    self.session_storage[session_id] = session_data
            
            # Update cache
            self.session_cache[session_id] = session_data
            
            logger.info(f"Session updated: {session_id}")
            
            return {
                'statusCode': 200,
                'success': True,
                'message': 'Session updated successfully',
                'data': {
                    'session_id': session_id,
                    'message_count': session_data['message_count']
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to update session: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'SessionUpdateError',
                'message': str(e)
            }

    def chat_with_session(self, session_id: str, user_message: str,
                         generation_config: Dict[str, Any] = None,
                         auto_create_session: bool = True) -> Dict[str, Any]:
        """
        Chat with session management and history.
        
        Args:
            session_id (str): Session identifier
            user_message (str): User's message
            generation_config (Dict, optional): Generation configuration
            auto_create_session (bool): Whether to create session if it doesn't exist
            
        Returns:
            Dict: Chat response with session handling
        """
        try:
            # Get or create session
            session_result = self.get_session(session_id)
            if not session_result['success']:
                if session_result['statusCode'] == 404 and auto_create_session:
                    # Create new session
                    create_result = self.create_session(session_id)
                    if not create_result['success']:
                        return create_result
                    session_result = self.get_session(session_id)
                else:
                    return session_result
            
            session_data = session_result['data']
            
            # Add user message to session
            user_msg = {'role': 'user', 'content': user_message}
            update_result = self.update_session(session_id, user_msg)
            if not update_result['success']:
                return update_result
            
            # Get updated session with message history
            session_result = self.get_session(session_id)
            messages = session_result['data']['messages']
            
            # Convert to chat format (exclude timestamps)
            chat_messages = [
                {'role': msg['role'], 'content': msg['content']} 
                for msg in messages
            ]
            
            # Generate response using conversation history
            response_result = self.chat_conversation(chat_messages, generation_config)
            
            if response_result['success']:
                # Add assistant response to session
                assistant_msg = {
                    'role': 'assistant', 
                    'content': response_result['data']['response']
                }
                self.update_session(session_id, assistant_msg)
                
                logger.info(f"Chat response generated for session: {session_id}")
                
                return {
                    'statusCode': 200,
                    'success': True,
                    'data': {
                        'session_id': session_id,
                        'response': response_result['data']['response'],
                        'message_count': session_result['data']['message_count'] + 2,  # +2 for user + assistant
                        'usage': response_result['data'].get('usage', {}),
                        'model': self.model
                    }
                }
            
            return response_result
            
        except Exception as e:
            logger.error(f"Failed to process chat with session: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'SessionChatError',
                'message': str(e)
            }

    def get_session_history(self, session_id: str, limit: int = None) -> Dict[str, Any]:
        """
        Get conversation history for a session.
        
        Args:
            session_id (str): Session identifier
            limit (int, optional): Limit number of messages returned
            
        Returns:
            Dict: Session history
        """
        try:
            session_result = self.get_session(session_id)
            if not session_result['success']:
                return session_result
            
            session_data = session_result['data']
            messages = session_data['messages']
            
            if limit:
                messages = messages[-limit:]
            
            return {
                'statusCode': 200,
                'success': True,
                'data': {
                    'session_id': session_id,
                    'messages': messages,
                    'total_messages': session_data['message_count'],
                    'created_at': session_data['created_at'],
                    'updated_at': session_data['updated_at']
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get session history: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'SessionHistoryError',
                'message': str(e)
            }

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        Delete a conversation session.
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            Dict: Deletion result
        """
        try:
            # Remove from storage
            if self.session_storage:
                if hasattr(self.session_storage, 'delete_item'):
                    # DynamoDB storage
                    result = self.session_storage.delete_item({'session_id': session_id})
                    if not result['success'] and result['statusCode'] != 404:
                        return result
                elif isinstance(self.session_storage, dict):
                    # Dict storage
                    if session_id in self.session_storage:
                        del self.session_storage[session_id]
            
            # Remove from cache
            if session_id in self.session_cache:
                del self.session_cache[session_id]
            
            logger.info(f"Session deleted: {session_id}")
            
            return {
                'statusCode': 200,
                'success': True,
                'message': 'Session deleted successfully',
                'data': {'session_id': session_id}
            }
            
        except Exception as e:
            logger.error(f"Failed to delete session: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'SessionDeletionError',
                'message': str(e)
            }

    def list_user_sessions(self, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """
        List sessions for a specific user.
        
        Args:
            user_id (str): User identifier
            limit (int): Maximum number of sessions to return
            
        Returns:
            Dict: List of user sessions
        """
        try:
            sessions = []
            
            if self.session_storage:
                if hasattr(self.session_storage, 'scan_items'):
                    # DynamoDB storage - scan with filter
                    result = self.session_storage.scan_items(
                        filter_expression='user_id = :user_id',
                        expression_attribute_values={':user_id': user_id},
                        limit=limit
                    )
                    
                    if result['success']:
                        sessions = [
                            {
                                'session_id': session['session_id'],
                                'created_at': session['created_at'],
                                'updated_at': session['updated_at'],
                                'message_count': session['message_count']
                            }
                            for session in result['data']
                        ]
                elif isinstance(self.session_storage, dict):
                    # Dict storage - filter by user_id
                    for session_id, session_data in self.session_storage.items():
                        if session_data.get('user_id') == user_id:
                            sessions.append({
                                'session_id': session_id,
                                'created_at': session_data['created_at'],
                                'updated_at': session_data['updated_at'],
                                'message_count': session_data['message_count']
                            })
                        
                        if len(sessions) >= limit:
                            break
            
            return {
                'statusCode': 200,
                'success': True,
                'data': {
                    'user_id': user_id,
                    'sessions': sessions,
                    'count': len(sessions)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to list user sessions: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'SessionListError',
                'message': str(e)
            }

    def clear_session_history(self, session_id: str, keep_last: int = 0) -> Dict[str, Any]:
        """
        Clear session history, optionally keeping the last N messages.
        
        Args:
            session_id (str): Session identifier
            keep_last (int): Number of recent messages to keep
            
        Returns:
            Dict: Clear operation result
        """
        try:
            from datetime import datetime
            
            session_result = self.get_session(session_id)
            if not session_result['success']:
                return session_result
            
            session_data = session_result['data']
            
            # Keep only the last N messages
            if keep_last > 0:
                session_data['messages'] = session_data['messages'][-keep_last:]
            else:
                session_data['messages'] = []
            
            session_data['message_count'] = len(session_data['messages'])
            session_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Update storage
            if self.session_storage:
                if hasattr(self.session_storage, 'update_item'):
                    # DynamoDB storage
                    update_expression = "SET messages = :messages, message_count = :count, updated_at = :updated"
                    expression_values = {
                        ':messages': session_data['messages'],
                        ':count': session_data['message_count'],
                        ':updated': session_data['updated_at']
                    }
                    
                    result = self.session_storage.update_item(
                        {'session_id': session_id},
                        update_expression,
                        expression_values
                    )
                    if not result['success']:
                        return result
                elif isinstance(self.session_storage, dict):
                    # Dict storage
                    self.session_storage[session_id] = session_data
            
            # Update cache
            self.session_cache[session_id] = session_data
            
            logger.info(f"Session history cleared: {session_id}")
            
            return {
                'statusCode': 200,
                'success': True,
                'message': 'Session history cleared successfully',
                'data': {
                    'session_id': session_id,
                    'messages_kept': keep_last,
                    'current_message_count': session_data['message_count']
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to clear session history: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'SessionClearError',
                'message': str(e)
            }

    def generate_text(self, prompt: str, generation_config: Dict[str, Any] = None,
                     safety_settings: List[Dict[str, str]] = None, parse_json: bool = False) -> Dict[str, Any]:
        """
        Generate text using Gemini model.
        
        Args:
            prompt (str): Input prompt for text generation
            generation_config (Dict, optional): Generation configuration parameters
            safety_settings (List[Dict], optional): Safety filtering settings
            parse_json (bool): Whether to attempt JSON parsing of the response
            
        Returns:
            Dict: Response from Gemini API
        """
        try:
            # Build request payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": generation_config or self.default_config,
                "safetySettings": safety_settings or self.default_safety_settings
            }
            
            # Make API request
            response = self._make_request("generateContent", payload)
            
            if response['success']:
                # Extract generated text
                candidates = response['data'].get('candidates', [])
                if candidates and candidates[0].get('content'):
                    generated_text = candidates[0]['content']['parts'][0]['text']
                    
                    # Parse JSON if requested
                    parsed_json = None
                    if parse_json:
                        parsed_json = self._parse_json_response(generated_text)
                    
                    logger.info("Text generated successfully")
                    
                    result_data = {
                        'generated_text': generated_text,
                        'model': self.model,
                        'usage': response['data'].get('usageMetadata', {}),
                        'safety_ratings': candidates[0].get('safetyRatings', []),
                        'finish_reason': candidates[0].get('finishReason', 'STOP')
                    }
                    
                    if parsed_json is not None:
                        result_data['parsed_json'] = parsed_json
                    
                    return {
                        'statusCode': 200,
                        'success': True,
                        'data': result_data
                    }
                else:
                    logger.warning("No content generated - possibly blocked by safety filters")
                    return {
                        'statusCode': 400,
                        'success': False,
                        'message': 'No content generated - possibly blocked by safety filters',
                        'data': response['data']
                    }
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate text: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'TextGenerationError',
                'message': str(e)
            }

    def generate_text_with_image(self, prompt: str, image_data: Union[str, bytes],
                                image_mime_type: str = "image/jpeg",
                                generation_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate text based on prompt and image using Gemini's multimodal capabilities.
        
        Args:
            prompt (str): Text prompt
            image_data (Union[str, bytes]): Image data (base64 string or bytes)
            image_mime_type (str): MIME type of the image
            generation_config (Dict, optional): Generation configuration
            
        Returns:
            Dict: Response from Gemini API
        """
        try:
            # Convert image data to base64 if needed
            if isinstance(image_data, bytes):
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            elif isinstance(image_data, str):
                # Assume it's already base64 encoded
                image_base64 = image_data
            else:
                raise ValueError("image_data must be bytes or base64 string")
            
            # Build request payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": image_mime_type,
                                    "data": image_base64
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": generation_config or self.default_config,
                "safetySettings": self.default_safety_settings
            }
            
            # Make API request
            response = self._make_request("generateContent", payload)
            
            if response['success']:
                candidates = response['data'].get('candidates', [])
                if candidates and candidates[0].get('content'):
                    generated_text = candidates[0]['content']['parts'][0]['text']
                    
                    logger.info("Multimodal text generated successfully")
                    
                    return {
                        'statusCode': 200,
                        'success': True,
                        'data': {
                            'generated_text': generated_text,
                            'model': self.model,
                            'usage': response['data'].get('usageMetadata', {}),
                            'safety_ratings': candidates[0].get('safetyRatings', []),
                            'finish_reason': candidates[0].get('finishReason', 'STOP')
                        }
                    }
                else:
                    return {
                        'statusCode': 400,
                        'success': False,
                        'message': 'No content generated',
                        'data': response['data']
                    }
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate text with image: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'MultimodalGenerationError',
                'message': str(e)
            }

    def chat_conversation(self, messages: List[Dict[str, str]], 
                         generation_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle multi-turn chat conversation.
        
        Args:
            messages (List[Dict]): List of messages with 'role' and 'content' keys
            generation_config (Dict, optional): Generation configuration
            
        Returns:
            Dict: Response from Gemini API
        """
        try:
            # Convert messages to Gemini format
            contents = []
            for message in messages:
                role = message.get('role', 'user')
                content = message.get('content', '')
                
                # Map roles to Gemini format
                if role == 'assistant':
                    gemini_role = 'model'
                else:
                    gemini_role = 'user'
                
                contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })
            
            # Build request payload
            payload = {
                "contents": contents,
                "generationConfig": generation_config or self.default_config,
                "safetySettings": self.default_safety_settings
            }
            
            # Make API request
            response = self._make_request("generateContent", payload)
            
            if response['success']:
                candidates = response['data'].get('candidates', [])
                if candidates and candidates[0].get('content'):
                    generated_text = candidates[0]['content']['parts'][0]['text']
                    
                    logger.info("Chat response generated successfully")
                    
                    return {
                        'statusCode': 200,
                        'success': True,
                        'data': {
                            'response': generated_text,
                            'model': self.model,
                            'usage': response['data'].get('usageMetadata', {}),
                            'safety_ratings': candidates[0].get('safetyRatings', []),
                            'finish_reason': candidates[0].get('finishReason', 'STOP')
                        }
                    }
                else:
                    return {
                        'statusCode': 400,
                        'success': False,
                        'message': 'No response generated',
                        'data': response['data']
                    }
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to process chat conversation: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'ChatConversationError',
                'message': str(e)
            }

    def analyze_document(self, document_content: str, analysis_prompt: str,
                        generation_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze document content with a specific prompt.
        
        Args:
            document_content (str): Content of the document to analyze
            analysis_prompt (str): Specific analysis instructions
            generation_config (Dict, optional): Generation configuration
            
        Returns:
            Dict: Analysis results from Gemini
        """
        try:
            # Combine document and analysis prompt
            full_prompt = f"""Document Content:
{document_content}

Analysis Request:
{analysis_prompt}

Please provide a detailed analysis based on the above document and request."""
            
            return self.generate_text(full_prompt, generation_config)
            
        except Exception as e:
            logger.error(f"Failed to analyze document: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'DocumentAnalysisError',
                'message': str(e)
            }

    def extract_structured_data(self, text: str, schema: Dict[str, Any],
                               generation_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extract structured data from text based on a provided schema.
        
        Args:
            text (str): Text to extract data from
            schema (Dict): JSON schema defining the expected structure
            generation_config (Dict, optional): Generation configuration
            
        Returns:
            Dict: Extracted structured data
        """
        try:
            schema_json = json.dumps(schema, indent=2)
            
            prompt = f"""Extract structured data from the following text according to the provided JSON schema.
Return only valid JSON that matches the schema structure.

Text to analyze:
{text}

Expected JSON Schema:
{schema_json}

Extracted JSON:"""
            
            response = self.generate_text(prompt, generation_config)
            
            if response['success']:
                try:
                    # Try to parse the generated text as JSON
                    generated_text = response['data']['generated_text'].strip()
                    
                    # Find JSON content (remove any markdown formatting)
                    if '```json' in generated_text:
                        json_start = generated_text.find('```json') + 7
                        json_end = generated_text.find('```', json_start)
                        json_content = generated_text[json_start:json_end].strip()
                    elif '{' in generated_text and '}' in generated_text:
                        json_start = generated_text.find('{')
                        json_end = generated_text.rfind('}') + 1
                        json_content = generated_text[json_start:json_end]
                    else:
                        json_content = generated_text
                    
                    extracted_data = json.loads(json_content)
                    
                    logger.info("Structured data extracted successfully")
                    
                    return {
                        'statusCode': 200,
                        'success': True,
                        'data': {
                            'extracted_data': extracted_data,
                            'raw_response': generated_text,
                            'model': self.model
                        }
                    }
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse extracted JSON: {e}")
                    return {
                        'statusCode': 400,
                        'success': False,
                        'error': 'JSONParseError',
                        'message': f'Generated text is not valid JSON: {str(e)}',
                        'raw_response': response['data']['generated_text']
                    }
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to extract structured data: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'StructuredDataError',
                'message': str(e)
            }

    def summarize_text(self, text: str, max_length: int = 500,
                      style: str = "concise") -> Dict[str, Any]:
        """
        Summarize long text content.
        
        Args:
            text (str): Text to summarize
            max_length (int): Maximum length of summary in words
            style (str): Summary style ('concise', 'detailed', 'bullet-points')
            
        Returns:
            Dict: Summary results
        """
        try:
            style_instructions = {
                'concise': 'Provide a concise, brief summary',
                'detailed': 'Provide a comprehensive, detailed summary',
                'bullet-points': 'Provide a summary in bullet-point format'
            }
            
            instruction = style_instructions.get(style, style_instructions['concise'])
            
            prompt = f"""{instruction} of the following text in approximately {max_length} words or less:

Text to summarize:
{text}

Summary:"""
            
            return self.generate_text(prompt)
            
        except Exception as e:
            logger.error(f"Failed to summarize text: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'SummarizationError',
                'message': str(e)
            }

    def translate_text(self, text: str, target_language: str,
                      source_language: str = "auto") -> Dict[str, Any]:
        """
        Translate text to target language.
        
        Args:
            text (str): Text to translate
            target_language (str): Target language (e.g., 'Spanish', 'French', 'Japanese')
            source_language (str): Source language (default: 'auto' for auto-detection)
            
        Returns:
            Dict: Translation results
        """
        try:
            if source_language == "auto":
                prompt = f"Translate the following text to {target_language}:\n\n{text}\n\nTranslation:"
            else:
                prompt = f"Translate the following text from {source_language} to {target_language}:\n\n{text}\n\nTranslation:"
            
            return self.generate_text(prompt)
            
        except Exception as e:
            logger.error(f"Failed to translate text: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'TranslationError',
                'message': str(e)
            }

    def classify_text(self, text: str, categories: List[str],
                     include_confidence: bool = True) -> Dict[str, Any]:
        """
        Classify text into provided categories.
        
        Args:
            text (str): Text to classify
            categories (List[str]): List of possible categories
            include_confidence (bool): Whether to include confidence scores
            
        Returns:
            Dict: Classification results
        """
        try:
            categories_str = ', '.join(categories)
            
            if include_confidence:
                prompt = f"""Classify the following text into one of these categories: {categories_str}

Text to classify:
{text}

Provide your response in JSON format with the following structure:
{{
    "category": "selected_category",
    "confidence": "high/medium/low",
    "reasoning": "brief explanation"
}}

Classification:"""
            else:
                prompt = f"""Classify the following text into one of these categories: {categories_str}

Text to classify:
{text}

Category:"""
            
            response = self.generate_text(prompt)
            
            if response['success'] and include_confidence:
                try:
                    # Try to parse JSON response
                    generated_text = response['data']['generated_text'].strip()
                    if '{' in generated_text and '}' in generated_text:
                        json_start = generated_text.find('{')
                        json_end = generated_text.rfind('}') + 1
                        json_content = generated_text[json_start:json_end]
                        classification_data = json.loads(json_content)
                        response['data']['classification'] = classification_data
                except json.JSONDecodeError:
                    # If JSON parsing fails, keep the raw text
                    pass
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to classify text: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'ClassificationError',
                'message': str(e)
            }

    def generate_embeddings(self, text: str) -> Dict[str, Any]:
        """
        Generate embeddings for text (using embedding model).
        Note: This uses the embedding-specific endpoint.
        
        Args:
            text (str): Text to generate embeddings for
            
        Returns:
            Dict: Embedding vector results
        """
        try:
            # Use embedding model endpoint
            payload = {
                "model": "models/embedding-001",
                "content": {
                    "parts": [{"text": text}]
                }
            }
            
            response = self._make_request("embedContent", payload)
            
            if response['success']:
                embedding = response['data'].get('embedding', {}).get('values', [])
                
                logger.info("Embeddings generated successfully")
                
                return {
                    'statusCode': 200,
                    'success': True,
                    'data': {
                        'embedding': embedding,
                        'dimension': len(embedding),
                        'model': 'embedding-001'
                    }
                }
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'EmbeddingError',
                'message': str(e)
            }

    def count_tokens(self, text: str) -> Dict[str, Any]:
        """
        Count tokens in the provided text.
        
        Args:
            text (str): Text to count tokens for
            
        Returns:
            Dict: Token count information
        """
        try:
            payload = {
                "contents": [
                    {
                        "parts": [{"text": text}]
                    }
                ]
            }
            
            response = self._make_request("countTokens", payload)
            
            if response['success']:
                token_count = response['data'].get('totalTokens', 0)
                
                logger.info(f"Token count: {token_count}")
                
                return {
                    'statusCode': 200,
                    'success': True,
                    'data': {
                        'token_count': token_count,
                        'model': self.model
                    }
                }
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to count tokens: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'TokenCountError',
                'message': str(e)
            }

    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request to Gemini API.
        
        Args:
            endpoint (str): API endpoint
            payload (Dict): Request payload
            
        Returns:
            Dict: API response
        """
        try:
            url = f"{self.base_url}/models/{self.model}:{endpoint}"
            if endpoint in ["embedContent", "countTokens"]:
                # These endpoints don't use model in URL
                url = f"{self.base_url}/models/{endpoint.replace('Content', '-001' if 'embed' in endpoint else self.model.split('-')[0])}:{endpoint}"
            
            url += f"?key={self.api_key}"
            
            # Prepare request
            data = json.dumps(payload).encode('utf-8')
            
            request = Request(url, data=data)
            request.add_header('Content-Type', 'application/json')
            
            # Make request
            with urlopen(request, timeout=60) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                
                return {
                    'statusCode': 200,
                    'success': True,
                    'data': response_data
                }
                
        except HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                error_data = json.loads(error_body)
                error_message = error_data.get('error', {}).get('message', str(e))
            except:
                error_message = error_body or str(e)
            
            logger.error(f"HTTP error {e.code}: {error_message}")
            
            return {
                'statusCode': e.code,
                'success': False,
                'error': f'HTTPError{e.code}',
                'message': error_message
            }
            
        except URLError as e:
            logger.error(f"URL error: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'URLError',
                'message': str(e)
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'JSONDecodeError',
                'message': str(e)
            }
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                'statusCode': 500,
                'success': False,
                'error': 'UnexpectedError',
                'message': str(e)
            }

    def set_generation_config(self, **kwargs) -> None:
        """
        Update default generation configuration.
        
        Args:
            **kwargs: Generation config parameters (temperature, topK, topP, maxOutputTokens)
        """
        self.default_config.update(kwargs)
        logger.info(f"Generation config updated: {kwargs}")

    def set_safety_settings(self, settings: List[Dict[str, str]]) -> None:
        """
        Update default safety settings.
        
        Args:
            settings (List[Dict]): List of safety setting configurations
        """
        self.default_safety_settings = settings
        logger.info("Safety settings updated")
    
    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from generated text, handling common formatting issues.
        
        Args:
            text (str): Generated text that may contain JSON
            
        Returns:
            Dict or None: Parsed JSON object or None if parsing fails
        """
        import re
        
        try:
            # Try direct parsing first
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        try:
            # Remove markdown code blocks
            cleaned = re.sub(r'^```json\n|\n```$', '', text.strip())
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        try:
            # Extract JSON from text (find first { to last })
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        logger.warning(f"Failed to parse JSON from response: {text[:100]}...")
        return None


# Convenience functions
def create_gemini_helper(api_key: str = None, model: str = "gemini-1.5-flash", 
                        session_storage=None) -> GeminiHelper:
    """
    Create a GeminiHelper instance with optional session storage.
    
    Args:
        api_key (str, optional): Google AI API key
        model (str): Model name to use
        session_storage: Storage backend for sessions (DynamoDBHelper, dict, etc.)
        
    Returns:
        GeminiHelper: Initialized Gemini helper instance
    """
    return GeminiHelper(api_key, model, session_storage)


def setup_session_storage(table_name: str = None, region: str = None) -> Any:
    """
    Set up DynamoDB session storage for Gemini conversations.
    
    Args:
        table_name (str, optional): DynamoDB table name for sessions
        region (str, optional): AWS region
        
    Returns:
        DynamoDBHelper instance or dict for in-memory storage
    """
    if table_name:
        try:
            # Try to import and create DynamoDB helper
            from dynamodb_helper import DynamoDBHelper
            return DynamoDBHelper(table_name, region)
        except ImportError:
            logger.warning("DynamoDB helper not available, using in-memory storage")
            return {}
    else:
        # Use in-memory dict storage
        return {}


# Example usage with session management:
"""
import json
from gemini_helper import GeminiHelper, setup_session_storage, lambda_response
from dynamodb_helper import DynamoDBHelper

def lambda_handler(event, context):
    # Set up session storage with DynamoDB
    session_storage = DynamoDBHelper('gemini-sessions')
    
    # Initialize Gemini helper with session support
    gemini = GeminiHelper(session_storage=session_storage)
    
    session_id = event.get('session_id', 'default-session')
    user_message = event.get('message', '')
    user_id = event.get('user_id')
    
    # Chat with session management
    result = gemini.chat_with_session(session_id, user_message)
    
    if result['success']:
        return lambda_response(200, {
            'session_id': session_id,
            'response': result['data']['response'],
            'message_count': result['data']['message_count'],
            'usage': result['data']['usage']
        })
    else:
        return lambda_response(result['statusCode'], {
            'error': result['message']
        })

def session_management_handler(event, context):
    # Handle session management operations
    session_storage = DynamoDBHelper('gemini-sessions')
    gemini = GeminiHelper(session_storage=session_storage)
    
    action = event.get('action')
    session_id = event.get('session_id')
    user_id = event.get('user_id')
    
    if action == 'create':
        result = gemini.create_session(session_id, user_id, event.get('metadata'))
    elif action == 'get':
        result = gemini.get_session(session_id)
    elif action == 'history':
        result = gemini.get_session_history(session_id, event.get('limit'))
    elif action == 'list':
        result = gemini.list_user_sessions(user_id, event.get('limit', 50))
    elif action == 'delete':
        result = gemini.delete_session(session_id)
    elif action == 'clear':
        result = gemini.clear_session_history(session_id, event.get('keep_last', 0))
    else:
        result = {
            'statusCode': 400,
            'success': False,
            'message': 'Invalid action'
        }
    
    return lambda_response(result['statusCode'], result)

def multimodal_chat_handler(event, context):
    # Handle chat with images in sessions
    session_storage = DynamoDBHelper('gemini-sessions')
    gemini = GeminiHelper(session_storage=session_storage)
    
    session_id = event.get('session_id')
    user_message = event.get('message')
    image_data = event.get('image_data')  # Base64 encoded image
    image_mime_type = event.get('image_mime_type', 'image/jpeg')
    
    if image_data:
        # Generate response with image
        result = gemini.generate_text_with_image(user_message, image_data, image_mime_type)
        
        if result['success']:
            # Manually add to session since this isn't using chat_with_session
            user_msg = {'role': 'user', 'content': f"{user_message} [Image attached]"}
            assistant_msg = {'role': 'assistant', 'content': result['data']['generated_text']}
            
            gemini.update_session(session_id, user_msg)
            gemini.update_session(session_id, assistant_msg)
    else:
        # Regular chat with session
        result = gemini.chat_with_session(session_id, user_message)
    
    return lambda_response(result['statusCode'], result)
"""


def lambda_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a standard Lambda response.
    
    Args:
        status_code (int): HTTP status code
        body (Dict): Response body
        
    Returns:
        Dict: Formatted Lambda response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body, default=str)
    }


# Example usage in a Lambda function:
"""
import json
from gemini_helper import GeminiHelper, lambda_response

def lambda_handler(event, context):
    # Initialize Gemini helper
    gemini = GeminiHelper()  # Uses GEMINI_API_KEY environment variable
    
    # Example 1: Simple text generation
    prompt = event.get('prompt', 'Hello, how can I help you today?')
    result = gemini.generate_text(prompt)
    
    if result['success']:
        return lambda_response(200, {
            'message': 'Text generated successfully',
            'generated_text': result['data']['generated_text'],
            'model': result['data']['model']
        })
    else:
        return lambda_response(result['statusCode'], {
            'error': result['message']
        })

def chat_handler(event, context):
    # Handle chat conversations
    gemini = GeminiHelper()
    
    messages = event.get('messages', [])
    result = gemini.chat_conversation(messages)
    
    if result['success']:
        return lambda_response(200, {
            'response': result['data']['response'],
            'usage': result['data']['usage']
        })
    else:
        return lambda_response(result['statusCode'], {
            'error': result['message']
        })

def document_analysis_handler(event, context):
    # Analyze document content
    gemini = GeminiHelper()
    
    document_content = event.get('document_content', '')
    analysis_prompt = event.get('analysis_prompt', 'Summarize this document')
    
    result = gemini.analyze_document(document_content, analysis_prompt)
    
    return lambda_response(result['statusCode'], result)
"""