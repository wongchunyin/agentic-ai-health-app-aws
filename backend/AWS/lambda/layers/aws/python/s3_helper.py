"""
S3 Helper Library for AWS Lambda Layer
======================================

This module provides basic S3 operations for AWS Lambda functions.
Designed to be used as a Lambda layer and imported by other Lambda functions.

Usage in Lambda functions:
    from s3_helper import S3Helper
    
    s3 = S3Helper('your-bucket-name')
    result = s3.upload_object('file.txt', 'Hello World')
"""

import boto3
import json
import logging
import base64
import mimetypes
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from urllib.parse import unquote_plus

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class S3Helper:
    """
    A helper class for S3 operations in AWS Lambda functions.
    
    This class provides methods for basic S3 operations including upload, download,
    delete, list, and various utility functions.
    """
    
    def __init__(self, bucket_name: str, region_name: str = None, profile_name: str = None):
        """
        Initialize the S3 helper.
        
        Args:
            bucket_name (str): Name of the S3 bucket
            region_name (str, optional): AWS region name. If not provided, uses default region.
            profile_name (str, optional): AWS profile name. If not provided, uses default profile.
        """
        self.bucket_name = bucket_name
        
        # Initialize boto3 session with profile if provided
        if profile_name:
            session = boto3.Session(profile_name=profile_name)
            if region_name:
                self.s3_client = session.client('s3', region_name=region_name)
                self.s3_resource = session.resource('s3', region_name=region_name)
            else:
                self.s3_client = session.client('s3')
                self.s3_resource = session.resource('s3')
        else:
            # Initialize S3 client and resource without profile
            if region_name:
                self.s3_client = boto3.client('s3', region_name=region_name)
                self.s3_resource = boto3.resource('s3', region_name=region_name)
            else:
                self.s3_client = boto3.client('s3')
                self.s3_resource = boto3.resource('s3')
            
        self.bucket = self.s3_resource.Bucket(bucket_name)
        
        logger.info(f"S3Helper initialized for bucket: {bucket_name}")

    def upload_object(self, key: str, data: Union[str, bytes], 
                     content_type: str = None, metadata: Dict[str, str] = None,
                     acl: str = 'private', storage_class: str = 'STANDARD') -> Dict[str, Any]:
        """
        Upload an object to S3.
        
        Args:
            key (str): S3 object key (file path)
            data (Union[str, bytes]): Data to upload
            content_type (str, optional): MIME type of the content
            metadata (Dict[str, str], optional): Metadata to attach to the object
            acl (str): Access control list setting
            storage_class (str): Storage class for the object
            
        Returns:
            Dict: Response from S3 operation
        """
        try:
            # Convert string data to bytes if necessary
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            logger.debug(f"Uploading object to s3://{self.bucket_name}/{key}, size: {len(data)} bytes")
            
            # Auto-detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(key)
                if not content_type:
                    content_type = 'binary/octet-stream'
            
            logger.debug(f"Content type: {content_type}, ACL: {acl}, Storage class: {storage_class}")
            
            # Prepare upload parameters
            upload_params = {
                'Key': key,
                'Body': data,
                'ContentType': content_type,
                'ACL': acl,
                'StorageClass': storage_class
            }
            
            if metadata:
                upload_params['Metadata'] = metadata
            
            # Upload the object
            response = self.s3_client.put_object(
                Bucket=self.bucket_name,
                **upload_params
            )
            
            # Get object URL
            object_url = f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
            
            logger.info(f"Object uploaded successfully to s3://{self.bucket_name}/{key}")
            
            return {
                'statusCode': 200,
                'success': True,
                'message': 'Object uploaded successfully',
                'data': {
                    'bucket': self.bucket_name,
                    'key': key,
                    'etag': response['ETag'].strip('"'),
                    'url': object_url,
                    'content_type': content_type,
                    'size': len(data)
                }
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to upload object: {error_code} - {error_message}")
            
            return {
                'statusCode': 500,
                'success': False,
                'error': error_code,
                'message': error_message
            }

    def download_object(self, key: str, decode_utf8: bool = False) -> Dict[str, Any]:
        """
        Download an object from S3.
        
        Args:
            key (str): S3 object key (file path)
            decode_utf8 (bool): Whether to decode bytes as UTF-8 string
            
        Returns:
            Dict: Downloaded object data and metadata
        """
        try:
            logger.debug(f"Downloading object from s3://{self.bucket_name}/{key}")
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            
            # Read the data
            data = response['Body'].read()
            logger.debug(f"Downloaded {len(data)} bytes")
            
            # Decode if requested
            if decode_utf8:
                try:
                    data = data.decode('utf-8')
                except UnicodeDecodeError:
                    logger.warning(f"Could not decode {key} as UTF-8")
            
            logger.info(f"Object downloaded successfully from s3://{self.bucket_name}/{key}")
            
            return {
                'statusCode': 200,
                'success': True,
                'data': {
                    'content': data,
                    'content_type': response.get('ContentType', ''),
                    'content_length': response.get('ContentLength', 0),
                    'last_modified': response.get('LastModified').isoformat() if response.get('LastModified') else None,
                    'etag': response.get('ETag', '').strip('"'),
                    'metadata': response.get('Metadata', {})
                }
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to download object: {error_code} - {error_message}")
            
            status_code = 404 if error_code == 'NoSuchKey' else 500
            
            return {
                'statusCode': status_code,
                'success': False,
                'error': error_code,
                'message': error_message
            }

    def delete_object(self, key: str) -> Dict[str, Any]:
        """
        Delete an object from S3.
        
        Args:
            key (str): S3 object key (file path)
            
        Returns:
            Dict: Response from S3 operation
        """
        try:
            response = self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            
            logger.info(f"Object deleted successfully from s3://{self.bucket_name}/{key}")
            
            return {
                'statusCode': 200,
                'success': True,
                'message': 'Object deleted successfully',
                'data': {
                    'bucket': self.bucket_name,
                    'key': key,
                    'delete_marker': response.get('DeleteMarker', False),
                    'version_id': response.get('VersionId', '')
                }
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to delete object: {error_code} - {error_message}")
            
            return {
                'statusCode': 500,
                'success': False,
                'error': error_code,
                'message': error_message
            }

    def list_objects(self, prefix: str = '', max_keys: int = 1000, 
                    continuation_token: str = None) -> Dict[str, Any]:
        """
        List objects in the S3 bucket.
        
        Args:
            prefix (str): Prefix to filter objects
            max_keys (int): Maximum number of objects to return
            continuation_token (str): Token for pagination
            
        Returns:
            Dict: List of objects and metadata
        """
        try:
            # Build list parameters
            list_params = {
                'Bucket': self.bucket_name,
                'MaxKeys': max_keys
            }
            
            if prefix:
                list_params['Prefix'] = prefix
                
            if continuation_token:
                list_params['ContinuationToken'] = continuation_token
            
            response = self.s3_client.list_objects_v2(**list_params)
            
            objects = []
            for obj in response.get('Contents', []):
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag'].strip('"'),
                    'storage_class': obj.get('StorageClass', 'STANDARD')
                })
            
            logger.info(f"Listed {len(objects)} objects from s3://{self.bucket_name}")
            
            return {
                'statusCode': 200,
                'success': True,
                'data': {
                    'objects': objects,
                    'count': len(objects),
                    'is_truncated': response.get('IsTruncated', False),
                    'next_continuation_token': response.get('NextContinuationToken'),
                    'prefix': prefix
                }
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to list objects: {error_code} - {error_message}")
            
            return {
                'statusCode': 500,
                'success': False,
                'error': error_code,
                'message': error_message
            }

    def object_exists(self, key: str) -> bool:
        """
        Check if an object exists in S3.
        
        Args:
            key (str): S3 object key
            
        Returns:
            bool: True if object exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise

    def get_object_metadata(self, key: str) -> Dict[str, Any]:
        """
        Get metadata for an S3 object without downloading the content.
        
        Args:
            key (str): S3 object key
            
        Returns:
            Dict: Object metadata
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            
            return {
                'statusCode': 200,
                'success': True,
                'data': {
                    'key': key,
                    'content_type': response.get('ContentType', ''),
                    'content_length': response.get('ContentLength', 0),
                    'last_modified': response.get('LastModified').isoformat() if response.get('LastModified') else None,
                    'etag': response.get('ETag', '').strip('"'),
                    'metadata': response.get('Metadata', {}),
                    'storage_class': response.get('StorageClass', 'STANDARD'),
                    'version_id': response.get('VersionId', '')
                }
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to get object metadata: {error_code} - {error_message}")
            
            status_code = 404 if error_code == '404' else 500
            
            return {
                'statusCode': status_code,
                'success': False,
                'error': error_code,
                'message': error_message
            }

    def copy_object(self, source_key: str, destination_key: str, 
                   source_bucket: str = None, metadata: Dict[str, str] = None,
                   storage_class: str = None) -> Dict[str, Any]:
        """
        Copy an object within S3.
        
        Args:
            source_key (str): Source object key
            destination_key (str): Destination object key
            source_bucket (str, optional): Source bucket name (defaults to current bucket)
            metadata (Dict[str, str], optional): New metadata for the copied object
            storage_class (str, optional): Storage class for the destination object
            
        Returns:
            Dict: Response from copy operation
        """
        try:
            if not source_bucket:
                source_bucket = self.bucket_name
            
            copy_source = {
                'Bucket': source_bucket,
                'Key': source_key
            }
            
            # Build copy parameters
            copy_params = {
                'CopySource': copy_source,
                'Bucket': self.bucket_name,
                'Key': destination_key
            }
            
            if metadata:
                copy_params['Metadata'] = metadata
                copy_params['MetadataDirective'] = 'REPLACE'
            
            if storage_class:
                copy_params['StorageClass'] = storage_class
            
            response = self.s3_client.copy_object(**copy_params)
            
            logger.info(f"Object copied from s3://{source_bucket}/{source_key} to s3://{self.bucket_name}/{destination_key}")
            
            return {
                'statusCode': 200,
                'success': True,
                'message': 'Object copied successfully',
                'data': {
                    'source_bucket': source_bucket,
                    'source_key': source_key,
                    'destination_bucket': self.bucket_name,
                    'destination_key': destination_key,
                    'etag': response['CopyObjectResult']['ETag'].strip('"'),
                    'last_modified': response['CopyObjectResult']['LastModified'].isoformat()
                }
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to copy object: {error_code} - {error_message}")
            
            return {
                'statusCode': 500,
                'success': False,
                'error': error_code,
                'message': error_message
            }

    def generate_presigned_url(self, key: str, operation: str = 'get_object', 
                              expiration: int = 3600, http_method: str = None) -> Dict[str, Any]:
        """
        Generate a presigned URL for S3 operations.
        
        Args:
            key (str): S3 object key
            operation (str): S3 operation ('get_object', 'put_object', 'delete_object')
            expiration (int): URL expiration time in seconds (default: 1 hour)
            http_method (str, optional): HTTP method for the presigned URL
            
        Returns:
            Dict: Presigned URL and metadata
        """
        try:
            params = {
                'Bucket': self.bucket_name,
                'Key': key
            }
            
            if http_method:
                url = self.s3_client.generate_presigned_url(
                    operation,
                    Params=params,
                    ExpiresIn=expiration,
                    HttpMethod=http_method
                )
            else:
                url = self.s3_client.generate_presigned_url(
                    operation,
                    Params=params,
                    ExpiresIn=expiration
                )
            
            expires_at = datetime.utcnow().timestamp() + expiration
            
            logger.info(f"Presigned URL generated for s3://{self.bucket_name}/{key}")
            
            return {
                'statusCode': 200,
                'success': True,
                'data': {
                    'url': url,
                    'expires_in': expiration,
                    'expires_at': datetime.fromtimestamp(expires_at).isoformat(),
                    'operation': operation,
                    'bucket': self.bucket_name,
                    'key': key
                }
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to generate presigned URL: {error_code} - {error_message}")
            
            return {
                'statusCode': 500,
                'success': False,
                'error': error_code,
                'message': error_message
            }

    def upload_file_from_path(self, file_path: str, key: str = None, 
                             metadata: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Upload a file from local file system to S3.
        
        Args:
            file_path (str): Local file path
            key (str, optional): S3 object key (defaults to filename)
            metadata (Dict[str, str], optional): Metadata to attach
            
        Returns:
            Dict: Response from upload operation
        """
        try:
            import os
            
            if not key:
                key = os.path.basename(file_path)
            
            # Auto-detect content type
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = 'binary/octet-stream'
            
            # Upload parameters
            extra_args = {'ContentType': content_type}
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.upload_file(file_path, self.bucket_name, key, ExtraArgs=extra_args)
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            logger.info(f"File uploaded successfully from {file_path} to s3://{self.bucket_name}/{key}")
            
            return {
                'statusCode': 200,
                'success': True,
                'message': 'File uploaded successfully',
                'data': {
                    'bucket': self.bucket_name,
                    'key': key,
                    'local_path': file_path,
                    'content_type': content_type,
                    'size': file_size
                }
            }
            
        except (ClientError, FileNotFoundError, OSError) as e:
            error_message = str(e)
            logger.error(f"Failed to upload file: {error_message}")
            
            return {
                'statusCode': 500,
                'success': False,
                'error': 'UploadError',
                'message': error_message
            }

    def download_file_to_path(self, key: str, file_path: str) -> Dict[str, Any]:
        """
        Download an S3 object to local file system.
        
        Args:
            key (str): S3 object key
            file_path (str): Local file path to save to
            
        Returns:
            Dict: Response from download operation
        """
        try:
            self.s3_client.download_file(self.bucket_name, key, file_path)
            
            # Get file size
            import os
            file_size = os.path.getsize(file_path)
            
            logger.info(f"File downloaded successfully from s3://{self.bucket_name}/{key} to {file_path}")
            
            return {
                'statusCode': 200,
                'success': True,
                'message': 'File downloaded successfully',
                'data': {
                    'bucket': self.bucket_name,
                    'key': key,
                    'local_path': file_path,
                    'size': file_size
                }
            }
            
        except (ClientError, OSError) as e:
            error_message = str(e)
            logger.error(f"Failed to download file: {error_message}")
            
            return {
                'statusCode': 500,
                'success': False,
                'error': 'DownloadError',
                'message': error_message
            }

    def delete_objects(self, keys: List[str]) -> Dict[str, Any]:
        """
        Delete multiple objects from S3 in a batch operation.
        
        Args:
            keys (List[str]): List of S3 object keys to delete
            
        Returns:
            Dict: Response from batch delete operation
        """
        try:
            if not keys:
                return {
                    'statusCode': 400,
                    'success': False,
                    'message': 'No keys provided for deletion'
                }
            
            # Prepare delete request
            delete_request = {
                'Objects': [{'Key': key} for key in keys],
                'Quiet': False
            }
            
            response = self.s3_client.delete_objects(
                Bucket=self.bucket_name,
                Delete=delete_request
            )
            
            deleted = response.get('Deleted', [])
            errors = response.get('Errors', [])
            
            logger.info(f"Batch delete completed. Deleted: {len(deleted)}, Errors: {len(errors)}")
            
            return {
                'statusCode': 200,
                'success': True,
                'message': f'Batch delete completed. {len(deleted)} objects deleted, {len(errors)} errors',
                'data': {
                    'deleted': [obj['Key'] for obj in deleted],
                    'errors': errors,
                    'deleted_count': len(deleted),
                    'error_count': len(errors)
                }
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to delete objects: {error_code} - {error_message}")
            
            return {
                'statusCode': 500,
                'success': False,
                'error': error_code,
                'message': error_message
            }

    def upload_json(self, key: str, data: Dict[str, Any], 
                   metadata: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Upload a JSON object to S3.
        
        Args:
            key (str): S3 object key
            data (Dict): Data to serialize as JSON
            metadata (Dict[str, str], optional): Metadata to attach
            
        Returns:
            Dict: Response from upload operation
        """
        try:
            json_data = json.dumps(data, indent=2, default=str)
            logger.debug(f"Uploading JSON object to s3://{self.bucket_name}/{key}, data size: {len(json_data)} chars")
            return self.upload_object(key, json_data, 'application/json', metadata)
            
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize data as JSON: {str(e)}")
            
            return {
                'statusCode': 400,
                'success': False,
                'error': 'SerializationError',
                'message': f'Failed to serialize data as JSON: {str(e)}'
            }

    def download_json(self, key: str) -> Dict[str, Any]:
        """
        Download and parse a JSON object from S3.
        
        Args:
            key (str): S3 object key
            
        Returns:
            Dict: Parsed JSON data
        """
        try:
            logger.debug(f"Downloading and parsing JSON from s3://{self.bucket_name}/{key}")
            download_result = self.download_object(key, decode_utf8=True)
            
            if not download_result['success']:
                return download_result
            
            # Parse JSON content
            json_data = json.loads(download_result['data']['content'])
            logger.debug(f"Successfully parsed JSON with {len(json_data)} top-level keys" if isinstance(json_data, dict) else f"Parsed JSON data type: {type(json_data)}")
            
            return {
                'statusCode': 200,
                'success': True,
                'data': {
                    'content': json_data,
                    'metadata': download_result['data']['metadata'],
                    'last_modified': download_result['data']['last_modified']
                }
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from {key}: {str(e)}")
            
            return {
                'statusCode': 400,
                'success': False,
                'error': 'JSONDecodeError',
                'message': f'Failed to parse JSON: {str(e)}'
            }

    def upload_base64(self, key: str, base64_data: str, 
                     content_type: str = None, metadata: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Upload base64-encoded data to S3.
        
        Args:
            key (str): S3 object key
            base64_data (str): Base64-encoded data
            content_type (str, optional): MIME type
            metadata (Dict[str, str], optional): Metadata to attach
            
        Returns:
            Dict: Response from upload operation
        """
        try:
            # Decode base64 data
            binary_data = base64.b64decode(base64_data)
            logger.debug(f"Decoded base64 data: {len(binary_data)} bytes for s3://{self.bucket_name}/{key}")
            
            return self.upload_object(key, binary_data, content_type, metadata)
            
        except Exception as e:
            logger.error(f"Failed to decode base64 data: {str(e)}")
            
            return {
                'statusCode': 400,
                'success': False,
                'error': 'Base64DecodeError',
                'message': f'Failed to decode base64 data: {str(e)}'
            }

    def get_bucket_info(self) -> Dict[str, Any]:
        """
        Get information about the S3 bucket.
        
        Returns:
            Dict: Bucket information
        """
        try:
            # Check if bucket exists and get location
            response = self.s3_client.get_bucket_location(Bucket=self.bucket_name)
            region = response.get('LocationConstraint') or 'us-east-1'
            
            # Get bucket versioning status
            try:
                versioning = self.s3_client.get_bucket_versioning(Bucket=self.bucket_name)
                versioning_status = versioning.get('Status', 'Disabled')
            except ClientError:
                versioning_status = 'Unknown'
            
            return {
                'statusCode': 200,
                'success': True,
                'data': {
                    'bucket_name': self.bucket_name,
                    'region': region,
                    'versioning_status': versioning_status,
                    'exists': True
                }
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Failed to get bucket info: {error_code} - {error_message}")
            
            status_code = 404 if error_code == 'NoSuchBucket' else 500
            
            return {
                'statusCode': status_code,
                'success': False,
                'error': error_code,
                'message': error_message
            }

    def search_objects(self, prefix: str = '', suffix: str = '', 
                      contains: str = '', max_results: int = 100) -> Dict[str, Any]:
        """
        Search for objects based on key patterns.
        
        Args:
            prefix (str): Key prefix to match
            suffix (str): Key suffix to match
            contains (str): Substring that key must contain
            max_results (int): Maximum number of results to return
            
        Returns:
            Dict: Matching objects
        """
        try:
            # List objects with prefix filter
            list_result = self.list_objects(prefix=prefix, max_keys=max_results)
            
            if not list_result['success']:
                return list_result
            
            objects = list_result['data']['objects']
            
            # Apply additional filters
            filtered_objects = []
            for obj in objects:
                key = obj['key']
                
                # Check suffix filter
                if suffix and not key.endswith(suffix):
                    continue
                
                # Check contains filter
                if contains and contains not in key:
                    continue
                
                filtered_objects.append(obj)
            
            logger.info(f"Search completed. Found {len(filtered_objects)} matching objects")
            
            return {
                'statusCode': 200,
                'success': True,
                'data': {
                    'objects': filtered_objects,
                    'count': len(filtered_objects),
                    'search_criteria': {
                        'prefix': prefix,
                        'suffix': suffix,
                        'contains': contains
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to search objects: {str(e)}")
            
            return {
                'statusCode': 500,
                'success': False,
                'error': 'SearchError',
                'message': str(e)
            }

    def move_object(self, source_key: str, destination_key: str) -> Dict[str, Any]:
        """
        Move an object to a new location (copy + delete).
        
        Args:
            source_key (str): Source object key
            destination_key (str): Destination object key
            
        Returns:
            Dict: Response from move operation
        """
        try:
            # First copy the object
            copy_result = self.copy_object(source_key, destination_key)
            
            if not copy_result['success']:
                return copy_result
            
            # Then delete the original
            delete_result = self.delete_object(source_key)
            
            if not delete_result['success']:
                # If delete fails, try to clean up the copy
                self.delete_object(destination_key)
                return delete_result
            
            logger.info(f"Object moved from s3://{self.bucket_name}/{source_key} to s3://{self.bucket_name}/{destination_key}")
            
            return {
                'statusCode': 200,
                'success': True,
                'message': 'Object moved successfully',
                'data': {
                    'source_key': source_key,
                    'destination_key': destination_key,
                    'bucket': self.bucket_name
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to move object: {str(e)}")
            
            return {
                'statusCode': 500,
                'success': False,
                'error': 'MoveError',
                'message': str(e)
            }


# Convenience functions for quick operations
def create_s3_helper(bucket_name: str, region_name: str = None) -> S3Helper:
    """
    Create an S3Helper instance.
    
    Args:
        bucket_name (str): Name of the S3 bucket
        region_name (str, optional): AWS region name
        
    Returns:
        S3Helper: Initialized S3 helper instance
    """
    return S3Helper(bucket_name, region_name)


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
        'body': json.dumps(body, default=str)
    }


def process_s3_event(event: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Process S3 event notifications from Lambda triggers.
    
    Args:
        event (Dict): Lambda event containing S3 notifications
        
    Returns:
        List[Dict]: Processed S3 event records
    """
    s3_records = []
    
    try:
        records = event.get('Records', [])
        
        for record in records:
            if record.get('eventSource') == 'aws:s3':
                s3_info = record.get('s3', {})
                
                bucket_name = s3_info.get('bucket', {}).get('name', '')
                object_key = unquote_plus(s3_info.get('object', {}).get('key', ''))
                object_size = s3_info.get('object', {}).get('size', 0)
                event_name = record.get('eventName', '')
                
                s3_records.append({
                    'event_name': event_name,
                    'bucket_name': bucket_name,
                    'object_key': object_key,
                    'object_size': object_size,
                    'event_time': record.get('eventTime', ''),
                    'region': record.get('awsRegion', ''),
                    'request_id': record.get('responseElements', {}).get('x-amz-request-id', '')
                })
        
        logger.info(f"Processed {len(s3_records)} S3 event records")
        
    except Exception as e:
        logger.error(f"Failed to process S3 event: {str(e)}")
    
    return s3_records


# Example usage in a Lambda function:
"""
import json
from s3_helper import S3Helper, lambda_response, process_s3_event

def lambda_handler(event, context):
    # Initialize S3 helper
    s3 = S3Helper('my-bucket-name')
    
    # Example 1: Upload a JSON file
    data = {'user_id': '123', 'name': 'John Doe', 'timestamp': '2024-01-01T00:00:00Z'}
    result = s3.upload_json('users/user123.json', data)
    
    if result['success']:
        return lambda_response(200, {
            'message': 'File uploaded successfully',
            'file_info': result['data']
        })
    else:
        return lambda_response(result['statusCode'], {
            'error': result['message']
        })

def s3_trigger_handler(event, context):
    # Handle S3 event triggers
    s3_records = process_s3_event(event)
    
    for record in s3_records:
        bucket_name = record['bucket_name']
        object_key = record['object_key']
        event_name = record['event_name']
        
        # Initialize S3 helper for the event bucket
        s3 = S3Helper(bucket_name)
        
        if 'ObjectCreated' in event_name:
            # Handle object creation
            print(f"New object created: {object_key}")
            
            # Example: Process uploaded file
            if object_key.endswith('.json'):
                result = s3.download_json(object_key)
                if result['success']:
                    data = result['data']['content']
                    # Process the JSON data here
                    print(f"Processed JSON data: {data}")
        
        elif 'ObjectRemoved' in event_name:
            # Handle object deletion
            print(f"Object deleted: {object_key}")
    
    return lambda_response(200, {
        'message': f'Processed {len(s3_records)} S3 events',
        'records': s3_records
    })
"""