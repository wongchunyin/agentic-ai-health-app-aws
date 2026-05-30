"""
Document Manager for Livewell Core
"""

from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
import json
import logging
import uuid
logger = logging.getLogger()
logger.setLevel(logging.INFO)


import os
import sys

# Import unique config to avoid conflicts
try:
    from livewell_config import livewell_config as config
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from livewell_config import livewell_config as config

try:
    from s3_helper import S3Helper
    from dynamodb_helper import DynamoDBHelper
    from schemas import Profile, Metadata, PlanStatusEnum, FrailtyAssessmentHistory, ActionTypeEnum, UserPreferences
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/aws/python'))
    from s3_helper import S3Helper
    from dynamodb_helper import DynamoDBHelper 
    sys.path.append(os.path.join(os.path.dirname(__file__), '../../layers/livewell-core/python'))
    from schemas import Profile, Metadata, PlanStatusEnum, FrailtyAssessmentHistory, ActionTypeEnum, UserPreferences

class DocumentManager:
    def __init__(self):
        logger.info(f"Initializing S3 helpers with buckets: profiles={config.S3_PROFILES_BUCKET}, plans={config.S3_PLANS_BUCKET}, chat={config.S3_CHAT_HISTORY_BUCKET}")
        self.s3_profile = S3Helper(config.S3_PROFILES_BUCKET)
        self.s3_plan = S3Helper(config.S3_PLANS_BUCKET)
        self.s3_chat_history = S3Helper(config.S3_CHAT_HISTORY_BUCKET)
        self.db = DynamoDBHelper(config.DYNAMODB_TABLE_NAME)
    
    def _get_s3_path(self, user_id: str, doc_type: str, doc_id: str = None) -> str:
        if doc_type == config.DOC_TYPE_PROFILE:
            return f"{user_id}/profile.json"
        elif doc_type == config.DOC_TYPE_PLAN:
            return f"{user_id}/plan_{doc_id}.json"
        elif doc_type == config.DOC_TYPE_ASSESSMENT:
            return f"{user_id}/assessment_{doc_id}.json"
        elif doc_type == config.DOC_TYPE_CHAT_HISTORY:
            return f"{user_id}/{doc_id}.json"
        else:
            raise ValueError(f"Unknown document type: {doc_type}")
    
    def _get_dynamodb_key(self, user_id: str, doc_type: str, doc_id: str = "") -> Dict[str, str]:
        if doc_type == config.DOC_TYPE_PROFILE:
            return {"PK": f"{config.PK_PREFIX_USER}{user_id}", "SK": "PROFILE"}
        elif doc_type == config.DOC_TYPE_PLAN:
            return {"PK": f"{config.PK_PREFIX_USER}{user_id}", "SK": f"{config.SK_PREFIX_PLAN}{doc_id}"}
        elif doc_type == config.DOC_TYPE_ASSESSMENT:
            return {"PK": f"{config.PK_PREFIX_USER}{user_id}", "SK": f"{config.SK_PREFIX_ASSESSMENT}{doc_id}"}
        elif doc_type == config.DOC_TYPE_CHAT_HISTORY:
            return {"PK": f"{config.PK_PREFIX_USER}{user_id}", "SK": f"{config.SK_PREFIX_CHAT_HISTORY}{doc_id}"}
        elif doc_type == config.DOC_TYPE_PREFERENCES:
            return {"PK": f"{config.PK_PREFIX_USER}{user_id}", "SK": f"{config.SK_PREFIX_PREFERENCES}{doc_id}"}
        elif doc_type == config.DOC_TYPE_FAILURE_LOG:
            return {"PK": f"{config.PK_PREFIX_FAILURE_LOG}{user_id}", "SK": f"{doc_id}"}
        elif doc_type == "SCHEDULE_TASK":
            return {"PK": f"SCHEDULE#{user_id}", "SK": f"TASK#{doc_id}"}
        else:
            raise ValueError(f"Unknown document type: {doc_type}")
    
    def _get_s3_bucket(self, doc_type: str):
        logger.info(f"Getting S3 bucket for doc_type: {doc_type}")
        if doc_type == config.DOC_TYPE_PROFILE:
            logger.info(f"Using profile bucket: {config.S3_PROFILES_BUCKET}")
            return self.s3_profile
        elif doc_type == config.DOC_TYPE_PLAN:
            logger.info(f"Using plan bucket: {config.S3_PLANS_BUCKET}")
            return self.s3_plan
        elif doc_type == config.DOC_TYPE_ASSESSMENT:
            logger.info(f"Using profile bucket for assessment: {config.S3_PROFILES_BUCKET}")
            return self.s3_profile  # Use profile bucket for assessments
        elif doc_type == config.DOC_TYPE_CHAT_HISTORY:
            logger.info(f"Using chat history bucket: {config.S3_CHAT_HISTORY_BUCKET}")
            return self.s3_chat_history # Use profile bucket for chat history
        else:
            raise ValueError(f"Unknown document type: {doc_type}")
        

    def delete_document(self, user_id: str, doc_type: str, doc_id: str) -> Dict[str, Any]:
        try:
            db_key = self._get_dynamodb_key(user_id, doc_type, doc_id)

            # For preferences, only delete from DynamoDB
            if doc_type == config.DOC_TYPE_PREFERENCES:
                db_result = self.db.delete_item(db_key)
                if not db_result['success']:
                    return {"success": False, "error": db_result['error']}
                return {"success": True}
            
            # For other document types, delete from both S3 and DynamoDB
            s3_path = self._get_s3_path(user_id, doc_type, doc_id)
            s3_bucket = self._get_s3_bucket(doc_type)
            s3_result = s3_bucket.delete_object(s3_path)
            if not s3_result['success']:
                return s3_result

            db_result = self.db.delete_item(db_key)
            if not db_result['success']:
                return {"success": False, "error": db_result['error']}

            return {"success": True}
        except Exception as e:
            logger.error(f"Error in delete_document: {str(e)}")
            raise e    

    def save_assessment(self, user_id: str, assessment_id: str, assessment: FrailtyAssessmentHistory) -> Dict[str, Any]:
        try:

            s3_path = self._get_s3_path(user_id, config.DOC_TYPE_ASSESSMENT, assessment_id)
            db_key = self._get_dynamodb_key(user_id, config.DOC_TYPE_ASSESSMENT, assessment_id)
      

            if not assessment.metadata:
                assessment.metadata = Metadata(
                created_at=datetime.utcnow().isoformat(),
                source="document_manager",
                updated_at= datetime.utcnow().isoformat()
            )


            logger.info("Uploading to S3...")
            s3_result = self.s3_profile.upload_json(s3_path, assessment.dict())
            logger.info("S3 upload call completed")
            if not s3_result['success']:
                logger.error(f"S3 upload failed: {s3_result}")
                return s3_result

            logger.info("Creating DB item...")
            db_item = {
                **db_key,
                "s3_path": s3_path,
                "status": assessment.status
            }
            logger.info(f"DB item: {db_item}")
  

            db_result = self.db.create_item(db_item)
            logger.info("DB create_item call completed")
            if not db_result['success']:
                logger.error(f"DB create failed: {db_result}")
                self.s3_profile.delete_object(s3_path)
                return { "success": False, "error": db_result['error']}
            logger.info("DB create successful")


            return {"success": True, "s3_path": s3_path, "assessment_id": assessment_id}
        except Exception as e:
            logger.error(f"Error in save_assessment: {str(e)}")
            raise e


    def get_multiple_assessments(self, user_id: str, status: str, limit: int = None) -> Dict[str, Any]:
        try:
            # Build query parameters for DynamoDB
            pk = f"{config.PK_PREFIX_USER}{user_id}"
            sk_prefix = config.SK_PREFIX_ASSESSMENT
            
            # Query expression to get assessments for user
            key_condition_expression = "PK = :pk AND begins_with(SK, :sk_prefix)"
            expression_attribute_values = {
                ':pk': pk,
                ':sk_prefix': sk_prefix
            }
            
            # Add status filter if not ALL
            filter_expression = None
            if status != 'ALL':
                filter_expression = "#status = :status"
                expression_attribute_values[':status'] = status
                expression_attribute_names = {'#status': 'status'}
            else:
                expression_attribute_names = None
            
            logger.info(f"🔍 Querying assessments for user: {user_id}, status: {status}, limit: {limit}")
            
            # Add limit and scan_index_forward for most recent first
            query_params = {
                'key_condition_expression': key_condition_expression,
                'expression_attribute_values': expression_attribute_values,
                'scan_index_forward': False  # Get most recent first
            }
            
            if expression_attribute_names:
                query_params['expression_attribute_names'] = expression_attribute_names
            if filter_expression:
                query_params['filter_expression'] = filter_expression
            if limit:
                query_params['limit'] = limit
            
            db_result = self.db.query_items(**query_params)
            
            if db_result['success']:
                bucket = self._get_s3_bucket(config.DOC_TYPE_ASSESSMENT)
                assessments = []
                logger.info(f"Found {len(db_result['data'])} assessment records")
                
                for item in db_result['data']:
                    if 's3_path' not in item:
                        logger.error(f"Missing s3_path in item: {item}")
                        continue
                        
                    s3_path = item['s3_path']
                    s3_result = bucket.download_json(s3_path)
                    if s3_result['success'] and s3_result.get('data') and s3_result['data'].get('content'):
                        assessments.append(s3_result['data']['content'])
                    else:
                        logger.warning(f"Failed to download assessment from S3: {s3_path}")
                        
                return {"success": True, "data": assessments}
            else:
                return db_result
                
        except Exception as e:
            logger.error(f"Error in get_multiple_assessments: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_single_assessment(self, user_id: str, assessment_id: str, status: str) -> Dict[str, Any]:
        """Get assessment from S3 and DynamoDB"""
        return self.get_document(user_id, config.DOC_TYPE_ASSESSMENT, assessment_id)
    
    def get_all_assessments(self, user_id: str) -> Dict[str, Any]:
        """Get all assessments for a user"""
        try:
            pk = f"{config.PK_PREFIX_USER}{user_id}"
            sk_prefix = config.SK_PREFIX_ASSESSMENT
            
            key_condition_expression = "PK = :pk AND begins_with(SK, :sk_prefix)"
            expression_attribute_values = {
                ':pk': pk,
                ':sk_prefix': sk_prefix
            }
            
            db_result = self.db.query_items(
                key_condition_expression=key_condition_expression,
                expression_attribute_values=expression_attribute_values,
                scan_index_forward=False  # Get most recent first
            )
            
            if db_result['success']:
                bucket = self._get_s3_bucket(config.DOC_TYPE_ASSESSMENT)
                assessments = []
                
                for item in db_result['data']:
                    if 's3_path' not in item:
                        continue
                        
                    s3_path = item['s3_path']
                    s3_result = bucket.download_json(s3_path)
                    if s3_result['success'] and s3_result.get('data') and s3_result['data'].get('content'):
                        assessments.append(s3_result['data']['content'])
                        
                return assessments
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error in get_all_assessments: {str(e)}")
            return []

    def create_profile(self, profile: Profile) -> Dict[str, Any]:
        """Create new profile (overwrites existing)"""
        s3_path = self._get_s3_path(profile.user_id, config.DOC_TYPE_PROFILE)
        db_key = self._get_dynamodb_key(profile.user_id, config.DOC_TYPE_PROFILE)
        
        if not profile.metadata:
            profile.metadata = Metadata(
                created_at=datetime.utcnow().isoformat(),
                source="document_manager",
                updated_at=datetime.utcnow().isoformat()
            )
        
        s3_result = self.s3_profile.upload_json(s3_path, profile.dict())
        if not s3_result['success']:
            return s3_result
        
        name = profile.full_name if profile.allowShareName else "Anonymous"
        
        db_item = {
            **db_key,
            "s3_path": s3_path,
            "username": name,
            "country": profile.address.country if profile.address else None,
            "city": profile.address.city if profile.address else None,
            "score": profile.activity_score,
            "allowShareName": profile.allowShareName,
            "allowSMS": profile.allowSMS,
            "allowEmail": profile.allowEmail,
            "created_at": profile.metadata.created_at,
            "updated_at": profile.metadata.updated_at
        }
        
        db_result = self.db.create_item(db_item)
        if not db_result['success']:
            self.s3_profile.delete_object(s3_path)
            return {"success": False, "error": db_result['error']}

        return {"success": True, "s3_path": s3_path, "profile": profile.dict()}
    
    def update_profile(self, profile: Profile) -> Dict[str, Any]:
        """Update existing profile (preserves existing fields)"""
        try:
            s3_path = self._get_s3_path(profile.user_id, config.DOC_TYPE_PROFILE)
            db_key = self._get_dynamodb_key(profile.user_id, config.DOC_TYPE_PROFILE)
            
            # Get existing profile to merge with new data
            existing_result = self.get_user_profile(profile.user_id)
            if existing_result['success']:
                existing_data = existing_result['data']
                new_data = profile.dict()
                
                # Merge: only update fields that are not None in new data
                merged_data = existing_data.copy()
                for key, value in new_data.items():
                    if value is not None:
                        merged_data[key] = value
                
                # Update metadata
                if not merged_data.get('metadata'):
                    merged_data['metadata'] = {}
                merged_data['metadata']['updated_at'] = datetime.utcnow().isoformat()
                merged_data['metadata']['source'] = "document_manager"
            else:
                # If no existing profile, use new profile data
                merged_data = profile.dict()
                if not profile.metadata:
                    merged_data['metadata'] = {
                        'updated_at': datetime.utcnow().isoformat(),
                        'source': "document_manager"
                    }
            
            s3_result = self.s3_profile.upload_json(s3_path, merged_data)
            if not s3_result['success']:
                return s3_result
            
            # Update username based on allowShareName
            name = profile.full_name if profile.allowShareName else "Anonymous"
            
            # Build update expression dynamically
            update_parts = ["s3_path = :s3_path", "updated_at = :updated_at", "username = :username"]
            attr_values = {
                ":s3_path": s3_path,
                ":updated_at": datetime.utcnow().isoformat(),
                ":username": name
            }
            
            # Add optional fields if they exist
            if profile.address and profile.address.country:
                update_parts.append("country = :country")
                attr_values[":country"] = profile.address.country
                
            if profile.address and profile.address.city:
                update_parts.append("city = :city")
                attr_values[":city"] = profile.address.city
            
            if profile.allowShareName:
                update_parts.append("allowShareName = :allowShareName")
                attr_values[":allowShareName"] = profile.allowShareName
            
            if profile.allowSMS is not None:
                update_parts.append("allowSMS = :allowSMS")
                attr_values[":allowSMS"] = profile.allowSMS
                
            if profile.allowEmail is not None:
                update_parts.append("allowEmail = :allowEmail")
                attr_values[":allowEmail"] = profile.allowEmail
                
            update_expression = "SET " + ", ".join(update_parts)
            
            db_result = self.db.update_item(
                key=db_key,
                update_expression=update_expression,
                expression_attribute_values=attr_values
            )
            
            if not db_result['success']:
                return {"success": False, "error": db_result['error']}
            
            return {"success": True, "s3_path": s3_path, "profile": profile.dict()}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_profile(self, profile: Profile) -> Dict[str, Any]:
        """Legacy method - defaults to create_profile"""
        return self.create_profile(profile)

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get profile from S3 and DynamoDB with activity_score from DynamoDB"""
        db_key = self._get_dynamodb_key(user_id, config.DOC_TYPE_PROFILE)
        db_result = self.db.get_item(db_key)
        if not db_result['success']:
            return db_result
        
        s3_path = db_result['data']['s3_path']
        s3_result = self._get_s3_bucket(config.DOC_TYPE_PROFILE).download_json(s3_path)
        if not s3_result['success']:
            return s3_result
        
        content = s3_result['data']['content']
        # Override activity_score with DynamoDB value
        content['activity_score'] = db_result['data'].get('score')
        
        return {"success": True, "data": content, "s3_path": s3_path}
    
    def get_document(self, user_id: str, doc_type: str, doc_id: str = None) -> Dict[str, Any]:
        db_key = self._get_dynamodb_key(user_id, doc_type, doc_id)
        logger.info(f"🔍 DB_KEY: {db_key}")
        db_result = self.db.get_item(db_key)
        if not db_result['success']:
            return db_result
        
        # For preferences, return data directly from DynamoDB
        if doc_type == config.DOC_TYPE_PREFERENCES:
            return {"success": True, "data": db_result['data']}
        
        # For other document types, get from S3
        s3_path = db_result['data']['s3_path']
        logger.info(f"Downloading from S3 path: {s3_path} for doc_type: {doc_type}")
        s3_result = self._get_s3_bucket(doc_type).download_json(s3_path)
        if not s3_result['success']:
            logger.error(f"S3 download failed for {s3_path}: {s3_result}")
            return s3_result
        
        # Add DynamoDB metadata to S3 content for plans
        content = s3_result['data']['content']
        if doc_type == config.DOC_TYPE_PLAN:
            content['plan_id'] = db_result['data'].get('plan_id')
            content['status'] = db_result['data'].get('status')
            content['created_at'] = db_result['data'].get('created_at', '')
        
        return {"success": True, "data": content, "s3_path": s3_path}
    
    def get_plan(self, user_id: str, plan_id: str) -> Dict[str, Any]:
        """Get plan from S3 and DynamoDB"""
        return self.get_document(user_id, config.DOC_TYPE_PLAN, plan_id)
    
    def get_multiple_plans(self, user_id: str) -> Dict[str, Any]:
        """Get all plans for a user"""
        try:
            pk = f"{config.PK_PREFIX_USER}{user_id}"
            sk_prefix = config.SK_PREFIX_PLAN
            
            key_condition_expression = "PK = :pk AND begins_with(SK, :sk_prefix)"
            expression_attribute_values = {
                ':pk': pk,
                ':sk_prefix': sk_prefix
            }
            
            db_result = self.db.query_items(
                key_condition_expression=key_condition_expression,
                expression_attribute_values=expression_attribute_values
            )
            
            if db_result['success']:
                plans = []
                for item in db_result['data']:
                    s3_path = item['s3_path']
                    s3_result = self.s3_plan.download_json(s3_path)
                    if s3_result['success'] and s3_result.get('data') and s3_result['data'].get('content'):
                        plan_content = s3_result['data']['content']
                        # Add metadata from DynamoDB
                        plan_content['plan_id'] = item.get('plan_id')
                        plan_content['status'] = item.get('status')
                        plan_content['created_at'] = item.get('created_at', '')
                        plans.append(plan_content)
                
                return {"success": True, "data": plans}
            else:
                return db_result
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_plans(self, user_id: str) -> Dict[str, Any]:
        """Get all plans for a user - alias for get_multiple_plans"""
        return self.get_multiple_plans(user_id)
    
    def update_score(self, user_id: str, score_type: str, operation: str, amount: int) -> Dict[str, Any]:
        """Update user score (increase/decrease)"""
        try:
            db_key = self._get_dynamodb_key(user_id, config.DOC_TYPE_PROFILE)
            
            # Get current profile to update S3
            profile_result = self.get_user_profile(user_id)
            if not profile_result['success']:
                return {"success": False, "error": "Profile not found"}
            
            profile_data = profile_result['data']
            current_score = profile_data.get(score_type, 0) or 0
            
            # Calculate new score
            if operation == 'increase':
                new_score = current_score + amount
            else:  # decrease
                new_score = max(0, current_score - amount)  # Don't go below 0
            
            # Update profile data
            profile_data[score_type] = new_score
            profile_data['metadata']['updated_at'] = datetime.utcnow().isoformat()
            
            # Update S3
            s3_path = self._get_s3_path(user_id, config.DOC_TYPE_PROFILE)
            s3_result = self.s3_profile.upload_json(s3_path, profile_data)
            if not s3_result['success']:
                return s3_result
            
            # Update DynamoDB score field
            update_expression = "SET score = :score, updated_at = :updated_at"
            attr_values = {
                ":score": new_score,
                ":updated_at": datetime.utcnow().isoformat()
            }
            
            db_result = self.db.update_item(
                key=db_key,
                update_expression=update_expression,
                expression_attribute_values=attr_values
            )
            
            if not db_result['success']:
                return {"success": False, "error": db_result['error']}
            
            return {
                "success": True,
                "score_type": score_type,
                "operation": operation,
                "amount": amount,
                "previous_score": current_score,
                "new_score": new_score
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_schedule_task(self, user_id: str, plan_id: str, action_type: str, plan_data: dict, plan_status: str = 'ACTIVE') -> Dict[str, Any]:
        """Create schedule task item for monitoring user activity"""
        try:
            logger.info(f"Creating schedule task for user_id: {user_id}, plan_id: {plan_id}, action_type: {action_type}")
            task_id = str(uuid.uuid4())
            db_key = self._get_dynamodb_key(user_id, "SCHEDULE_TASK", task_id)
            logger.info(f"Generated task_id: {task_id}, db_key: {db_key}")
            
            # Extract schedule from plan data - handle nested time structure
            time_data = plan_data.get('time', {})
            logger.info(f"Time data from plan: {time_data}")
            if isinstance(time_data, dict):
                schedule_time = time_data.get('schedule', 'daily')
            else:
                schedule_time = 'daily'  # fallback
            logger.info(f"Schedule time: {schedule_time}")
            
            # Calculate next execution based on schedule
            now = datetime.utcnow()
            if schedule_time == 'daily':
                next_exec = now + timedelta(days=1)
            elif schedule_time == 'weekly':
                next_exec = now + timedelta(weeks=1)
            elif schedule_time == 'monthly':
                next_exec = now + timedelta(days=30)
            else:
                next_exec = now + timedelta(days=1)  # default to daily
            
            task_item = {
                **db_key,
                "user_id": user_id,
                "plan_id": plan_id,
                "action_type": action_type,
                "schedule_time": schedule_time,
                "status": "ACTIVE" if plan_status == 'active' else "INACTIVE",
                "created_at": int(now.timestamp()),
                "updated_at": int(now.timestamp()),
                "last_execution": None,
                "next_execution": int(next_exec.timestamp()),
                "cnt_activity_done": 0, # count of completed activities
                "target": time_data.get('frequency').get('value'),
                "finished_cycle" : 0 # count of finished cycles
            }
            logger.info(f"Task item to create: {task_item}")
            
            db_result = self.db.create_item(task_item)
            logger.info(f"DynamoDB create_item result: {db_result}")
            if not db_result['success']:
                logger.error(f"Failed to create schedule task: {db_result['error']}")
                return {"success": False, "error": db_result['error']}
            
            logger.info(f"Successfully created schedule task with task_id: {task_id}")
            return {"success": True, "task_id": task_id}
            
        except Exception as e:
            logger.error(f"Exception in create_schedule_task: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_schedule_tasks(self, user_id: str) -> Dict[str, Any]:
        """Get all schedule tasks for a user"""
        try:
            pk = f"SCHEDULE#{user_id}"
            sk_prefix = "TASK#"
            
            key_condition_expression = "PK = :pk AND begins_with(SK, :sk_prefix)"
            expression_attribute_values = {
                ':pk': pk,
                ':sk_prefix': sk_prefix
            }
            
            db_result = self.db.query_items(
                key_condition_expression=key_condition_expression,
                expression_attribute_values=expression_attribute_values
            )
            
            if db_result['success']:
                return {"success": True, "data": db_result['data']}
            else:
                return db_result
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_plan_status(self, user_id: str, plan_id: str, new_status: str) -> Dict[str, Any]:
        """Update plan status in DynamoDB"""
        try:
            valid_statuses = [e.value for e in PlanStatusEnum]
            if new_status not in valid_statuses:
                return {"success": False, "error": f"Status must be one of: {', '.join(valid_statuses)}"}
            
            db_key = self._get_dynamodb_key(user_id, config.DOC_TYPE_PLAN, plan_id)
            
            update_expression = "SET #status = :status, updated_at = :updated_at"
            expression_attribute_names = {"#status": "status"}
            expression_attribute_values = {
                ":status": new_status,
                ":updated_at": datetime.utcnow().isoformat()
            }
            
            db_result = self.db.update_item(
                key=db_key,
                update_expression=update_expression,
                expression_attribute_names=expression_attribute_names,
                expression_attribute_values=expression_attribute_values
            )
            
            if not db_result['success']:
                return {"success": False, "error": db_result['error']}
            
            # Update corresponding schedule task status
            task_status = "ACTIVE" if new_status == PlanStatusEnum.ACTIVE.value else "INACTIVE"
            self.update_schedule_task_status(user_id, plan_id, task_status)
            
            return {"success": True, "plan_id": plan_id, "new_status": new_status}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_schedule_task_status(self, user_id: str, plan_id: str, status: str) -> Dict[str, Any]:
        """Update schedule task status to ACTIVE or INACTIVE by plan_id"""
        try:
            if status not in ['ACTIVE', 'INACTIVE']:
                return {"success": False, "error": "Status must be ACTIVE or INACTIVE"}
            
            # First, find tasks with the given plan_id
            pk = f"SCHEDULE#{user_id}"
            sk_prefix = "TASK#"
            
            key_condition_expression = "PK = :pk AND begins_with(SK, :sk_prefix)"
            filter_expression = "plan_id = :plan_id"
            expression_attribute_values = {
                ':pk': pk,
                ':sk_prefix': sk_prefix,
                ':plan_id': plan_id
            }
            
            query_result = self.db.query_items(
                key_condition_expression=key_condition_expression,
                filter_expression=filter_expression,
                expression_attribute_values=expression_attribute_values
            )
            
            if not query_result['success']:
                return {"success": False, "error": query_result['error']}
            
            tasks = query_result['data']
            if not tasks:
                return {"success": False, "error": "No tasks found for the given plan_id"}
            
            # Update status for all found tasks
            updated_tasks = []
            for task in tasks:
                task_key = {"PK": task['PK'], "SK": task['SK']}
                
                update_expression = "SET #status = :status, updated_at = :updated_at"
                update_values = {
                    ":status": status,
                    ":updated_at": int(datetime.utcnow().timestamp())
                }
                update_names = {"#status": "status"}
                
                update_result = self.db.update_item(
                    key=task_key,
                    update_expression=update_expression,
                    expression_attribute_values=update_values,
                    expression_attribute_names=update_names
                )
                
                if update_result['success']:
                    updated_tasks.append(task['SK'].replace('TASK#', ''))
            
            return {
                "success": True,
                "plan_id": plan_id,
                "status": status,
                "updated_tasks": updated_tasks
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_overdue_schedule_tasks(self) -> Dict[str, Any]:
        """Get all schedule tasks where next_execution is past due"""
        try:
            current_time = int(datetime.utcnow().timestamp())
            yesterday_time = current_time - 86400  # 24 hours ago
            
            # Scan all schedule tasks (since we need to check across all users)
            filter_expression = "begins_with(PK, :pk_prefix) AND begins_with(SK, :sk_prefix) AND next_execution <= :current_time AND #status = :status"
            expression_attribute_values = {
                ':pk_prefix': 'SCHEDULE#',
                ':sk_prefix': 'TASK#',
                ':current_time': current_time,
                ':status': 'ACTIVE'
            }
            expression_attribute_names = {
                '#status': 'status'
            }
            
            db_result = self.db.scan_items(
                filter_expression=filter_expression,
                expression_attribute_values=expression_attribute_values,
                expression_attribute_names=expression_attribute_names
            )
            
            if db_result['success']:
                return {"success": True, "data": db_result['data']}
            else:
                return db_result
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def batch_update_schedule_tasks(self, tasks: list) -> Dict[str, Any]:
        """Batch update multiple schedule tasks"""
        try:
            updated_count = 0
            failed_count = 0
            
            for task in tasks:
                task_key = {"PK": task['PK'], "SK": task['SK']}
                
                cnt_activity_done = task.get('cnt_activity_done', 0)
                target = task.get('target', 0)
                
                update_expression = "SET cnt_activity_done = :cnt, next_execution = :next_exec, updated_at = :updated_at"
                attr_values = {
                    ":cnt": cnt_activity_done,
                    ":next_exec": task.get('next_execution'),
                    ":updated_at": int(datetime.utcnow().timestamp())
                }
                
                # Increment finished_cycle if cnt_activity_done >= target
                if target and cnt_activity_done >= target:
                    update_expression += ", finished_cycle = finished_cycle + :cycle_inc"
                    attr_values[":cycle_inc"] = 1
                
                if task.get('last_execution'):
                    update_expression += ", last_execution = :last_exec"
                    attr_values[":last_exec"] = task.get('last_execution')
                
                update_result = self.db.update_item(
                    key=task_key,
                    update_expression=update_expression,
                    expression_attribute_values=attr_values
                )
                
                if update_result['success']:
                    updated_count += 1
                else:
                    failed_count += 1
                    logger.error(f"Failed to update task {task_key}: {update_result.get('error')}")
            
            return {
                "success": True,
                "updated_count": updated_count,
                "failed_count": failed_count
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def batch_update_scores(self, score_updates: list) -> Dict[str, Any]:
        """Batch update scores for multiple users in DynamoDB only"""
        try:
            updated_count = 0
            failed_count = 0
            
            for update in score_updates:
                user_id = update['user_id']
                amount = update.get('amount', 10)
                
                db_key = self._get_dynamodb_key(user_id, config.DOC_TYPE_PROFILE)
                
                update_expression = "ADD score :amount SET updated_at = :updated_at"
                attr_values = {
                    ":amount": amount,
                    ":updated_at": datetime.utcnow().isoformat()
                }
                
                update_result = self.db.update_item(
                    key=db_key,
                    update_expression=update_expression,
                    expression_attribute_values=attr_values
                )
                
                if update_result['success']:
                    updated_count += 1
                else:
                    failed_count += 1
                    logger.error(f"Failed to update score for user {user_id}: {update_result.get('error')}")
            
            return {
                "success": True,
                "updated_count": updated_count,
                "failed_count": failed_count
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def increment_activity_done(self, user_id: str, plan_id: str) -> Dict[str, Any]:
        """Increment the cnt_activity_done for a schedule task by plan_id"""
        try:
            # First, find the task by plan_id
            pk = f"SCHEDULE#{user_id}"
            sk_prefix = "TASK#"
            
            key_condition_expression = "PK = :pk AND begins_with(SK, :sk_prefix)"
            filter_expression = "plan_id = :plan_id"
            expression_attribute_values = {
                ':pk': pk,
                ':sk_prefix': sk_prefix,
                ':plan_id': plan_id
            }
            
            db_result = self.db.query_items(
                key_condition_expression=key_condition_expression,
                filter_expression=filter_expression,
                expression_attribute_values=expression_attribute_values
            )
            
            if not db_result['success'] or not db_result['data']:
                return {"success": False, "error": "Schedule task not found for plan_id"}
            
            # Get the first matching task
            task = db_result['data'][0]
            task_key = {"PK": task['PK'], "SK": task['SK']}
            
            current_count = task.get('cnt_activity_done', 0)
            target = task.get('target', 0)
            new_count = current_count + 1
            
            # Check if we've reached the target to complete a cycle
            if target and new_count >= target:
                # Increment finished_cycle and reset cnt_activity_done
                update_expression = "SET cnt_activity_done = :reset_count, updated_at = :updated_at, last_execution = :last_exec ADD finished_cycle :cycle_inc"
                attr_values = {
                    ":reset_count": 0,
                    ":cycle_inc": 1,
                    ":updated_at": int(datetime.utcnow().timestamp()),
                    ":last_exec": int(datetime.utcnow().timestamp())
                }
            else:
                # Just increment cnt_activity_done
                update_expression = "ADD cnt_activity_done :inc SET updated_at = :updated_at, last_execution = :last_exec"
                attr_values = {
                    ":inc": 1,
                    ":updated_at": int(datetime.utcnow().timestamp()),
                    ":last_exec": int(datetime.utcnow().timestamp())
                }
            
            update_result = self.db.update_item(
                key=task_key,
                update_expression=update_expression,
                expression_attribute_values=attr_values
            )
            
            if not update_result['success']:
                return {"success": False, "error": update_result['error']}
            
            return {"success": True, "plan_id": plan_id, "cycle_completed": target and new_count >= target}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_plan(self, user_id: str, plan_id: str) -> Dict[str, Any]:
        """Delete plan and related schedule tasks"""
        try:
            # Delete the plan first
            plan_result = self.delete_document(user_id, config.DOC_TYPE_PLAN, plan_id)
            if not plan_result['success']:
                return plan_result
            
            # Find and delete related schedule tasks
            pk = f"SCHEDULE#{user_id}"
            sk_prefix = "TASK#"
            
            key_condition_expression = "PK = :pk AND begins_with(SK, :sk_prefix)"
            filter_expression = "plan_id = :plan_id"
            expression_attribute_values = {
                ':pk': pk,
                ':sk_prefix': sk_prefix,
                ':plan_id': plan_id
            }
            
            db_result = self.db.query_items(
                key_condition_expression=key_condition_expression,
                filter_expression=filter_expression,
                expression_attribute_values=expression_attribute_values
            )
            
            # Delete schedule tasks if they exist
            if db_result['success'] and db_result['data']:
                for task in db_result['data']:
                    task_key = {"PK": task['PK'], "SK": task['SK']}
                    delete_result = self.db.delete_item(task_key)
                    if not delete_result['success']:
                        logger.warning(f"Failed to delete schedule task: {delete_result.get('error')}")
            
            return {"success": True, "plan_id": plan_id}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_plan(self, user_id: str, plan_id: str, updated_plan_data: dict) -> Dict[str, Any]:
        """Update plan in S3 and return plan data like save_plan"""
        try:
            # Get existing plan
            plan_result = self.get_plan(user_id, plan_id)
            if not plan_result['success']:
                return plan_result
            
            # Merge existing data with updates
            plan_data = plan_result['data']
            plan_data.update(updated_plan_data)
            plan_data['updated_at'] = datetime.utcnow().isoformat()
            
            # Save updated plan to S3
            s3_path = self._get_s3_path(user_id, config.DOC_TYPE_PLAN, plan_id)
            s3_result = self.s3_plan.upload_json(s3_path, plan_data)
            if not s3_result['success']:
                return s3_result
            
            # Update DynamoDB metadata if needed
            db_key = self._get_dynamodb_key(user_id, config.DOC_TYPE_PLAN, plan_id)
            update_expression = "SET updated_at = :updated_at"
            attr_values = {":updated_at": datetime.utcnow().isoformat()}
            
            # Update action_name if action changed
            if 'action' in updated_plan_data:
                update_expression += ", action_name = :action_name"
                attr_values[":action_name"] = updated_plan_data.get('action', {}).get('name', 'Unknown')
            
            db_result = self.db.update_item(
                key=db_key,
                update_expression=update_expression,
                expression_attribute_values=attr_values
            )
            
            if not db_result['success']:
                return {"success": False, "error": db_result['error']}
            
            return {
                'success': True,
                'plan_id': plan_id,
                'plan_data': plan_data
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    

    
    def _update_schedule_task_from_plan(self, user_id: str, plan_id: str, time_data: dict) -> None:
        """Update schedule task when plan time data changes"""
        try:
            # Find the schedule task
            pk = f"SCHEDULE#{user_id}"
            sk_prefix = "TASK#"
            
            key_condition_expression = "PK = :pk AND begins_with(SK, :sk_prefix)"
            filter_expression = "plan_id = :plan_id"
            expression_attribute_values = {
                ':pk': pk,
                ':sk_prefix': sk_prefix,
                ':plan_id': plan_id
            }
            
            db_result = self.db.query_items(
                key_condition_expression=key_condition_expression,
                filter_expression=filter_expression,
                expression_attribute_values=expression_attribute_values
            )
            
            if not db_result['success'] or not db_result['data']:
                logger.warning(f"No schedule task found for plan_id: {plan_id}")
                return
            
            task = db_result['data'][0]
            task_key = {"PK": task['PK'], "SK": task['SK']}
            
            # Extract new schedule and target values
            schedule_time = time_data.get('schedule', 'daily')
            new_target = time_data.get('frequency', {}).get('value', 1)
            
            # Calculate new next_execution
            now = datetime.utcnow()
            if schedule_time == 'daily':
                next_exec = now + timedelta(days=1)
            elif schedule_time == 'weekly':
                next_exec = now + timedelta(weeks=1)
            elif schedule_time == 'monthly':
                next_exec = now + timedelta(days=30)
            else:
                next_exec = now + timedelta(days=1)
            
            # Update the schedule task
            update_expression = "SET schedule_time = :schedule, target = :target, next_execution = :next_exec, updated_at = :updated_at"
            attr_values = {
                ":schedule": schedule_time,
                ":target": new_target,
                ":next_exec": int(next_exec.timestamp()),
                ":updated_at": int(now.timestamp())
            }
            
            update_result = self.db.update_item(
                key=task_key,
                update_expression=update_expression,
                expression_attribute_values=attr_values
            )
            
            if update_result['success']:
                logger.info(f"Updated schedule task for plan_id: {plan_id}")
            else:
                logger.error(f"Failed to update schedule task: {update_result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error updating schedule task: {str(e)}")

    def update_plan_status(self, user_id: str, plan_id: str, status: str) -> Dict[str, Any]:
        """Update plan status in DynamoDB"""
        try:
            valid_statuses = [e.value for e in PlanStatusEnum]
            if status not in valid_statuses:
                return {"success": False, "error": f"Invalid status: {status}"}
            
            db_key = self._get_dynamodb_key(user_id, config.DOC_TYPE_PLAN, plan_id)
            
            update_expression = "SET #status = :status, updated_at = :updated_at"
            attr_values = {
                ":status": status,
                ":updated_at": datetime.utcnow().isoformat()
            }
            attr_names = {"#status": "status"}
            
            db_result = self.db.update_item(
                key=db_key,
                update_expression=update_expression,
                expression_attribute_values=attr_values,
                expression_attribute_names=attr_names
            )
            
            if db_result['success']:
                # Update related schedule task status
                if status == 'active':
                    self.update_schedule_task_status(user_id, plan_id, 'ACTIVE')
                else:
                    self.update_schedule_task_status(user_id, plan_id, 'INACTIVE')
                
                return {"success": True, "plan_id": plan_id, "status": status}
            else:
                return db_result
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def save_plan(self, user_id: str, plan_id: str, action_type: str, plan, status : str) -> Dict[str, Any]:
        """Save plan to both S3 and DynamoDB"""
        try:
            # Validate status
            valid_statuses = [e.value for e in PlanStatusEnum]
            if status not in valid_statuses:
                raise ValueError(f"Invalid status: {status}")

            s3_path = self._get_s3_path(user_id, config.DOC_TYPE_PLAN, plan_id)
            db_key = self._get_dynamodb_key(user_id, config.DOC_TYPE_PLAN, plan_id)
            
            plan_data = plan.dict() if hasattr(plan, 'dict') else plan
            created_timestamp = datetime.utcnow().isoformat()
            plan_data['created_at'] = created_timestamp
            
            s3_result = self.s3_plan.upload_json(s3_path, plan_data)
            if not s3_result['success']:
                return s3_result
            
            
            db_item = {
                **db_key,
                "plan_id": plan_id,
                "action_type": action_type,
                "action_name": plan_data.get('action', {}).get('name', 'Unknown'),
                "s3_path": s3_path,
                "status": status,
                "created_at": created_timestamp
            }
            
            db_result = self.db.create_item(db_item)
            if not db_result['success']:
                self.s3_plan.delete_object(s3_path)
                return {
                    'success' : False,
                    'error': db_result['error']
                }
            
            # Create schedule task for monitoring with matching status
            task_result = self.create_schedule_task(user_id, plan_id, action_type, plan_data, status)
            if not task_result['success']:
                logger.warning(f"Failed to create schedule task: {task_result.get('error')}")
            
            return {
                'success': True,
                'plan_id': plan_id,
                'task_id': task_result.get('task_id') if task_result['success'] else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
                         
    def log_failure(self, user_id: str, doc_type: str, doc_id: str, error_message: str) -> None:
        """Log failures to DynamoDB for auditing"""
        try:
            db_key = self._get_dynamodb_key(user_id, doc_type, doc_id)
            log_item = {
                **db_key,
                "error_message": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.db.create_item(log_item)
        except Exception as e:
            logger.error(f"Failed to log failure: {str(e)}")
    
    def save_user_preferences(self, user_id: str, preferences: UserPreferences, preference_id: str = "default") -> Dict[str, Any]:
        """Save user preferences directly to DynamoDB"""
        try:
            db_key = self._get_dynamodb_key(user_id, config.DOC_TYPE_PREFERENCES, preference_id)
            
            preferences_data = preferences.dict() if hasattr(preferences, 'dict') else preferences
            
            db_item = {
                **db_key,
                "preference_id": preference_id,
                "physical_activities_like": preferences_data.get('physical_activities_like', []),
                "physical_activities_dislike": preferences_data.get('physical_activities_dislike', []),
                "mental_activities_like": preferences_data.get('mental_activities_like', []),
                "mental_activities_dislike": preferences_data.get('mental_activities_dislike', []),
                "diet_activities_like": preferences_data.get('diet_activities_like', []),
                "diet_activities_dislike": preferences_data.get('diet_activities_dislike', []),
                "medical_activities_like": preferences_data.get('medical_activities_like', []),
                "medical_activities_dislike": preferences_data.get('medical_activities_dislike', []),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            db_result = self.db.create_item(db_item)
            if not db_result['success']:
                return {"success": False, "error": db_result['error']}
            
            return {"success": True, "preference_id": preference_id}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_user_preferences(self, user_id: str, preference_id: str = "default") -> Dict[str, Any]:
        """Get user preferences from DynamoDB"""
        try:
            db_key = self._get_dynamodb_key(user_id, config.DOC_TYPE_PREFERENCES, preference_id)
            db_result = self.db.get_item(db_key)
            
            if not db_result['success']:
                return db_result
            
            return {"success": True, "data": db_result['data']}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def extract_and_save_preferences_async(self, user_id: str, text: str) -> Dict[str, Any]:
        """Call dedicated Lambda function for background processing"""
        try:
            import boto3
            import json
            
            lambda_client = boto3.client('lambda')
            
            payload = {
                'user_id': user_id,
                'text': text[:5000],  # Limit text size
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Invoking process-preferences Lambda for user {user_id}")
            response = lambda_client.invoke(
                FunctionName='process-preferences',
                InvocationType='Event',  # Async invocation
                Payload=json.dumps(payload)
            )
            logger.info(f"Successfully invoked process-preferences Lambda for user {user_id}")
            
            return {"success": True, "status": "processing"}
            
        except Exception as e:
            logger.error(f"Failed to invoke process-preferences Lambda for user {user_id}: {str(e)}")
            # Fallback to sync processing
            return self.extract_and_save_preferences_sync(user_id, text)
    
    def extract_and_save_preferences_sync(self, user_id: str, text: str) -> Dict[str, Any]:
        """Extract preferences from text using AWS Comprehend and save them"""
        logger.info(f"extract_and_save_preferences_sync ENTRY for user {user_id}")
        try:
            import boto3
            comprehend = boto3.client('comprehend')
            
            # Get existing preferences or create new
            existing_prefs = self.get_user_preferences(user_id)
            if existing_prefs['success']:
                preferences_data = existing_prefs['data']
            else:
                preferences_data = {
                    "physical_activities_like": [],
                    "physical_activities_dislike": [],
                    "mental_activities_like": [],
                    "mental_activities_dislike": [],
                    "diet_activities_like": [],
                    "diet_activities_dislike": [],
                    "medical_activities_like": [],
                    "medical_activities_dislike": []
                }
            
            # Extract using Comprehend
            logger.info(f"Starting AWS Comprehend analysis for user {user_id}")
            logger.info(f"Text length: {len(text)}, truncated to: {len(text[:5000])}")
            logger.info(f"Text content being sent to Comprehend: '{text[:5000]}'")
            
            logger.info("Calling detect_sentiment...")
            sentiment = comprehend.detect_sentiment(Text=text[:5000], LanguageCode='en')
            logger.info("Sentiment detection completed")
            
            logger.info("Calling detect_entities...")
            entities = comprehend.detect_entities(Text=text[:5000], LanguageCode='en')
            logger.info("Entity detection completed")
            
            logger.info("Calling detect_key_phrases...")
            key_phrases = comprehend.detect_key_phrases(Text=text[:5000], LanguageCode='en')
            logger.info("Key phrase detection completed")
            
            logger.info(f"AWS Comprehend results - Sentiment: {sentiment['Sentiment']}, Entities: {len(entities['Entities'])}, Key phrases: {len(key_phrases['KeyPhrases'])}")
            logger.info(f"Entities found: {[e['Text'] for e in entities['Entities']]}")
            logger.info(f"Key phrases found: {[p['Text'] for p in key_phrases['KeyPhrases']]}")
            
            # Use AI to classify activities instead of keyword matching
            from gemini_simple import GeminiSimple
            
            # Collect all entities and phrases
            activities = []
            for entity in entities['Entities']:
                activities.append(entity['Text'])
            for phrase in key_phrases['KeyPhrases']:
                activities.append(phrase['Text'])
            
            if activities:
                # Use AI to classify activities
                gemini = GeminiSimple()
                classification_prompt = f"""
You are analyzing user preferences for health activities. Focus ONLY on health-related activities.

User text: "{text[:1000]}"
Sentiment: {sentiment['Sentiment']}
Found entities/phrases: {activities}

For each item, classify ONLY if it's a health/wellness activity:
- physical: walking, running, swimming, gym, exercise, yoga, sports, dancing, etc.
- mental: meditation, reading, puzzles, relaxation, mindfulness, etc. 
- diet: eating, cooking, nutrition, healthy foods, meal prep, etc.
- medical: doctor visits, medication, therapy, checkups, etc.

SKIP non-health items like locations, objects, or irrelevant phrases.

Return JSON:
{{
  "classifications": [
    {{"activity": "walking", "category": "physical", "sentiment": "like"}}
  ]
}}
"""
                
                logger.info(f"Sending classification prompt to Gemini for {len(activities)} activities")
                ai_result = gemini.generate_text(classification_prompt, parse_json=True)
                logger.info(f"Gemini AI result: {ai_result}")
                
                if ai_result.get('success') and ai_result.get('data', {}).get('parsed_json'):
                    classifications = ai_result['data']['parsed_json'].get('classifications', [])
                    logger.info(f"Gemini classified {len(classifications)} activities")
                    
                    for item in classifications:
                        activity = item.get('activity', '').lower()
                        category = item.get('category', 'other')
                        sentiment_type = item.get('sentiment', 'like')
                        
                        logger.info(f"Processing classification: {item}")
                        logger.info(f"Extracted - activity: '{activity}', category: '{category}', sentiment: '{sentiment_type}'")
                        
                        if category in ['physical', 'mental', 'diet', 'medical']:
                            key = f"{category}_activities_{sentiment_type}"
                            logger.info(f"Target key: {key}")
                            logger.info(f"Current {key}: {preferences_data.get(key, 'KEY_NOT_FOUND')}")
                            logger.info(f"Activity '{activity}' already in list: {activity in preferences_data.get(key, [])}")
                            
                            if key in preferences_data and activity not in preferences_data[key]:
                                preferences_data[key].append(activity)
                                logger.info(f"✅ ADDED '{activity}' to {key}")
                                logger.info(f"Updated {key}: {preferences_data[key]}")
                            else:
                                logger.warning(f"❌ NOT ADDED '{activity}' - key exists: {key in preferences_data}, duplicate: {activity in preferences_data.get(key, [])}")
                        else:
                            logger.warning(f"❌ SKIPPED '{activity}' - invalid category: '{category}'")
                else:
                    logger.warning("Gemini classification failed, using keyword fallback")
                    # Fallback to basic keyword matching
                    self._extract_with_keywords(entities, key_phrases, sentiment, preferences_data)
            
            # Save updated preferences
            logger.info(f"Final preferences data: {preferences_data}")
            preferences = UserPreferences(**preferences_data)
            save_result = self.save_user_preferences(user_id, preferences)
            logger.info(f"Save preferences result: {save_result}")
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def extract_and_save_preferences(self, user_id: str, text: str, async_mode: bool = False) -> Dict[str, Any]:
        """Extract preferences with async option - defaulting to sync due to Lambda container freezing"""
        if async_mode:
            return self.extract_and_save_preferences_async(user_id, text)
        else:
            return self.extract_and_save_preferences_sync(user_id, text)
    
    def _extract_with_keywords(self, entities, key_phrases, sentiment, preferences_data):
        """Fallback keyword-based extraction"""
        activity_keywords = {
            'physical': ['walk', 'run', 'swim', 'gym', 'exercise', 'yoga', 'dance', 'bike', 'sport', 'fitness', 'workout', 'training', 'cardio', 'strength', 'pilates', 'aerobic', 'jogging', 'hiking', 'climbing', 'tennis', 'basketball', 'football', 'soccer', 'volleyball', 'badminton', 'golf', 'skiing', 'surfing', 'cycling', 'rowing', 'boxing', 'martial arts', 'crossfit', 'zumba', 'spinning'],
            'mental': ['read', 'meditate', 'puzzle', 'music', 'art', 'learn', 'study', 'mindfulness', 'relaxation', 'breathing', 'visualization', 'journaling', 'therapy', 'counseling', 'chess', 'sudoku', 'crossword', 'brain games', 'memory exercises', 'concentration', 'focus', 'stress relief', 'anxiety management'],
            'diet': ['eat', 'food', 'meal', 'cook', 'nutrition', 'diet', 'vegetable', 'fruit', 'protein', 'carbs', 'vitamins', 'minerals', 'healthy eating', 'meal prep', 'organic', 'whole foods', 'plant-based', 'keto', 'mediterranean', 'low-carb', 'high-protein', 'fiber', 'antioxidants', 'superfoods'],
            'medical': ['doctor', 'medicine', 'therapy', 'treatment', 'checkup', 'medication', 'prescription', 'diagnosis', 'symptoms', 'health screening', 'blood test', 'physical exam', 'specialist', 'clinic', 'hospital', 'surgery', 'rehabilitation', 'physiotherapy', 'occupational therapy']
        }
        
        sentiment_score = sentiment['Sentiment']
        is_positive = sentiment_score in ['POSITIVE', 'NEUTRAL']
        
        for entity in entities['Entities']:
            entity_text = entity['Text'].lower()
            for category, keywords in activity_keywords.items():
                if any(keyword in entity_text for keyword in keywords):
                    key = f"{category}_activities_{'like' if is_positive else 'dislike'}"
                    if entity_text not in preferences_data[key]:
                        preferences_data[key].append(entity_text)
        
        for phrase in key_phrases['KeyPhrases']:
            phrase_text = phrase['Text'].lower()
            for category, keywords in activity_keywords.items():
                if any(keyword in phrase_text for keyword in keywords):
                    key = f"{category}_activities_{'like' if is_positive else 'dislike'}"
                    if phrase_text not in preferences_data[key]:
                        preferences_data[key].append(phrase_text)