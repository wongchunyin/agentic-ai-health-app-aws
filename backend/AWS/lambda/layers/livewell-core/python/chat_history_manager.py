"""
Chat History Manager for AI Chatbot
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger()

try:
    from s3_helper import S3Helper
    from dynamodb_helper import DynamoDBHelper
    from config import config
    from document_manager import DocumentManager
except ImportError:
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../aws/python'))
    from s3_helper import S3Helper
    from dynamodb_helper import DynamoDBHelper
    sys.path.append(os.path.dirname(__file__))
    from config import config
    try:
        from document_manager import DocumentManager
    except ImportError:
        DocumentManager = None

class ChatHistoryManager:
    def __init__(self):
        self.s3_chat_history = S3Helper(config.S3_CHAT_HISTORY_BUCKET)
        self.db = DynamoDBHelper(config.DYNAMODB_TABLE_NAME)
        self.docManager = DocumentManager() if DocumentManager else None
        
    def remove_conversation(self, user_id: str, conversation_id: str):
        try:
            if self.docManager:
                resp = self.docManager.delete_document(user_id=user_id, doc_type=config.DOC_TYPE_CHAT_HISTORY, doc_id=conversation_id)
                return resp
            else:
                # Fallback to direct DynamoDB deletion
                db_key = {
                    "PK": f"{config.PK_PREFIX_USER}{user_id}", 
                    "SK": f"{config.SK_PREFIX_CHAT_HISTORY}{conversation_id}"
                }
                return self.db.delete_item(db_key)
        except Exception as e:
            logger.error(f"Error removing conversation: {str(e)}")
            return {"success": False, "error": str(e)}
        
        
    def save_conversation(self, user_id: str, conversation_id: str, messages: List[Dict[str, Any]], chat_session_name: Optional[str] = None) -> Dict[str, Any]:
        """Save conversation messages to storage"""
        try:
            chat_data = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "chat_session_name": chat_session_name or "Default Chat",
                "messages": messages,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            s3_path = f"{user_id}/{conversation_id}.json"
            db_key = {
                "PK": f"{config.PK_PREFIX_USER}{user_id}", 
                "SK": f"{config.SK_PREFIX_CHAT_HISTORY}{conversation_id}"
            }
            
            # Upload to S3
            s3_result = self.s3_chat_history.upload_json(s3_path, chat_data)
            if not s3_result['success']:
                return s3_result
            
            # Save metadata to DynamoDB
            db_item = {
                **db_key,
                "s3_path": s3_path,
                "chat_session_name": chat_data["chat_session_name"],
                "message_count": len(messages),
                "created_at": chat_data["created_at"],
                "updated_at": chat_data["updated_at"]
            }
            
            db_result = self.db.create_item(db_item)
            if not db_result['success']:
                self.s3_chat_history.delete_object(s3_path)
                return {"success": False, "error": db_result['error']}
            
            return {"success": True, "conversation_id": conversation_id}
            
        except Exception as e:
            logger.error(f"Error saving conversation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_conversation(self, user_id: str, conversation_id: str) -> Dict[str, Any]:
        """Get conversation messages from storage"""
        try:
            db_key = {
                "PK": f"{config.PK_PREFIX_USER}{user_id}", 
                "SK": f"{config.SK_PREFIX_CHAT_HISTORY}{conversation_id}"
            }
            
            db_result = self.db.get_item(db_key)
            if not db_result['success']:
                return db_result
            
            s3_path = db_result['data']['s3_path']
            s3_result = self.s3_chat_history.download_json(s3_path)
            if not s3_result['success']:
                return s3_result
            
            return {"success": True, "data": s3_result['data']['content']}
        except Exception as e:
            logger.error(f"Error getting conversation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def add_message(self, user_id: str, conversation_id: str, role: str, content: str, tool_calls: Optional[List[Dict]] = None, tool_responses: Optional[List[Dict]] = None, chat_session_name: Optional[str] = None, hidden_for_user: bool = False) -> Dict[str, Any]:
        """Add a single message to existing conversation with optional tool execution data"""
        try:
            # Get existing conversation
            result = self.get_conversation(user_id, conversation_id)
            
            if result['success']:
                messages = result['data']['messages']
                existing_name = result['data'].get('chat_session_name')
            else:
                # Create new conversation if doesn't exist
                messages = []
                existing_name = None
            
            # Add new message with tool data
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
                "hidden_for_user": hidden_for_user
            }
            
            if tool_calls:
                message["tool_calls"] = tool_calls
            if tool_responses:
                message["tool_responses"] = tool_responses
                
            messages.append(message)
            
            # Save updated conversation
            return self.save_conversation(user_id, conversation_id, messages, chat_session_name or existing_name)
            
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def add_agent_interaction(self, user_id: str, conversation_id: str, user_input: str, agent_response: str, agent_steps: Optional[List[Dict]] = None, chat_session_name: Optional[str] = None, hidden_user_message: bool = False) -> Dict[str, Any]:
        """Add complete agent interaction including tool executions"""
        try:
            result = self.get_conversation(user_id, conversation_id)
            if result['success']:
                messages = result['data']['messages']
                existing_name = result['data'].get('chat_session_name')
            else:
                messages = []
                existing_name = None
            
            # Add user message
            messages.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.utcnow().isoformat(),
                "hidden_for_user": hidden_user_message
            })
            
            # Add agent response with tool execution details
            agent_message = {
                "role": "assistant", 
                "content": agent_response,
                "timestamp": datetime.utcnow().isoformat(),
                "hidden_for_user": False
            }
            
            if agent_steps:
                agent_message["agent_steps"] = agent_steps
                
            messages.append(agent_message)
            
            return self.save_conversation(user_id, conversation_id, messages, chat_session_name or existing_name)
            
        except Exception as e:
            logger.error(f"Error adding agent interaction: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_formatted_history(self, user_id: str, conversation_id: str) -> dict:
        """Get formatted chat history for frontend display"""
        try:
            result = self.get_conversation(user_id, conversation_id)
            if result['success']:
                chat_data = result['data']
                messages = chat_data.get('messages', [])
                
                # Format messages for frontend, filtering out hidden messages
                formatted_messages = []
                for msg in messages:
                    if not msg.get('hidden_for_user', False):
                        formatted_msg = {
                            "role": msg['role'],
                            "content": msg['content'],
                            "timestamp": msg.get('timestamp', ''),
                            "agent_steps": msg.get('agent_steps', [])
                        }
                        formatted_messages.append(formatted_msg)
                
                return {
                    "success": True,
                    "conversation_id": chat_data.get('conversation_id', conversation_id),
                    "chat_session_name": chat_data.get('chat_session_name', "Default Chat"),
                    "messages": formatted_messages,
                    "message_count": len(formatted_messages),
                    "created_at": chat_data.get('created_at', ''),
                    "updated_at": chat_data.get('updated_at', '')
                }
            else:
                return {
                    "success": True,
                    "conversation_id": conversation_id,
                    "chat_session_name": "Default Chat",
                    "messages": [],
                    "message_count": 0
                }
        except Exception as e:
            logger.error(f"Error getting formatted history: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_all_user_conversations(self, user_id: str) -> dict:
        """Get all chat conversations for a user with chat history"""
        try:
            # Query all chat history items for user
            result = self.db.query_items(
                key_condition_expression="PK = :pk AND begins_with(SK, :sk)",
                expression_attribute_values={
                    ":pk": f"{config.PK_PREFIX_USER}{user_id}",
                    ":sk": config.SK_PREFIX_CHAT_HISTORY
                }
            )
            
            if result['success']:
                conversations = []
                for item in result['data']:
                    # Extract conversation_id from SK
                    sk_parts = item['SK'].split('#')
                    if len(sk_parts) > 1:
                        conversation_id = sk_parts[1]
                        
                        # Get full conversation data including messages
                        conv_result = self.get_conversation(user_id, conversation_id)
                        if conv_result['success']:
                            conv_data = conv_result['data']
                            conversations.append({
                                "conversation_id": conversation_id,
                                "chat_session_name": conv_data.get('chat_session_name', 'Default Chat'),
                                "message_count": len(conv_data.get('messages', [])),
                                "created_at": conv_data.get('created_at', ''),
                                "updated_at": conv_data.get('updated_at', ''),
                                "messages": conv_data.get('messages', [])
                            })
                        else:
                            # Fallback to metadata only if S3 fetch fails
                            conversations.append({
                                "conversation_id": conversation_id,
                                "chat_session_name": item.get('chat_session_name', 'Default Chat'),
                                "message_count": item.get('message_count', 0),
                                "created_at": item.get('created_at', ''),
                                "updated_at": item.get('updated_at', ''),
                                "messages": []
                            })
                
                return {
                    "success": True,
                    "conversations": conversations,
                    "total_count": len(conversations)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error getting user conversations: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }