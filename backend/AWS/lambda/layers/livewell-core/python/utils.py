import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional


def isEmptyStr(str: str) -> bool:
    """Check if a string is empty or None"""
    return str is None or str == ""


def generate_uuid() -> str:
    """Generate a unique UUID string"""
    return str(uuid.uuid4())


def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.utcnow().isoformat()


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely parse JSON string with fallback"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """Safely serialize object to JSON with fallback"""
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return default


def extract_user_id_from_event(event: Dict[str, Any]) -> Optional[str]:
    """Extract user ID from Lambda event context"""
    try:
        return event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
    except (KeyError, AttributeError):
        return None


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> Dict[str, Any]:
    """Validate that required fields are present in data"""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        return {
            'valid': False,
            'missing_fields': missing_fields,
            'error': f"Missing required fields: {', '.join(missing_fields)}"
        }
    
    return {'valid': True}