"""DateTime utilities for weather data processing"""

from datetime import datetime, timezone, timedelta
import re
from typing import Dict, Any, Optional, Union
import pytz

class DateTimeHandler:
    """Handle datetime conversion and timezone operations"""
    
    @staticmethod
    def to_iso_format(dt_input: Union[str, datetime, int], 
                     timezone_str: str = 'UTC') -> Optional[str]:
        """
        Convert various datetime inputs to ISO 8601 format
        Supports: ISO strings, Unix timestamps, human-readable strings
        """
        if not dt_input:
            return None
            
        try:
            # If already ISO format
            if isinstance(dt_input, str) and DateTimeHandler._is_iso_format(dt_input):
                return dt_input
                
            # Convert to datetime object
            dt_obj = DateTimeHandler._parse_datetime(dt_input, timezone_str)
            if not dt_obj:
                return None
                
            # Ensure timezone awareness
            if dt_obj.tzinfo is None:
                dt_obj = dt_obj.replace(tzinfo=timezone.utc)
                
            return dt_obj.isoformat()
            
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _is_iso_format(dt_string: str) -> bool:
        """Check if string is in ISO 8601 format"""
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$'
        return bool(re.match(iso_pattern, dt_string))
    
    @staticmethod
    def _parse_datetime(dt_input: Union[str, datetime, int], 
                       timezone_str: str) -> Optional[datetime]:
        """Parse various datetime inputs to datetime object"""
        try:
            if isinstance(dt_input, datetime):
                return dt_input
                
            elif isinstance(dt_input, (int, float)):
                # Unix timestamp
                return datetime.fromtimestamp(dt_input, timezone.utc)
                
            elif isinstance(dt_input, str):
                # Try ISO format first
                if DateTimeHandler._is_iso_format(dt_input):
                    return datetime.fromisoformat(dt_input.replace('Z', '+00:00'))
                
                # Try common date formats
                return DateTimeHandler._parse_string_formats(dt_input, timezone_str)
                
            return None
            
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _parse_string_formats(dt_string: str, timezone_str: str) -> Optional[datetime]:
        """Parse various string formats"""
        formats = [
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y %H:%M',
            '%m/%d/%Y',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M',
            '%d/%m/%Y',
            '%B %d, %Y %H:%M:%S',
            '%B %d, %Y %H:%M',
            '%B %d, %Y'
        ]
        
        for fmt in formats:
            try:
                dt_obj = datetime.strptime(dt_string, fmt)
                # Apply timezone
                tz = pytz.timezone(timezone_str)
                return tz.localize(dt_obj)
            except ValueError:
                continue
                
        return None
    

    

    

if __name__ == "__main__":
    ## testing
    handler = DateTimeHandler()
    print(handler.to_iso_format("2023-12-01 12:00:00"))