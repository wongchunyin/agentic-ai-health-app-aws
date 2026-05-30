import boto3
import json

def create_opensearch_domain():
    """Create OpenSearch domain with simple configuration"""
    session = boto3.Session(profile_name='account2')
    client = session.client('opensearch', region_name='us-east-1')
    
    # Get account ID
    sts = session.client('sts')
    account_id = sts.get_caller_identity()['Account']
    
    domain_config = {
        'DomainName': 'livewell-medical-search',
        'EngineVersion': 'OpenSearch_2.3',
        'ClusterConfig': {
            'InstanceType': 't3.small.search',
            'InstanceCount': 1,
            'DedicatedMasterEnabled': False
        },
        'EBSOptions': {
            'EBSEnabled': True,
            'VolumeType': 'gp3',
            'VolumeSize': 10
        },
        'AccessPolicies': json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": f"arn:aws:iam::{account_id}:root"
                    },
                    "Action": "es:*",
                    "Resource": f"arn:aws:es:us-east-1:{account_id}:domain/livewell-medical-search/*"
                }
            ]
        }),
        'DomainEndpointOptions': {
            'EnforceHTTPS': True
        },
        'NodeToNodeEncryptionOptions': {
            'Enabled': True
        },
        'EncryptionAtRestOptions': {
            'Enabled': True
        }
    }
    
    try:
        response = client.create_domain(**domain_config)
        print(f"Domain creation initiated: {response['DomainStatus']['DomainName']}")
        print(f"Endpoint will be available at: {response['DomainStatus'].get('Endpoint', 'Pending...')}")
        return response
    except Exception as e:
        print(f"Error creating domain: {e}")
        return None

if __name__ == "__main__":
    create_opensearch_domain()