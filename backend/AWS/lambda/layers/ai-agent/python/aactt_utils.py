import os
import random
import uuid
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
try:
    from s3_helper import S3Helper
    from dynamodb_helper import DynamoDBHelper
    from schemas import ActionTypeEnum, PlanTypeEnum
    from gemini_simple import GeminiSimple
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../aws/python'))
    from s3_helper import S3Helper
    from dynamodb_helper import DynamoDBHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../livewell-core/python'))
    from schemas import ActionTypeEnum, PlanTypeEnum
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../ai-agent/python'))
    from gemini_simple import GeminiSimple


BUCKET_NAME="livewell-bucket"


class AACTTUtils():

    def __init__(self, profile_name=None):
        # Lambda environment - no profile support needed
        self.bucket = S3Helper(BUCKET_NAME)
        
    
    def prepare_prompt(self, user_profile: dict, target: str = "health improvement", action_type: str = None, assessment_data: dict = None, existing_plans: list = None):
        # Action-specific instructions
        action_instructions = {
            "physical": "Focus on safe, low-impact exercises that improve strength, balance, and mobility. Consider limitations and safety. IMPORTANT: Avoid repetitive suggestions like chair yoga. Suggest diverse activities such as walking, swimming, tai chi, resistance training, balance exercises, stretching routines, or other varied physical activities.",
            "mental": "Focus on cognitive activities that stimulate the brain, improve memory, and provide mental engagement. Consider activities that are mentally stimulating but not overwhelming.",
            "diet": "Focus on nutritional recommendations that are practical, safe, and appropriate for older adults. Consider dietary restrictions and ease of preparation.",
            "medical": "Focus on health monitoring, medication management, and preventive care activities. Consider safety and medical supervision requirements."
        }
        
        # Context-specific guidance
        context_guidance = {
            "physical": "Consider indoor/outdoor options, safety equipment needed, and assistance requirements.",
            "mental": "Consider quiet environments, good lighting, comfortable seating, and social vs. solitary activities.",
            "diet": "Consider kitchen accessibility, shopping assistance, meal preparation capabilities, and dietary restrictions.",
            "medical": "Consider healthcare facility access, home monitoring options, and caregiver involvement."
        }
        
        prompt = (
            f"You are an expert in creating {action_type.upper()} wellness plans for older adults using the AACTT framework. "
            f"IMPORTANT: You must create a {action_type.upper()} plan only. Do not suggest activities from other categories. "
            f"\n\nUser profile: {user_profile}\n\n"
            f"ACTION TYPE: {action_type.upper()}\n"
            f"Instructions: {action_instructions.get(action_type, '')}\n\n"
            f"CONTEXT GUIDANCE: {context_guidance.get(action_type, '')}\n\n"
            f"TARGET: {target}\n\n"
        )
        
        # Add fitness preferred times for physical activities
        if action_type == "physical" and user_profile and isinstance(user_profile, dict):
            preferred_days = user_profile.get('preferred_fitness_days', [])
            if preferred_days:
                available_times = []
                for day_info in preferred_days:
                    if day_info.get('available') and day_info.get('time_slots'):
                        day = day_info['day'].capitalize()
                        for slot in day_info['time_slots']:
                            start = slot.get('start_time', '')
                            end = slot.get('end_time', '')
                            if start and end:
                                available_times.append(f"{day}: {start}-{end}")
                
                if available_times:
                    prompt += f"PREFERRED FITNESS TIMES: The user has specified these preferred workout times:\n"
                    for time_slot in available_times:
                        prompt += f"- {time_slot}\n"
                    prompt += "Please schedule the physical activity during these preferred times when possible.\n\n"
        
        # Add assessment data for personalization
        if assessment_data and isinstance(assessment_data, dict):
            prompt += "HEALTH ASSESSMENT DATA: Use this information to personalize the plan:\n"
            
            # Check if it's assessment history with multiple assessments
            if 'data' in assessment_data and isinstance(assessment_data['data'], list):
                assessments = assessment_data['data']
                if assessments:
                    latest_assessment = assessments[0]  # Most recent
                    assessment_info = latest_assessment.get('assessment_data', {})
                    score = latest_assessment.get('score', 0)
                    assessment_type = latest_assessment.get('assessment_type', '')
                    
                    prompt += f"- Assessment Type: {assessment_type}\n"
                    prompt += f"- Frailty Score: {score}\n"
                    
                    if assessment_type == 'FRAIL':
                        if assessment_info.get('fatigue'):
                            prompt += "- User experiences fatigue - recommend low-intensity activities\n"
                        if assessment_info.get('resistance'):
                            prompt += "- User has difficulty with stairs - avoid high-impact exercises\n"
                        if assessment_info.get('ambulation'):
                            prompt += "- User has walking difficulties - focus on seated or supported exercises\n"
                        if assessment_info.get('loss_of_weight'):
                            prompt += "- User has recent weight loss - consider nutrition-focused activities\n"
                    
                    # Provide general recommendations based on score
                    if score >= 3:
                        prompt += "- HIGH FRAILTY: Recommend very gentle, low-risk activities with safety considerations\n"
                    elif score >= 1:
                        prompt += "- MODERATE FRAILTY: Recommend moderate activities with some safety precautions\n"
                    else:
                        prompt += "- LOW FRAILTY: Can recommend more active and varied activities\n"
            
            prompt += "Please tailor the activity recommendations based on this health assessment data.\n\n"
        
        # Add existing plans information to avoid duplicates
        if existing_plans and isinstance(existing_plans, list):
            same_type_plans = [p for p in existing_plans if p.get('plan_type') == action_type]
            if same_type_plans:
                prompt += f"EXISTING {action_type.upper()} PLANS: The user already has these {action_type} plans:\n"
                for plan in same_type_plans:
                    action_name = plan.get('action', {}).get('name', 'Unknown')
                    status = plan.get('status', 'unknown')
                    prompt += f"- {action_name} (Status: {status})\n"
                prompt += f"Please create a DIFFERENT {action_type} activity to provide variety and avoid duplication.\n\n"
    
        # if action_list:
        #     for action in action_list:
        #         prompt += f"- {action}\n"
        
        # Time format varies by activity type
        if action_type == "diet":
            time_format = '"time": {"frequency": { "value":1, "unit":"per day/week/month"}, "timing": "when to do (e.g., before meals, morning, evening)", "schedule": "daily" }'
        elif action_type == "physical" and user_profile and user_profile.get('preferred_fitness_days'):
            time_format = '"time": {"frequency": { "value":1, "unit":"per day/week/month"}, "duration":{"value":1, "unit":"hours/minutes/seconds"}, "schedule": "daily", "preferred_times": "use the user\'s preferred fitness times when scheduling" }'
        else:
            time_format = '"time": {"frequency": { "value":1, "unit":"per day/week/month"}, "duration":{"value":1, "unit":"hours/minutes/seconds"}, "schedule": "daily" }'
        
        # Add randomness to ensure unique plans
        import time
        import random
        timestamp = int(time.time())
        random_seed = random.randint(1000, 9999)
        
        prompt += (
            f"\n\nSuggest an appropriate {action_type} activity that provides health benefits for older adults.\n\n"
            f"IMPORTANT: Your response must be a {action_type.upper()} activity only. "
            f"Do not mix with physical, mental, diet, or medical activities from other categories.\n\n"
            f"DIVERSITY REQUIREMENT: Suggest creative and varied activities. Avoid overused suggestions like chair yoga. "
            f"Consider activities like walking, swimming, tai chi, resistance training, balance exercises, stretching, dancing, gardening, or other diverse options.\n\n"
            f"UNIQUENESS: Generate a unique plan (timestamp: {timestamp}, seed: {random_seed}). Each plan should be different and creative.\n\n"
            "Output format (valid JSON):"
            "{"
            f'  "action": {{"action_type": "{action_type}", "name": "{action_type} activity name", "description":"{action_type} activity description"}},'
            '  "actor": "user",'
            '  "context": {"location": "where to perform (indoor/outdoor)", "condition": "under what condition or null"},'
            f'  "target": "{target}",'
            f"  {time_format}"
            "}"
            "\n\nIMPORTANT: For the 'schedule' field, use ONLY one of these exact values: 'daily', 'weekly', or 'monthly'. Do not use any other text."
        )
        return prompt
    
    def get_object_key(self, activity_type: str):
        if activity_type.lower() not in ["physical", "mental", "diet", "medical"]:
            raise ValueError("Activity type must be physical, mental, diet or medical.")

        # First try to list objects to see what's available
        try:
            objects = self.list_s3_objects()
            logger.info(f"Available S3 objects: {[obj.get('key', obj) for obj in objects]}")
        except Exception as e:
            logger.warning(f"Could not list S3 objects: {e}")

        key_map = {
            "physical": "physcial_activities.txt",  # Note: matches actual filename with typo
            "mental": "mental_activities.txt",
            "diet": "diet_activities.txt",
            "medical": "medical_activities.txt"
        }
        return key_map.get(activity_type.lower(), "")

    def list_s3_objects(self):
        try:
            result = self.bucket.list_objects()
            if result['success']:
                return result['data']['objects']
            else:
                print(f"S3 Error: {result['error']} - {result['message']}")
                return []
        except Exception as e:
            print(f"Error listing S3 objects: {e}")
            return []
    
    def get_s3_object_content(self, object_key):
        try:
            if object_key.endswith(".json"):
                result = self.bucket.download_json(object_key)
            else:
                result = self.bucket.download_object(object_key, decode_utf8=True)
            
            if result['success']:
                return result['data']['content']
            else:
                print(f"S3 Error: {result['error']} - {result['message']}")
                return None
        except Exception as e:
            print(f"Error accessing S3: {e}")
            return None

    def get_activity_list_by_type(self, activity_type: str):
        object_key = self.get_object_key(activity_type=activity_type)
        logger.info(f"Looking for S3 key: {object_key}")
        content = self.get_s3_object_content(object_key)
        if content:
            return [line.strip() for line in content.split("\n") if line.strip()]
        else:
            logger.warning(f"No content found for {activity_type} at key: {object_key}")
            return []
    

    def get_random_activities(self, activity_type: str, count: int = 3):

        activities = self.get_activity_list_by_type(activity_type)
        return random.sample(activities, min(count, len(activities)))
    

    def get_activities_for_prompt(self, types: list = None, prompt_size: int = 10):
        if not types:
            types = ["physical", "mental", "diet", "medical"]
        
        prompt_data = {}
        for activity_type in types:
            activities = self.get_activity_list_by_type(activity_type)
            prompt_data[activity_type] = activities[:prompt_size]  # Limit for prompt size
        return prompt_data
    

    def format_activities_for_ai(self, activity_type: str):
        activities = self.get_activity_list_by_type(activity_type)
        return f"{activity_type.title()} activities:\n" + "\n".join(f"- {act}" for act in activities[:15])
    


def generate_aactt_plan(action_type, target: str = None, user_profile: dict = None, assessment_data: dict = None, existing_plans: list = None):
    """Generate AACTT (Action, Actor, Context, Target, Time) plan"""
    import logging
    logger = logging.getLogger()
    
    try:
        logger.info(f"=== STARTING generate_aactt_plan ===")
        logger.info(f"Raw input - action_type: {action_type}, target: {target}")
        
        # Handle ActionTypeEnum objects
        if hasattr(action_type, 'value'):
            action_type = action_type.value
            logger.info(f"Extracted enum value: {action_type}")
        
        # Ensure action_type is string
        action_type = str(action_type).lower()
        logger.info(f"Normalized action_type: {action_type}")
        
        # Generate action-specific target if not provided by user
        if not target:
            action_targets = {
                "physical": "improve strength, balance, and mobility",
                "mental": "enhance cognitive function and mental well-being", 
                "diet": "optimize nutrition and eating habits",
                "medical": "maintain health monitoring and preventive care"
            }
            target = action_targets.get(action_type, "health improvement")
            logger.info(f"Generated target for {action_type}: {target}")
        else:
            logger.info(f"Using user-provided target: {target}")
        
        # Support all action types
        valid_types = ["physical", "mental", "diet", "medical"]
        if action_type not in valid_types:
            error_msg = f"Action type must be one of: {valid_types}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Action type validated: {action_type}")
        
        logger.info("Creating AACTTUtils instance...")
        aactt_utils = AACTTUtils()
        logger.info("AACTTUtils instance created successfully")
        
        logger.info(f"Getting activity list for type: {action_type}")
        # action_list = aactt_utils.get_activity_list_by_type(action_type)
        # logger.info(f"Retrieved {len(action_list)} activities for type: {action_type}")
            
        logger.info("Preparing prompt with personalization data...")
        prompt = aactt_utils.prepare_prompt(user_profile, target, action_type, assessment_data, existing_plans)
        logger.info(f"Prompt prepared successfully (length: {len(prompt)} chars)")
            
        logger.info("Creating GeminiSimple instance...")
        gemini = GeminiSimple()
        logger.info("GeminiSimple instance created, calling generate_text...")
        
        result = gemini.generate_text(prompt, parse_json=True, temperature=0.7)
        logger.info(f"Gemini generate_text completed. Result keys: {list(result.keys()) if isinstance(result, dict) else 'not dict'}")
        logger.info(f"Gemini result success: {result.get('success') if isinstance(result, dict) else 'unknown'}")
            
        if result.get('success') and 'data' in result:
            logger.info("Processing successful Gemini result...")
            raw_text = result['data']['generated_text']
            
            # Extract JSON from markdown code block
            import re
            import json
            import html
            
            json_match = re.search(r'```json\s*\n(.+?)\n```', raw_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                logger.info(f"Extracted raw JSON: {json_str[:200]}...")
                
                # Multiple parsing strategies
                parsing_strategies = [
                    lambda s: s,  # Original
                    lambda s: html.unescape(s),  # Decode HTML entities
                    lambda s: html.unescape(s).replace("'", '"'),  # HTML + quote fix
                    lambda s: re.sub(r"([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:", r'\1"\2":', html.unescape(s)),  # Fix unquoted keys
                    lambda s: re.sub(r'"([^"]*?)"([^":,}\]]*?)"', r'"\1\2"', html.unescape(s).replace("'", '"')),  # Fix nested quotes
                ]
                
                plan_data = None
                for i, strategy in enumerate(parsing_strategies):
                    try:
                        processed_json = strategy(json_str)
                        plan_data = json.loads(processed_json)
                        logger.info(f"Successfully parsed JSON using strategy {i+1}")
                        break
                    except (json.JSONDecodeError, Exception) as e:
                        logger.warning(f"Strategy {i+1} failed: {str(e)[:100]}")
                        continue
                
                if plan_data is None:
                    logger.error(f"All JSON parsing strategies failed")
                    logger.error(f"Original JSON: {json_str}")
                    # Return a fallback plan structure
                    return {
                        "action": {
                            "action_type": action_type,
                            "name": f"{action_type.title()} Activity",
                            "description": f"A {action_type} activity for health improvement"
                        },
                        "actor": "user",
                        "context": {"location": "indoor", "condition": None},
                        "target": target,
                        "time": {"frequency": {"value": 1, "unit": "per day"}, "schedule": "daily"},
                        "error_note": "Generated from fallback due to JSON parsing issues"
                    }
            else:
                logger.error(f"No JSON code block found in response: {raw_text[:500]}...")
                return {"error": "No JSON found in generated response"}
            
            logger.info(f"Plan data type: {type(plan_data)}")
            logger.info(f"Plan data content: {plan_data}")
                
            # Add plan_id to the plan data
            if isinstance(plan_data, dict):
                if not plan_data.get('plan_id'):
                    plan_data['plan_id'] = str(uuid.uuid4())
                # Remove plan_type from plan_data since action_type is now in action object
                plan_data['plan_type'] = PlanTypeEnum.GENERATED.value
                # Clean up any enum objects in the plan data to ensure JSON serialization
                def clean_enums(obj):
                    if isinstance(obj, dict):
                        return {k: clean_enums(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [clean_enums(item) for item in obj]
                    elif hasattr(obj, 'value'):  # Enum object
                        return obj.value
                    else:
                        return obj
                
                plan_data = clean_enums(plan_data)
                logger.info(f"Successfully returning plan with plan_type: {action_type}")
                logger.info(f"=== COMPLETED generate_aactt_plan SUCCESSFULLY ===")
                return plan_data
            else:
                error_msg = f"Invalid plan data format: {type(plan_data)}, content: {plan_data}"
                logger.error(error_msg)
                logger.error(f"Raw Gemini result: {result}")
                return {"error": "Invalid plan format generated"}
        else:
            error_msg = f"Gemini generation failed: {result}"
            logger.error(error_msg)
            return {"error": "Plan generation failed"}
            
    except Exception as e:
        import traceback
        error_msg = f"Error in generate_aactt_plan: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.info(f"=== COMPLETED generate_aactt_plan WITH ERROR ===")
        return {"error": str(e)}
    
if __name__ == "__main__":

    # local testing
    try:
        # Use your AWS profile name here, or None for default
        aactt_utils = AACTTUtils(profile_name="account2")  # Change this to your profile
        
        # First, list available objects
        print("Available objects in bucket:")
        objects = aactt_utils.list_s3_objects()
        for obj in objects:
            print(f"  - {obj['key']} (size: {obj['size']} bytes)")
        
        # Try to download the file
        object_key = "physcial_activities.txt"
        print(f"\nTrying to download: {object_key}")
        content = aactt_utils.get_s3_object_content(object_key)
        if content:
            print("Content:", content)
        
    except Exception as e:
        print(f"Error: {e}")
        print("Configure AWS credentials: aws configure")
        print("Or check your profile name in ~/.aws/credentials")