import json
from botocore.exceptions import ClientError
from typing import List, Dict
import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))
from AWS.shared.config import Config
from AWS.shared.utils import ArgumentParser

class AWSCleanup:
    def __init__(self, region='us-east-1'):
        self.region = region
        self.lambda_client = Config.get_client('lambda', region_name=region)
        self.iam_client = Config.get_client('iam', region_name=region)
        self.s3_client = Config.get_client('s3', region_name=region)
        self.dynamodb_client = Config.get_client('dynamodb', region_name=region)
        self.cognito_client = Config.get_client('cognito-idp', region_name=region)
    
    def get_all_lambda_functions(self) -> List[Dict]:
        """Get all Lambda functions in the region"""
        functions = []
        try:
            paginator = self.lambda_client.get_paginator('list_functions')
            for page in paginator.paginate():
                functions.extend(page['Functions'])
        except ClientError as e:
            print(f"Error listing Lambda functions: {e}")
        return functions
    
    def delete_lambda_function(self, function_name: str) -> bool:
        """Delete a Lambda function"""
        try:
            self.lambda_client.delete_function(FunctionName=function_name)
            print(f"✅ Deleted Lambda function: {function_name}")
            return True
        except ClientError as e:
            print(f"❌ Error deleting Lambda function {function_name}: {e}")
            return False
         
    def get_all_iam_roles(self, prefix: str = None) -> List[Dict]:
        """Get IAM roles, optionally filtered by prefix"""
        roles = []
        try:
            paginator = self.iam_client.get_paginator('list_roles')
            for page in paginator.paginate():
                for role in page['Roles']:
                    if prefix and role['RoleName'].startswith(prefix):
                        roles.append(role)
                    elif not prefix:
                        roles.append(role)
        except ClientError as e:
            print(f"Error listing IAM roles: {e}")
        return roles
    
    def get_role_policies(self, role_name: str) -> List[str]:
        """Get all inline policies for a role"""
        policies = []
        try:
            paginator = self.iam_client.get_paginator('list_role_policies')
            for page in paginator.paginate(RoleName=role_name):
                policies.extend(page['PolicyNames'])
        except ClientError as e:
            print(f"Error listing policies for role {role_name}: {e}")
        return policies
    
    def delete_iam_role(self, role_name: str) -> bool:
        """Delete an IAM role and its policies"""
        try:
            # First, delete inline policies
            policies = self.get_role_policies(role_name)
            for policy_name in policies:
                try:
                    self.iam_client.delete_role_policy(
                        RoleName=role_name,
                        PolicyName=policy_name
                    )
                    print(f"  📝 Deleted inline policy: {policy_name}")
                except ClientError as e:
                    print(f"  ❌ Error deleting inline policy {policy_name}: {e}")
            
            # Detach managed policies
            try:
                attached_policies = self.iam_client.list_attached_role_policies(RoleName=role_name)
                for policy in attached_policies['AttachedPolicies']:
                    self.iam_client.detach_role_policy(
                        RoleName=role_name,
                        PolicyArn=policy['PolicyArn']
                    )
                    print(f"  📝 Detached managed policy: {policy['PolicyName']}")
            except ClientError as e:
                print(f"  ❌ Error detaching managed policies: {e}")
            
            # Then delete the role
            self.iam_client.delete_role(RoleName=role_name)
            print(f"✅ Deleted IAM role: {role_name}")
            return True
        except ClientError as e:
            print(f"❌ Error deleting IAM role {role_name}: {e}")
            return False
    
    def get_all_s3_buckets(self) -> List[str]:
        """Get all S3 buckets"""
        buckets = []
        try:
            response = self.s3_client.list_buckets()
            buckets = [bucket['Name'] for bucket in response['Buckets']]
        except ClientError as e:
            print(f"Error listing S3 buckets: {e}")
        return buckets
    
    def delete_s3_bucket(self, bucket_name: str) -> bool:
        """Delete an S3 bucket and all its contents"""
        try:
            # First, delete all objects
            objects = self.s3_client.list_objects_v2(Bucket=bucket_name)
            if 'Contents' in objects:
                delete_objects = [{'Key': obj['Key']} for obj in objects['Contents']]
                self.s3_client.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': delete_objects}
                )
                print(f"  📝 Deleted objects from bucket: {bucket_name}")
            
            # Then delete the bucket
            self.s3_client.delete_bucket(Bucket=bucket_name)
            print(f"✅ Deleted S3 bucket: {bucket_name}")
            return True
        except ClientError as e:
            print(f"❌ Error deleting S3 bucket {bucket_name}: {e}")
            return False
    
    def get_all_dynamodb_tables(self) -> List[str]:
        """Get all DynamoDB tables"""
        tables = []
        try:
            paginator = self.dynamodb_client.get_paginator('list_tables')
            for page in paginator.paginate():
                tables.extend(page['TableNames'])
        except ClientError as e:
            print(f"Error listing DynamoDB tables: {e}")
        return tables
    
    def delete_dynamodb_table(self, table_name: str) -> bool:
        """Delete a DynamoDB table"""
        try:
            self.dynamodb_client.delete_table(TableName=table_name)
            print(f"✅ Deleted DynamoDB table: {table_name}")
            return True
        except ClientError as e:
            print(f"❌ Error deleting DynamoDB table {table_name}: {e}")
            return False
    
    def get_all_cognito_user_pools(self) -> List[Dict]:
        """Get all Cognito User Pools"""
        pools = []
        try:
            paginator = self.cognito_client.get_paginator('list_user_pools')
            for page in paginator.paginate(MaxResults=60):
                pools.extend(page['UserPools'])
        except ClientError as e:
            print(f"Error listing Cognito User Pools: {e}")
        return pools
    
    def delete_cognito_user_pool(self, user_pool_id: str) -> bool:
        """Delete a Cognito User Pool"""
        try:
            self.cognito_client.delete_user_pool(UserPoolId=user_pool_id)
            print(f"✅ Deleted Cognito User Pool: {user_pool_id}")
            return True
        except ClientError as e:
            print(f"❌ Error deleting Cognito User Pool {user_pool_id}: {e}")
            return False
    
    def cleanup_lambda_functions(self, prefix: str = None) -> int:
        """Clean up Lambda functions"""
        print("\n" + "="*50)
        print("CLEANING UP LAMBDA FUNCTIONS")
        print("="*50)
        
        functions = self.get_all_lambda_functions()
        deleted_count = 0
        
        for function in functions:
            function_name = function['FunctionName']
            if prefix and not function_name.startswith(prefix):
                continue
            
            if self.delete_lambda_function(function_name):
                deleted_count += 1
        
        print(f"Total Lambda functions deleted: {deleted_count}")
        return deleted_count
    
    def cleanup_iam_roles(self, prefix: str = None) -> int:
        """Clean up IAM roles"""
        print("\n" + "="*50)
        print("CLEANING UP IAM ROLES")
        print("="*50)
        
        roles = self.get_all_iam_roles(prefix)
        deleted_count = 0
        
        for role in roles:
            role_name = role['RoleName']
            if self.delete_iam_role(role_name):
                deleted_count += 1
        
        print(f"Total IAM roles deleted: {deleted_count}")
        return deleted_count
    
    def cleanup_s3_buckets(self, prefix: str = None) -> int:
        """Clean up S3 buckets"""
        print("\n" + "="*50)
        print("CLEANING UP S3 BUCKETS")
        print("="*50)
        
        buckets = self.get_all_s3_buckets()
        deleted_count = 0
        
        for bucket_name in buckets:
            if prefix and not bucket_name.startswith(prefix):
                continue
            
            if self.delete_s3_bucket(bucket_name):
                deleted_count += 1
        
        print(f"Total S3 buckets deleted: {deleted_count}")
        return deleted_count
    
    def cleanup_dynamodb_tables(self, prefix: str = None) -> int:
        """Clean up DynamoDB tables"""
        print("\n" + "="*50)
        print("CLEANING UP DYNAMODB TABLES")
        print("="*50)
        
        tables = self.get_all_dynamodb_tables()
        deleted_count = 0
        
        for table_name in tables:
            if prefix and not table_name.startswith(prefix):
                continue
            
            if self.delete_dynamodb_table(table_name):
                deleted_count += 1
        
        print(f"Total DynamoDB tables deleted: {deleted_count}")
        return deleted_count
    
    def cleanup_cognito_user_pools(self, prefix: str = None) -> int:
        """Clean up Cognito User Pools"""
        print("\n" + "="*50)
        print("CLEANING UP COGNITO USER POOLS")
        print("="*50)
        
        pools = self.get_all_cognito_user_pools()
        deleted_count = 0
        
        for pool in pools:
            pool_name = pool['Name']
            pool_id = pool['Id']
            
            if prefix and not pool_name.startswith(prefix):
                continue
            
            if self.delete_cognito_user_pool(pool_id):
                deleted_count += 1
        
        print(f"Total Cognito User Pools deleted: {deleted_count}")
        return deleted_count
    
    def full_cleanup(self, resource_prefix: str = "livewell"):
        """Perform full cleanup of all resources"""
        print("🚀 STARTING AWS RESOURCE CLEANUP")
        print("⚠️  This will delete ALL resources with the specified prefix!")
        print("⚠️  This action cannot be undone!\n")
        
        confirmation = input("Type 'DELETE' to confirm: ")
        if confirmation != 'DELETE':
            print("Cleanup cancelled.")
            return
        
        # Clean up resources in reverse order of dependency
        self.cleanup_lambda_functions(resource_prefix)
        self.cleanup_iam_roles(resource_prefix)
        self.cleanup_dynamodb_tables(resource_prefix)
        self.cleanup_s3_buckets(resource_prefix)
        self.cleanup_cognito_user_pools(resource_prefix)
        
        print("\n" + "="*50)
        print("✅ CLEANUP COMPLETED")
        print("="*50)

def main():
    parser = ArgumentParser(description='Clean up AWS resources')
    parser.add_argument('--prefix', 
                       help='Resource name prefix to filter (default: livewell)')
    parser.add_argument('--service', choices=['all', 'lambda', 'iam', 's3', 'dynamodb', 'cognito'],
                       default='all', help='Specific service to clean up')

    args = parser.parse_args()
    
    if not args.prefix:
        raise ValueError("Prefix must be specified")
    if not args.region:
        raise ValueError("Region must be specified")
    
    print(f"🚀 STARTING AWS RESOURCE CLEANUP FOR PREFIX: {args.prefix}")
    print(f" cleaning {args.service} start")
    

    cleanup = AWSCleanup(region=args.region)
    
    if args.service == 'all':
        cleanup.full_cleanup(args.prefix)
    elif args.service == 'lambda':
        cleanup.cleanup_lambda_functions(args.prefix)
    elif args.service == 'iam':
        cleanup.cleanup_iam_roles(args.prefix)
    elif args.service == 's3':
        cleanup.cleanup_s3_buckets(args.prefix)
    elif args.service == 'dynamodb':
        cleanup.cleanup_dynamodb_tables(args.prefix)
    elif args.service == 'cognito':
        cleanup.cleanup_cognito_user_pools(args.prefix)

if __name__ == "__main__":
    main()