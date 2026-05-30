"""
DynamoDB Helper Library for AWS Lambda Layer
============================================

This module provides basic CRUD operations for DynamoDB tables.
Designed to be used as a Lambda layer and imported by other Lambda functions.

Usage in Lambda functions:
    from dynamodb_helper import DynamoDBHelper
    
    db = DynamoDBHelper('your-table-name')
    result = db.create_item({'id': '123', 'name': 'John'})
"""

import boto3
import json
import logging
from botocore.exceptions import ClientError
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DecimalEncoder(json.JSONEncoder):
    """Helper class to handle Decimal types in JSON serialization"""
    def default(self, o):
        if isinstance(o, Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


class DynamoDBHelper:
    """
    A helper class for DynamoDB operations in AWS Lambda functions.
    
    This class provides methods for basic CRUD operations on DynamoDB tables.
    """
    
    def __init__(self, table_name: str, region_name: str = None):
        """
        Initialize the DynamoDB helper.
        
        Args:
            table_name (str): Name of the DynamoDB table
            region_name (str, optional): AWS region name. If not provided, uses default region.
        """
        self.table_name = table_name
        
        # Initialize DynamoDB resource
        if region_name:
            self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        else:
            self.dynamodb = boto3.resource('dynamodb')
            
        self.table = self.dynamodb.Table(table_name)
        
        logger.info(f"DynamoDBHelper initialized for table: {table_name}")

    def create_item(self, item: Dict[str, Any], condition_expression: str = None) -> Dict[str, Any]:
        """
        Create a new item in the DynamoDB table.
        
        Args:
            item (Dict): The item to create
            condition_expression (str, optional): Condition that must be satisfied for the operation to succeed
            
        Returns:
            Dict: Response from DynamoDB operation
            
        Raises:
            ClientError: If the operation fails
        """
        try:
            # Convert float values to Decimal for DynamoDB compatibility
            item = self._convert_floats_to_decimal(item)
            logger.debug(f"Creating item in table {self.table_name}: {item}")
            
            if condition_expression:
                logger.debug(f"Using condition expression: {condition_expression}")
                response = self.table.put_item(
                    Item=item,
                    ConditionExpression=condition_expression
                )
            else:
                response = self.table.put_item(Item=item)
                
                # Add created_at timestamp before saving the item
                item['created_at'] = datetime.now().isoformat()

            logger.info(f"Item created successfully in table {self.table_name}")
            return {
                'statusCode': 200,
                'success': True,
                'message': 'Item created successfully',
                'data': item
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to create item: {error_code} - {error_message}")
            
            return {
                'statusCode': 400 if error_code == 'ConditionalCheckFailedException' else 500,
                'success': False,
                'error': error_code,
                'message': error_message
            }

    def get_item(self, key: Dict[str, Any], attributes_to_get: List[str] = None) -> Dict[str, Any]:
        """
        Get an item from the DynamoDB table.
        
        Args:
            key (Dict): The primary key of the item to retrieve
            attributes_to_get (List[str], optional): List of attribute names to retrieve
            
        Returns:
            Dict: The retrieved item or error information
        """
        try:
            # Convert float values to Decimal for DynamoDB compatibility
            key = self._convert_floats_to_decimal(key)
            logger.debug(f"Getting item from table {self.table_name} with key: {key}")
            
            if attributes_to_get:
                logger.debug(f"Projection expression: {','.join(attributes_to_get)}")
                response = self.table.get_item(
                    Key=key,
                    ProjectionExpression=','.join(attributes_to_get)
                )
            else:
                response = self.table.get_item(Key=key)
            
            if 'Item' in response:
                item = self._convert_decimal_to_native(response['Item'])
                logger.info(f"Item retrieved successfully from table {self.table_name}")
                return {
                    'statusCode': 200,
                    'success': True,
                    'data': item
                }
            else:
                logger.info(f"Item not found in table {self.table_name}")
                return {
                    'statusCode': 404,
                    'success': False,
                    'message': 'Item not found'
                }
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to get item: {error_code} - {error_message}")
            
            return {
                'statusCode': 500,
                'success': False,
                'error': error_code,
                'message': error_message
            }

    def update_item(self, key: Dict[str, Any], update_expression: str, 
                   expression_attribute_values: Dict[str, Any] = None,
                   expression_attribute_names: Dict[str, str] = None,
                   condition_expression: str = None) -> Dict[str, Any]:
        """
        Update an item in the DynamoDB table.
        
        Args:
            key (Dict): The primary key of the item to update
            update_expression (str): Expression defining the updates to perform
            expression_attribute_values (Dict, optional): Values used in the update expression
            expression_attribute_names (Dict, optional): Name placeholders used in the update expression
            condition_expression (str, optional): Condition that must be satisfied for the operation to succeed
            
        Returns:
            Dict: Response from DynamoDB operation
        """
        try:
            # Convert float values to Decimal for DynamoDB compatibility
            key = self._convert_floats_to_decimal(key)
            logger.debug(f"Updating item in table {self.table_name} with key: {key}")
            logger.debug(f"Update expression: {update_expression}")
            
            if expression_attribute_values:
                expression_attribute_values = self._convert_floats_to_decimal(expression_attribute_values)
                logger.debug(f"Expression attribute values: {expression_attribute_values}")
            
            # Build the update parameters
            update_params = {
                'Key': key,
                'UpdateExpression': update_expression,
                'ReturnValues': 'ALL_NEW'
            }
            
            if expression_attribute_values:
                update_params['ExpressionAttributeValues'] = expression_attribute_values
                
            if expression_attribute_names:
                update_params['ExpressionAttributeNames'] = expression_attribute_names
                
            if condition_expression:
                update_params['ConditionExpression'] = condition_expression
            
            # add updated_at in item before update
            updated_item['updated_at'] = datetime.now().isoformat()

            response = self.table.update_item(**update_params)
            
            updated_item = self._convert_decimal_to_native(response['Attributes'])
            logger.info(f"Item updated successfully in table {self.table_name}")
            


            return {
                'statusCode': 200,
                'success': True,
                'message': 'Item updated successfully',
                'data': updated_item
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to update item: {error_code} - {error_message}")
            
            return {
                'statusCode': 400 if error_code == 'ConditionalCheckFailedException' else 500,
                'success': False,
                'error': error_code,
                'message': error_message
            }

    def delete_item(self, key: Dict[str, Any], condition_expression: str = None) -> Dict[str, Any]:
        """
        Delete an item from the DynamoDB table.
        
        Args:
            key (Dict): The primary key of the item to delete
            condition_expression (str, optional): Condition that must be satisfied for the operation to succeed
            
        Returns:
            Dict: Response from DynamoDB operation
        """
        try:
            # Convert float values to Decimal for DynamoDB compatibility
            key = self._convert_floats_to_decimal(key)
            
            if condition_expression:
                response = self.table.delete_item(
                    Key=key,
                    ConditionExpression=condition_expression,
                    ReturnValues='ALL_OLD'
                )
            else:
                response = self.table.delete_item(
                    Key=key,
                    ReturnValues='ALL_OLD'
                )
            
            deleted_item = None
            if 'Attributes' in response:
                deleted_item = self._convert_decimal_to_native(response['Attributes'])
            
            logger.info(f"Item deleted successfully from table {self.table_name}")
            
            return {
                'statusCode': 200,
                'success': True,
                'message': 'Item deleted successfully',
                'data': deleted_item
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to delete item: {error_code} - {error_message}")
            
            return {
                'statusCode': 400 if error_code == 'ConditionalCheckFailedException' else 500,
                'success': False,
                'error': error_code,
                'message': error_message
            }

    def query_items(self, key_condition_expression: str, 
                   expression_attribute_values: Dict[str, Any] = None,
                   expression_attribute_names: Dict[str, str] = None,
                   filter_expression: str = None,
                   index_name: str = None,
                   limit: int = None,
                   scan_index_forward: bool = True) -> Dict[str, Any]:
        """
        Query items from the DynamoDB table.
        
        Args:
            key_condition_expression (str): Key condition for the query
            expression_attribute_values (Dict, optional): Values used in the expressions
            expression_attribute_names (Dict, optional): Name placeholders used in the expressions
            filter_expression (str, optional): Filter expression to apply after the query
            index_name (str, optional): Name of the Global Secondary Index to query
            limit (int, optional): Maximum number of items to return
            scan_index_forward (bool): Whether to scan in ascending order
            
        Returns:
            Dict: Query results
        """
        try:
            # Convert float values to Decimal for DynamoDB compatibility
            if expression_attribute_values:
                expression_attribute_values = self._convert_floats_to_decimal(expression_attribute_values)
            
            # Build query parameters
            query_params = {
                'KeyConditionExpression': key_condition_expression,
                'ScanIndexForward': scan_index_forward
            }
            
            if expression_attribute_values:
                query_params['ExpressionAttributeValues'] = expression_attribute_values
                
            if expression_attribute_names:
                query_params['ExpressionAttributeNames'] = expression_attribute_names
                
            if filter_expression:
                query_params['FilterExpression'] = filter_expression
                
            if index_name:
                query_params['IndexName'] = index_name
                
            if limit:
                query_params['Limit'] = limit
            
            response = self.table.query(**query_params)
            
            items = [self._convert_decimal_to_native(item) for item in response.get('Items', [])]
            
            logger.info(f"Query executed successfully on table {self.table_name}. Found {len(items)} items")
            
            return {
                'statusCode': 200,
                'success': True,
                'data': items,
                'count': response.get('Count', 0),
                'scanned_count': response.get('ScannedCount', 0),
                'last_evaluated_key': response.get('LastEvaluatedKey')
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to query items: {error_code} - {error_message}")
            
            return {
                'statusCode': 500,
                'success': False,
                'error': error_code,
                'message': error_message
            }

    def scan_items(self, filter_expression: str = None,
                  expression_attribute_values: Dict[str, Any] = None,
                  expression_attribute_names: Dict[str, str] = None,
                  limit: int = None,
                  index_name: str = None) -> Dict[str, Any]:
        """
        Scan items from the DynamoDB table.
        
        Args:
            filter_expression (str, optional): Filter expression to apply
            expression_attribute_values (Dict, optional): Values used in the expressions
            expression_attribute_names (Dict, optional): Name placeholders used in the expressions
            limit (int, optional): Maximum number of items to return
            index_name (str, optional): Name of the Global Secondary Index to scan
            
        Returns:
            Dict: Scan results
        """
        try:
            # Convert float values to Decimal for DynamoDB compatibility
            if expression_attribute_values:
                expression_attribute_values = self._convert_floats_to_decimal(expression_attribute_values)
            
            # Build scan parameters
            scan_params = {}
            
            if filter_expression:
                scan_params['FilterExpression'] = filter_expression
                
            if expression_attribute_values:
                scan_params['ExpressionAttributeValues'] = expression_attribute_values
                
            if expression_attribute_names:
                scan_params['ExpressionAttributeNames'] = expression_attribute_names
                
            if limit:
                scan_params['Limit'] = limit
                
            if index_name:
                scan_params['IndexName'] = index_name
            
            response = self.table.scan(**scan_params)
            
            items = [self._convert_decimal_to_native(item) for item in response.get('Items', [])]
            
            logger.info(f"Scan executed successfully on table {self.table_name}. Found {len(items)} items")
            
            return {
                'statusCode': 200,
                'success': True,
                'data': items,
                'count': response.get('Count', 0),
                'scanned_count': response.get('ScannedCount', 0),
                'last_evaluated_key': response.get('LastEvaluatedKey')
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to scan items: {error_code} - {error_message}")
            
            return {
                'statusCode': 500,
                'success': False,
                'error': error_code,
                'message': error_message
            }

    def batch_write_items(self, items_to_put: List[Dict[str, Any]] = None, 
                         items_to_delete: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform batch write operations (put/delete) on the DynamoDB table.
        
        Args:
            items_to_put (List[Dict], optional): List of items to put
            items_to_delete (List[Dict], optional): List of keys for items to delete
            
        Returns:
            Dict: Response from batch write operation
        """
        try:
            request_items = {self.table_name: []}
            
            if items_to_put:
                for item in items_to_put:
                    item = self._convert_floats_to_decimal(item)
                    request_items[self.table_name].append({'PutRequest': {'Item': item}})
            
            if items_to_delete:
                for key in items_to_delete:
                    key = self._convert_floats_to_decimal(key)
                    request_items[self.table_name].append({'DeleteRequest': {'Key': key}})
            
            response = self.dynamodb.batch_write_item(RequestItems=request_items)
            
            unprocessed_items = response.get('UnprocessedItems', {})
            
            logger.info(f"Batch write completed for table {self.table_name}")
            
            return {
                'statusCode': 200,
                'success': True,
                'message': 'Batch write completed',
                'unprocessed_items': unprocessed_items
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to batch write items: {error_code} - {error_message}")
            
            return {
                'statusCode': 500,
                'success': False,
                'error': error_code,
                'message': error_message
            }

    def batch_get_items(self, keys: List[Dict[str, Any]], 
                       attributes_to_get: List[str] = None) -> Dict[str, Any]:
        """
        Get multiple items from the DynamoDB table in a single request.
        
        Args:
            keys (List[Dict]): List of primary keys for items to retrieve
            attributes_to_get (List[str], optional): List of attribute names to retrieve
            
        Returns:
            Dict: The retrieved items
        """
        try:
            # Convert float values to Decimal for DynamoDB compatibility
            keys = [self._convert_floats_to_decimal(key) for key in keys]
            
            request_items = {
                self.table_name: {
                    'Keys': keys
                }
            }
            
            if attributes_to_get:
                request_items[self.table_name]['ProjectionExpression'] = ','.join(attributes_to_get)
            
            response = self.dynamodb.batch_get_item(RequestItems=request_items)
            
            items = response.get('Responses', {}).get(self.table_name, [])
            items = [self._convert_decimal_to_native(item) for item in items]
            
            unprocessed_keys = response.get('UnprocessedKeys', {})
            
            logger.info(f"Batch get completed for table {self.table_name}. Retrieved {len(items)} items")
            
            return {
                'statusCode': 200,
                'success': True,
                'data': items,
                'count': len(items),
                'unprocessed_keys': unprocessed_keys
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to batch get items: {error_code} - {error_message}")
            
            return {
                'statusCode': 500,
                'success': False,
                'error': error_code,
                'message': error_message
            }

    def table_exists(self) -> bool:
        """
        Check if the DynamoDB table exists.
        
        Returns:
            bool: True if table exists, False otherwise
        """
        try:
            self.table.table_status
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return False
            raise

    def get_table_info(self) -> Dict[str, Any]:
        """
        Get information about the DynamoDB table.
        
        Returns:
            Dict: Table information including status, item count, etc.
        """
        try:
            table_description = self.table.Table().table_status
            
            return {
                'statusCode': 200,
                'success': True,
                'data': {
                    'table_name': self.table_name,
                    'table_status': self.table.table_status,
                    'item_count': self.table.item_count,
                    'table_size_bytes': self.table.table_size_bytes,
                    'creation_date_time': str(self.table.creation_date_time)
                }
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to get table info: {error_code} - {error_message}")
            
            return {
                'statusCode': 500,
                'success': False,
                'error': error_code,
                'message': error_message
            }

    def _convert_floats_to_decimal(self, obj: Any) -> Any:
        """
        Convert float values to Decimal for DynamoDB compatibility.
        
        Args:
            obj: Object to convert
            
        Returns:
            Object with floats converted to Decimal
        """
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(item) for item in obj]
        else:
            return obj

    def _convert_decimal_to_native(self, obj: Any) -> Any:
        """
        Convert Decimal values back to native Python types.
        
        Args:
            obj: Object to convert
            
        Returns:
            Object with Decimals converted to int/float
        """
        if isinstance(obj, Decimal):
            if obj % 1 > 0:
                return float(obj)
            else:
                return int(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_decimal_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimal_to_native(item) for item in obj]
        else:
            return obj


# Convenience functions for quick operations
def create_db_helper(table_name: str, region_name: str = None) -> DynamoDBHelper:
    """
    Create a DynamoDBHelper instance.
    
    Args:
        table_name (str): Name of the DynamoDB table
        region_name (str, optional): AWS region name
        
    Returns:
        DynamoDBHelper: Initialized DynamoDB helper instance
    """
    return DynamoDBHelper(table_name, region_name)


def lambda_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format a standard Lambda response.
    
    Args:
        status_code (int): HTTP status code
        body (Dict): Response body
        
    Returns:
        Dict: Formatted Lambda response
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }


# Example usage in a Lambda function:
"""
import json
from dynamodb_helper import DynamoDBHelper, lambda_response

def lambda_handler(event, context):
    # Initialize DynamoDB helper
    db = DynamoDBHelper('my-table-name')
    
    # Example: Create an item
    new_item = {
        'id': 'user123',
        'name': 'John Doe',
        'email': 'john@example.com',
        'age': 30
    }
    
    result = db.create_item(new_item)
    
    if result['success']:
        return lambda_response(200, {
            'message': 'User created successfully',
            'user': result['data']
        })
    else:
        return lambda_response(result['statusCode'], {
            'error': result['message']
        })
"""