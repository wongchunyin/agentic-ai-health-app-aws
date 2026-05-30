"""
Lambda function to process user preferences from SQS queue
Handles AWS Comprehend + Gemini AI processing in background
"""

import json
import logging
import os
import sys

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Add layers to path
sys.path.append('/opt/python')

def lambda_handler(event, context):
    """Process preference extraction via direct Lambda invocation"""
    
    try:
        from document_manager import DocumentManager
        
        # Parse direct Lambda invocation payload
        user_id = event.get('user_id')
        text = event.get('text')
        
        if not user_id or not text:
            logger.error("Missing user_id or text in event payload")
            return {
                'success': False,
                'error': 'user_id and text are required'
            }
        
        logger.info(f"Processing preference extraction for user: {user_id}")
        
        doc_manager = DocumentManager()
        result = doc_manager.extract_and_save_preferences_sync(user_id, text)
        
        if result['success']:
            logger.info(f"Successfully processed preferences for user: {user_id}")
            return {
                'success': True,
                'message': 'Preferences processed successfully'
            }
        else:
            logger.error(f"Failed to process preferences for user {user_id}: {result.get('error')}")
            return {
                'success': False,
                'error': result.get('error')
            }
        
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }