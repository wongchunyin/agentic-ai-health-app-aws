import json
import uuid
from datetime import datetime
from langchain_core.tools import tool

try:
    from assessment_utils import AssessmentUtils
    from schemas import FrailtyScoreTypeEnum, FrailScale, RockwoodMitnitski, FrailtyAssessmentHistory, AssessmentStatusEnum
    from document_manager import DocumentManager
    from assessment_manager import AssessmentManager
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../livewell-core/python'))
    from assessment_utils import AssessmentUtils
    from schemas import FrailtyScoreTypeEnum, FrailScale, RockwoodMitnitski, FrailtyAssessmentHistory, AssessmentStatusEnum
    from document_manager import DocumentManager
    from assessment_manager import AssessmentManager

def get_current_user_id():
    """Helper function to get current user ID from context"""
    return getattr(get_current_user_id, 'user_id', 'unknown')

def _get_assessment_questions_base(assessment_type: str = "FRAIL") -> dict:
    """Get health assessment questions (FRAIL or ROCKWOOD_MITNITSKI)."""
    try:
        assessment_type = assessment_type.strip().upper()
        
        if assessment_type in ['FRAIL_SCALE', 'FRAIL', '']:
            survey = AssessmentUtils.get_FRAIL_survey()
            assessment_type = 'FRAIL'
        elif assessment_type == 'ROCKWOOD_MITNITSKI':
            survey = AssessmentUtils.get_rockwood_mitnitski_survey()
        else:
            return {
                "success": False, 
                "error": f"Unsupported assessment type: {assessment_type}. Supported types: FRAIL, ROCKWOOD_MITNITSKI"
            }
        
        if not survey:
            return {"success": False, "error": "Survey not found"}
        
        return {
            "success": True,
            "assessment_type": assessment_type,
            "survey": survey
        }
        
    except Exception as e:
        return {"success": False, "error": f"Error getting assessment questions: {str(e)}"}

# Dynamic navigation based on assessment type
def _assessment_navigation_wrapper(func):
    """Custom wrapper to handle different assessment types"""
    def wrapper(assessment_type: str = "FRAIL"):
        result = func(assessment_type)
        
        if result.get('success'):
            assessment_type = result.get('assessment_type')
            if assessment_type in ['FRAIL', 'ROCKWOOD_MITNITSKI']:
                result['navigation'] = {
                    "action": "navigate_to",
                    "target": "frailty",
                    "assessment_type": assessment_type
                }
        
        return result
    
    # Preserve metadata
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    wrapper.__annotations__ = getattr(func, '__annotations__', {})
    return wrapper

# Apply navigation wrapper
get_assessment_questions = tool(_assessment_navigation_wrapper(_get_assessment_questions_base))

@tool
def save_assessment(assessment_data: str = "") -> dict:
    """Save health assessment answers and get results."""
    try:
        user_id = get_current_user_id()
        assessment_type = 'FRAIL'
        parsed_data = None
        
        if assessment_data and assessment_data.strip():
            if assessment_data.startswith('{'):
                data = json.loads(assessment_data)
                assessment_type = data.get('assessment_type', 'FRAIL').upper()
                parsed_data = data.get('assessment_data', {})
            else:
                # Parse simple format like "fatigue:yes,resistance:no,ambulation:no,illnesses:2,loss_of_weight:no"
                parsed_data = {}
                try:
                    pairs = assessment_data.split(',')
                    for pair in pairs:
                        if ':' in pair:
                            key, value = pair.split(':', 1)
                            key = key.strip().lower()
                            value = value.strip().lower()
                            
                            if value in ['yes', 'true', '1']:
                                parsed_data[key] = True
                            elif value in ['no', 'false', '0']:
                                parsed_data[key] = False
                            elif value.isdigit():
                                parsed_data[key] = int(value)
                            else:
                                parsed_data[key] = value
                except:
                    parsed_data = None
        
        if not parsed_data:
            return {
                "success": False, 
                "error": "No assessment data found. Please provide data in format: 'fatigue:yes,resistance:no,ambulation:no,illnesses:2,loss_of_weight:no' or use JSON format."
            }
        
        # Map assessment type variations
        if assessment_type in ['FRAIL_SCALE', 'FRAIL']:
            assessment_type = FrailtyScoreTypeEnum.FRAIL_SCALE.value
            assessment_obj = FrailScale(**parsed_data)
        elif assessment_type == 'ROCKWOOD_MITNITSKI':
            assessment_type = FrailtyScoreTypeEnum.ROCKWOOD_MITNITSKI.value
            assessment_obj = RockwoodMitnitski(**parsed_data)
        else:
            return {"success": False, "error": f"Unsupported assessment type: {assessment_type}"}
        
        # Generate new assessment_id
        assessment_id = str(uuid.uuid4())
        
        # Calculate score and interpretation
        score = AssessmentUtils.calculate_score(assessment_type, assessment_obj.dict())
        interpret_score = AssessmentUtils.interpret_score(assessment_type, score)
        
        # Create FrailtyAssessmentHistory
        fah_data = {
            'assessment_id': assessment_id,
            'timestamp': datetime.utcnow().isoformat(),
            'assessment_type': assessment_type,
            'score': score,
            'assessment_data': assessment_obj.dict()
        }
        fah = FrailtyAssessmentHistory(**fah_data)
        
        # Set assessment_result based on status
        if fah.status == AssessmentStatusEnum.COMPLETED:
            fah.assessment_result = interpret_score
        else:
            fah.assessment_result = None
            interpret_score = {'message': 'Assessment incomplete - please answer all questions to get results.'}
        
        # Save assessment
        doc_manager = DocumentManager()
        result = doc_manager.save_assessment(user_id, assessment_id, fah)
        
        if result.get('success'):
            return {
                "success": True,
                "message": f"Assessment {'completed' if fah.status == AssessmentStatusEnum.COMPLETED else 'saved (incomplete)'} successfully",
                "assessment_id": assessment_id,
                "status": fah.status.value if hasattr(fah.status, 'value') else fah.status,
                "assessment_result": interpret_score,
                "score": score
            }
        else:
            return {"success": False, "error": result.get('error', 'Failed to create assessment')}
            
    except Exception as e:
        return {"success": False, "error": f"Error creating assessment: {str(e)}"}

@tool
def get_assessment_history() -> dict:
    """Get user's last 2 completed assessments."""
    try:
        user_id = get_current_user_id()
        assessment_manager = AssessmentManager()
        return assessment_manager.get_assessment_history(user_id, limit=2)
    except Exception as e:
        return {"success": False, "error": f"Error getting assessment history: {str(e)}"}



@tool
def delete_assessment_tool(assessment_id: str) -> dict:
    """Delete an assessment permanently. Use with caution as this cannot be undone."""
    try:
        user_id = get_current_user_id()
        doc_manager = DocumentManager()
        result = doc_manager.delete_document(user_id, 'ASSESSMENT', assessment_id)
        
        if result.get('success'):
            return {
                "success": True,
                "assessment_id": assessment_id,
                "message": f"Assessment {assessment_id} has been deleted permanently"
            }
        else:
            return {
                "success": False,
                "error": result.get('error', 'Failed to delete assessment')
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error deleting assessment: {str(e)}"
        }

def get_assessment_tools():
    """Get all assessment-related tools"""
    return [
        get_assessment_questions,
        save_assessment,
        get_assessment_history,
        delete_assessment_tool
    ]