import json
import logging

# Import from layers
try:
    from message_helper import MsgHelper
    from medical_search_manager import MedicalSearchManager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/livewell-core/python'))
    from medical_search_manager import MedicalSearchManager

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function for medical Q&A search
    """
    try:
        msgHelper = MsgHelper()
        
        # Parse request body
        body = json.loads(event['body'])
        query = body.get('query', '').strip()
        
        if not query:
            return msgHelper.error_response("Query is required", 400)
        
        # Initialize search manager and perform search
        search_manager = MedicalSearchManager()
        results = search_manager.search(query, top_k=body.get('top_k', 5))
        
        return msgHelper.success_response({
            "results": results,
            "query": query,
            "total_results": len(results)
        })
        
    except Exception as e:
        logger.error(f"Error in medical search: {str(e)}")
        return msgHelper.error_response(f"Internal server error: {str(e)}", 500)