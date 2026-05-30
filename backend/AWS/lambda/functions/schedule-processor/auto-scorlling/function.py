import json
from datetime import datetime, timedelta
from document_manager import DocumentManager

def lambda_handler(event, context):
    """Process all overdue scheduled tasks"""
    try:
        doc_manager = DocumentManager()
        
        # Get all overdue tasks
        result = doc_manager.get_overdue_schedule_tasks()
        if not result['success']:
            return {"statusCode": 500, "body": result['error']}
        
        tasks = result['data']
        if not tasks:
            return {"statusCode": 200, "body": "No overdue tasks found"}
        
        # Separate achieved and not achieved tasks
        score_updates = []
        
        # Process each task
        for task in tasks:
            # Check if user achieved target
            if task.get('cnt_activity_done', 0) >= task.get('target', 1):
                score_updates.append({
                    'user_id': task['user_id'],
                    'score_type': 'activity_score',
                    'amount': 10  # Award 10 points for achieving target
                })
            
            # Reset activity count for new cycle
            task['cnt_activity_done'] = 0
            task['last_execution'] = task.get('next_execution')
            
            # Calculate next execution time
            schedule_time = task.get('schedule_time', 'daily')
            if schedule_time.lower() == 'daily':
                frequency_days = 1
            elif schedule_time.lower() == 'weekly':
                frequency_days = 7
            elif schedule_time.lower() == 'monthly':
                frequency_days = 30
            else:
                frequency_days = 1
            
            next_exec = datetime.utcnow() + timedelta(days=frequency_days)
            task['next_execution'] = int(next_exec.timestamp())
        
        # Batch update all tasks
        update_result = doc_manager.batch_update_schedule_tasks(tasks)
        
        # Batch update scores for achieved targets
        score_result = {"updated_count": 0, "failed_count": 0}
        if score_updates:
            score_result = doc_manager.batch_update_scores(score_updates)
        
        if update_result['success']:
            return {
                "statusCode": 200,
                "body": f"Processed {len(tasks)} tasks. Updated: {update_result['updated_count']}, Failed: {update_result['failed_count']}. Scores updated: {score_result['updated_count']}"
            }
        else:
            return {"statusCode": 500, "body": update_result['error']}
            
    except Exception as e:
        print(f"Error processing scheduled tasks: {str(e)}")
        return {"statusCode": 500, "body": str(e)}