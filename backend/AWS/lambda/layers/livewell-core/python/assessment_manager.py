"""
Assessment Manager for Health Assessments
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import uuid

logger = logging.getLogger()

try:
    from document_manager import DocumentManager
    from config import config
    from schemas import FrailtyAssessmentHistory, FrailtyScoreTypeEnum, AssessmentStatusEnum
except ImportError:
    import os
    import sys
    sys.path.append(os.path.dirname(__file__))
    from document_manager import DocumentManager
    from config import config
    from schemas import FrailtyAssessmentHistory, FrailtyScoreTypeEnum, AssessmentStatusEnum

class AssessmentManager:
    def __init__(self):
        self.doc_manager = DocumentManager()
    
    def save_assessment(self, user_id: str, assessment_data: Dict[str, Any], assessment_type: str, score: float, status: str = None) -> Dict[str, Any]:
        """Save a new assessment"""
        try:
            assessment_id = str(uuid.uuid4())
            
            assessment = FrailtyAssessmentHistory(
                assessment_id=assessment_id,
                timestamp=datetime.utcnow().isoformat(),
                assessment_type=FrailtyScoreTypeEnum(assessment_type),
                score=score,
                assessment_data=assessment_data,
                status=AssessmentStatusEnum(status) if status else None
            )
            
            return self.doc_manager.save_assessment(user_id, assessment_id, assessment)
            
        except Exception as e:
            logger.error(f"Error saving assessment: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_assessment(self, user_id: str, assessment_id: str) -> Dict[str, Any]:
        """Get a specific assessment"""
        try:
            return self.doc_manager.get_single_assessment(user_id, assessment_id, "ALL")
        except Exception as e:
            logger.error(f"Error getting assessment: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_user_assessments(self, user_id: str, status: str = "ALL", limit: int = None) -> Dict[str, Any]:
        """Get assessments for a user with optional limit"""
        try:
            return self.doc_manager.get_multiple_assessments(user_id, status, limit)
        except Exception as e:
            logger.error(f"Error getting user assessments: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_latest_assessment(self, user_id: str, assessment_type: str = None) -> Dict[str, Any]:
        """Get the most recent assessment for a user"""
        try:
            result = self.get_user_assessments(user_id, AssessmentStatusEnum.COMPLETED.value)
            if not result['success']:
                return result
            
            assessments = result['data']
            if not assessments:
                return {"success": True, "data": None}
            
            # Filter by assessment type if specified
            if assessment_type:
                assessments = [a for a in assessments if a.get('assessment_type') == assessment_type]
            
            # Sort by timestamp and get latest
            assessments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            latest = assessments[0] if assessments else None
            
            return {"success": True, "data": latest}
            
        except Exception as e:
            logger.error(f"Error getting latest assessment: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def update_assessment_status(self, user_id: str, assessment_id: str, status: str) -> Dict[str, Any]:
        """Update assessment status"""
        try:
            # Get existing assessment
            result = self.get_assessment(user_id, assessment_id)
            if not result['success']:
                return result
            
            assessment_data = result['data']
            assessment_data['status'] = status
            assessment_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Create updated assessment object
            assessment = FrailtyAssessmentHistory(**assessment_data)
            
            return self.doc_manager.save_assessment(user_id, assessment_id, assessment)
            
        except Exception as e:
            logger.error(f"Error updating assessment status: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def delete_assessment(self, user_id: str, assessment_id: str) -> Dict[str, Any]:
        """Delete an assessment"""
        try:
            return self.doc_manager.delete_document(user_id, config.DOC_TYPE_ASSESSMENT, assessment_id)
        except Exception as e:
            logger.error(f"Error deleting assessment: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_assessment_history(self, user_id: str, limit: int = None) -> Dict[str, Any]:
        """Get assessment history for a user with optional limit"""
        try:
            # Pass limit directly to get_user_assessments for DB-level filtering
            result = self.get_user_assessments(user_id, AssessmentStatusEnum.COMPLETED.value, limit)
            if not result['success']:
                return result
            
            assessments = result['data']
            if not assessments:
                return {"success": True, "data": []}
            
            # Data is already sorted by DynamoDB (scan_index_forward=False)
            return {"success": True, "data": assessments}
            
        except Exception as e:
            logger.error(f"Error getting assessment history: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_unfinished_assessment(self, user_id: str) -> Dict[str, Any]:
        """Check if user has any unfinished assessments"""
        try:
            result = self.get_user_assessments(user_id, AssessmentStatusEnum.INCOMPLETE.value)
            if not result['success']:
                return result

            assessments = result['data']
            if not assessments:
                return {"success": True, "data": None}

            # Data is already sorted by DynamoDB (scan_index_forward=False)
            return {"success": True, "data": assessments[0]}

        except Exception as e:
            logger.error(f"Error getting unfinished assessment: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_assessment_summary(self, user_id: str) -> Dict[str, Any]:
        """Get assessment summary for a user"""
        try:
            result = self.get_user_assessments(user_id, "ALL")
            if not result['success']:
                return result
            
            assessments = result['data']
            
            summary = {
                "total_assessments": len(assessments),
                "completed_assessments": len([a for a in assessments if a.get('status') == AssessmentStatusEnum.COMPLETED.value]),
                "incomplete_assessments": len([a for a in assessments if a.get('status') == AssessmentStatusEnum.INCOMPLETE.value]),
                "assessment_types": list(set(a.get('assessment_type') for a in assessments)),
                "latest_assessment": None,
                "average_score": 0
            }
            
            if assessments:
                # Get latest assessment
                assessments.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                summary["latest_assessment"] = assessments[0]
                
                # Calculate average score for completed assessments
                completed = [a for a in assessments if a.get('status') == AssessmentStatusEnum.COMPLETED.value]
                if completed:
                    scores = [a.get('score', 0) for a in completed]
                    summary["average_score"] = sum(scores) / len(scores)
            
            return {"success": True, "data": summary}
            
        except Exception as e:
            logger.error(f"Error getting assessment summary: {str(e)}")
            return {"success": False, "error": str(e)}