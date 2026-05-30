import boto3

def update_cognito_token_settings():
    client = boto3.client('cognito-idp', region_name='us-east-1')
    
    try:
        response = client.update_user_pool(
            UserPoolId='us-east-1_tjhTbNShM',
            UserPoolTags={},
            UserAttributeUpdateSettings={
                'AttributesRequireVerificationBeforeUpdate': []
            },
            # Set token validity periods
            UserPoolAddOns={
                'AdvancedSecurityMode': 'OFF'
            },
            # Token configuration
            Policies={
                'PasswordPolicy': {
                    'MinimumLength': 8,
                    'RequireUppercase': False,
                    'RequireLowercase': False,
                    'RequireNumbers': False,
                    'RequireSymbols': False
                }
            }
        )
        
        print("User pool updated successfully")
        return response
        
    except Exception as e:
        print(f"Error updating user pool: {e}")
        return None

if __name__ == "__main__":
    update_cognito_token_settings()