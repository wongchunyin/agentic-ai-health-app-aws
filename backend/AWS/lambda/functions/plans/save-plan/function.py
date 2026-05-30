import json
import logging
from typing import Dict, Any

# Import from layers
try:
    from message_helper import MsgHelper
    from schemas import AACTTPlan, PlanStatusEnum, PlanTypeEnum
    from document_manager import DocumentManager
    from gemini_simple import GeminiSimple
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/message/python'))
    from message_helper import MsgHelper
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/livewell-core/python'))
    from schemas import AACTTPlan, PlanStatusEnum, PlanTypeEnum
    from document_manager import DocumentManager
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/aws/python'))
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/ai-agent/python'))
    from gemini_simple import GeminiSimple


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    try:
        msg_helper = MsgHelper()
       
        user_id = event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('sub')
        if not user_id:
            logger.error("User not authenticated")           
            return msg_helper.error_response('User not authenticated', 401)

        body = json.loads(event.get('body', '{}'))

        # Create plan object with validation
        plan_data = body.get('plan_data', {})
        
        # Generate plan_id if not provided
        if not plan_data.get('plan_id'):
            import uuid
            plan_data['plan_id'] = str(uuid.uuid4())
            logger.info(f"Generated plan_id: {plan_data['plan_id']}")
        
        plan = AACTTPlan(**plan_data)
        plan_type = plan_data.get('plan_type') # manually created plan or generation plan
         
        # plan_type validation with schemas 
        if plan_type not in [e.value for e in PlanTypeEnum]:
            return msg_helper.error_response(f"Invalid plan_type: {plan_type}", 400)

        if plan_type == PlanTypeEnum.MANUALLY_CREATED.value:
            # Validate manually created plan with AI
            doc_manager = DocumentManager()
            validation_result = plan_validation_by_AI(user_id, plan, doc_manager)
            if not validation_result['is_suitable']:
                error_data = {
                    "error": "Plan Safety Validation Failed",
                    "validation_failed": True,
                    "reason": validation_result['reason'],
                    "recommendations": validation_result.get('recommendations'),
                    "message": "Please modify your plan to address these safety concerns and try again."
                }
                
                return msg_helper.format_api_gateway_response(400, error_data)


        # Get action_type from plan's action object or fallback to request body
        action_type = plan_data.get('action', {}).get('action_type') or body.get('plan_type', 'physical')
        status = body.get('status', PlanStatusEnum.ACTIVE.value)
        
        # Initialize DocumentManager if not already done
        if 'doc_manager' not in locals():
            doc_manager = DocumentManager()
        logger.info(f"Saving Plan: {plan_data} | action_type: {action_type} | {status}")
        # Create plan document
        result = doc_manager.save_plan(user_id, plan.plan_id, action_type, plan, status)
        
        if result['success']:
            logger.info(f"Plan created successfully for user_id: {user_id}")
            logger.info(f"Save result: {result}")
            if not result.get('task_id'):
                logger.warning("Task ID is None - schedule task creation may have failed")
            
            # Get the saved plan data to ensure consistency
            saved_plan_result = doc_manager.get_plan(user_id, result['plan_id'])
            if saved_plan_result['success']:
                saved_plan_data = saved_plan_result['data']
            else:
                # Fallback to original plan data if retrieval fails
                saved_plan_data = plan.dict()
            
            # Return complete plan data to frontend
            response_data = {
                'message': "Plan created successfully",
                'success': True,
                'plan_id': result['plan_id'],
                'task_id': result.get('task_id'),
                'plan_data': saved_plan_data  # Return the actual saved plan data
            }
            
            return msg_helper.success_response(response_data)
        else:
            return msg_helper.error_response(result.get('error', 'Failed to create plan'), 400)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return msg_helper.error_response(str(e), 500)


def plan_validation_by_AI(user_id: str, plan: AACTTPlan, doc_manager: DocumentManager) -> Dict[str, Any]:
    """
    Use Gemini AI to validate if the plan is suitable for the user based on their profile and assessment results.
    """
    try:
        # Get user profile
        profile_result = doc_manager.get_user_profile(user_id)
        if not profile_result.get('success'):
            return {'is_suitable': True, 'reason': 'No profile found, allowing plan'}
        
        user_profile = profile_result.get('data', {})
        
        # Get latest assessment results
        assessments = doc_manager.get_all_assessments(user_id)
        latest_assessment = None
        if isinstance(assessments, list) and assessments:
            latest_assessment = max(assessments, key=lambda x: x.get('timestamp', ''))
        
        # Get user preferences
        preferences_result = doc_manager.get_user_preferences(user_id)
        user_preferences = preferences_result.get('data', {}) if preferences_result.get('success') else {}
        
        # Prepare validation prompt
        prompt = f"""
You are a health and fitness expert. Analyze if this exercise plan is suitable for the user.

USER PROFILE:
- Age: {user_profile.get('dob', 'Unknown')}
- Gender: {user_profile.get('gender', 'Unknown')}
- Height: {user_profile.get('height', 'Unknown')} cm
- Weight: {user_profile.get('weight', 'Unknown')} kg

LATEST ASSESSMENT:
{json.dumps(latest_assessment, indent=2) if latest_assessment else 'No assessment available'}

USER PREFERENCES:
{json.dumps(user_preferences, indent=2) if user_preferences else 'No preferences available'}

PROPOSED PLAN:
- Activity: {plan.action.name}
- Description: {plan.action.description}
- Location: {plan.context.location}
- Frequency: {plan.time.frequency.value} times per {plan.time.frequency.unit}
- Duration: {plan.time.duration.value if plan.time.duration else 'Not specified'} {plan.time.duration.unit if plan.time.duration else ''}
- Target: {plan.target}

Analyze if this plan is safe and appropriate for this user. Consider:
1. User's frailty score and physical limitations
2. Age-appropriate exercise intensity
3. Safety concerns based on health conditions
4. Realistic frequency and duration
5. User's activity preferences (likes/dislikes)
6. Alignment with user's preferred activities

Respond with JSON format:
{{
    "is_suitable": true/false,
    "reason": "Brief explanation of your decision",
    "recommendations": "Optional suggestions for improvement"
}}
        """
        
        # Call Gemini for validation
        gemini = GeminiSimple()
        gemini_result = gemini.generate_text(prompt)
        
        if not gemini_result['success']:
            return {
                'is_suitable': True, 
                'reason': f'AI validation service unavailable, allowing plan: {gemini_result.get("error")}'
            }
        
        response = gemini_result['data']['generated_text']
        
        # Parse Gemini response
        try:
            # Extract JSON from response
            response_text = response.strip()
            if '```json' in response_text:
                json_start = response_text.find('{', response_text.find('```json'))
                json_end = response_text.rfind('}') + 1
                response_text = response_text[json_start:json_end]
            elif response_text.startswith('{'):
                pass  # Already JSON format
            else:
                # Find JSON in text
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    response_text = response_text[json_start:json_end]
            
            validation_result = json.loads(response_text)
            
            # Ensure required fields
            if 'is_suitable' not in validation_result:
                validation_result['is_suitable'] = True
            if 'reason' not in validation_result:
                validation_result['reason'] = 'AI validation completed'
                
            return validation_result
            
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse Gemini response as JSON: {response}")
            return {
                'is_suitable': True, 
                'reason': 'AI validation response could not be parsed, allowing plan'
            }
            
    except Exception as e:
        logger.error(f"Error in AI plan validation: {str(e)}")
        return {
            'is_suitable': True, 
            'reason': f'AI validation failed with error, allowing plan: {str(e)}'
        }