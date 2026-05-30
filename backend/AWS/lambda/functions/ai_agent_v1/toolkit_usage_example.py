"""
Example usage of the Toolkit for ai_agent function calls

This demonstrates how the ai_agent can use the unified toolkit to call
various lambda functions as tools through Gemini function calling.
"""

import json
from toolkit import Toolkit

def example_usage():
    # Initialize toolkit
    toolkit = Toolkit()
    
    # Example 1: Generate AACTT plan
    try:
        plan = toolkit.generate_aactt_plan(action_type="physical")
        print("AACTT Plan:", plan)
    except Exception as e:
        print(f"AACTT Plan Error: {e}")
    
    # Example 2: Check weather for outdoor activities
    try:
        weather_check = toolkit.check_outdoor_weather(
            location="Adelaide",
            month=12,
            day=25,
            hour=14,
            duration=2
        )
        print("Weather Check:", weather_check)
    except Exception as e:
        print(f"Weather Check Error: {e}")
    
    # Example 3: Get weather forecast
    try:
        forecast = toolkit.get_weather_forecast(location="Sydney")
        print("Weather Forecast:", forecast)
    except Exception as e:
        print(f"Weather Forecast Error: {e}")
    
    # Example 4: Create session
    try:
        session = toolkit.create_session(user_id="user123")
        print("Session Created:", session)
    except Exception as e:
        print(f"Session Creation Error: {e}")

if __name__ == "__main__":
    example_usage()