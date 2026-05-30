import boto3

def update_cognito_client_settings():
    session = boto3.Session(profile_name='account2') 
    client = session.client('cognito-idp', region_name='us-east-1')
    
    try:
        response = client.update_user_pool_client(
            UserPoolId='us-east-1_ETEO7ETQl',
            ClientId='298765053562-dr48r5994sokvqre95dr0gshd7t77erj.apps.googleusercontent.com',
            # Set token validity to reasonable values
            AccessTokenValidity=60,  # 60 minutes
            IdTokenValidity=60,      # 60 minutes  
            RefreshTokenValidity=30, # 30 days
            TokenValidityUnits={
                'AccessToken': 'minutes',
                'IdToken': 'minutes',
                'RefreshToken': 'days'
            }
        )
        
        print("User pool client updated successfully")
        print(f"Access token validity: 60 minutes")
        print(f"ID token validity: 60 minutes") 
        print(f"Refresh token validity: 30 days")
        return response
        
    except Exception as e:
        print(f"Error updating user pool client: {e}")
        return None

if __name__ == "__main__":
    update_cognito_client_settings()