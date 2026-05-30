"""
Navigation Wrapper for AI Agent Tools
Provides clean way to add navigation to function responses
"""

class NavigationWrapper:
    """Wrapper class to add navigation to function responses"""
    
    @staticmethod
    def add_navigation(func, target_page, condition=None):
        """Add navigation to function response
        
        Args:
            func: Function to wrap
            target_page: Target page for navigation
            condition: Optional condition function to check if navigation should be added
        """
        def wrapper(*args, **kwargs):
            import logging
            logger = logging.getLogger()
            
            logger.info(f"NavigationWrapper: Calling function with target_page={target_page}")
            result = func(*args, **kwargs)
            logger.info(f"NavigationWrapper: Function returned: {type(result)} with keys: {list(result.keys()) if isinstance(result, dict) else 'not dict'}")
            
            # Check if navigation should be added
            should_navigate = True
            if condition:
                should_navigate = condition(result)
                logger.info(f"NavigationWrapper: Condition check result: {should_navigate}")
            elif not result.get('success'):
                should_navigate = False
                logger.info(f"NavigationWrapper: No success in result, should_navigate: {should_navigate}")
            
            # Add navigation if conditions are met
            if should_navigate:
                result['navigation'] = {
                    "action": "navigate_to",
                    "target": target_page
                }
                logger.info(f"NavigationWrapper: Added navigation to {target_page}")
            else:
                logger.info(f"NavigationWrapper: Navigation not added, should_navigate: {should_navigate}")
            
            logger.info(f"NavigationWrapper: Final result keys: {list(result.keys()) if isinstance(result, dict) else 'not dict'}")
            return result
        
        # Preserve original function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__annotations__ = getattr(func, '__annotations__', {})
        
        return wrapper
    
    @staticmethod
    def has_data_condition(result):
        """Condition: navigation only if result has data"""
        return result.get('success') and result.get('data')
    
    @staticmethod
    def success_only_condition(result):
        """Condition: navigation only on success"""
        return result.get('success', False)
    
    @staticmethod
    def custom_condition(check_func):
        """Create custom condition function"""
        return lambda result: check_func(result)