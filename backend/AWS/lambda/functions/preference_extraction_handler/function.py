import json
import boto3
from typing import Dict, Any

try:
    from message_helper import MsgHelper
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/message/python'))
    from message_helper import MsgHelper

# Initialize AWS clients and helpers
comprehend = boto3.client('comprehend')
msg_helper = MsgHelper()

def lambda_handler(event, context) -> Dict[str, Any]:
    """
    Returns raw AWS Comprehend JSON for external classification
    """
    try:
        # Parse input from different invocation methods
        text = extract_text_from_event(event)
        
        if not text:
            return msg_helper.error_response('No text provided in request', 400, methods='POST,OPTIONS')
        
        # Validate text length (Comprehend limit: 5000 characters)
        if len(text) > 5000:
            text = text[:5000]
            metadata['text_truncated'] = True
        
        # Perform Comprehend analysis
        sentiment = comprehend.detect_sentiment(Text=text, LanguageCode='en')
        entities = comprehend.detect_entities(Text=text, LanguageCode='en')
        key_phrases = comprehend.detect_key_phrases(Text=text, LanguageCode='en')
        
        # Return raw Comprehend results for external processing
        raw_results = {
            'raw_sentiment': sentiment,
            'raw_entities': entities,
            'raw_key_phrases': key_phrases,
            'metadata': {
                'original_text': text,
                'text_length': len(text),
                'processed_chars': min(len(text), 5000),
                'service': 'aws_comprehend',
                'classification_strategy': 'external_processing'
            }
        }
        
        return msg_helper.success_response(raw_results, methods='POST,OPTIONS')
        
    except Exception as e:
        return msg_helper.error_response(f'Internal server error: {str(e)}', 500, methods='POST,OPTIONS')

def extract_text_from_event(event: Dict) -> str:
    """Extract text from various Lambda invocation patterns"""
    # Direct invocation
    if 'text' in event:
        return event['text']
    
    # API Gateway with body
    if 'body' in event:
        try:
            body = json.loads(event['body'])
            return body.get('text', '')
        except:
            return ''
    
    # Query string parameters
    if 'queryStringParameters' in event and event['queryStringParameters']:
        return event['queryStringParameters'].get('text', '')
    
    return ''

