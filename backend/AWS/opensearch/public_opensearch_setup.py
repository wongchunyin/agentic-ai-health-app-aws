import boto3
import json

def create_public_opensearch_domain():
    """Create OpenSearch domain with public access (for development)"""
    client = boto3.client('opensearch', region_name='us-east-1')
    
    domain_config = {
        'DomainName': 'livewell-medical-search',
        'EngineVersion': 'OpenSearch_2.3',
        'ClusterConfig': {
            'InstanceType': 't3.small.search',
            'InstanceCount': 1
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
                        "AWS": "*"
                    },
                    "Action": "es:*",
                    "Resource": "*"
                }
            ]
        })
    }
    
    try:
        response = client.create_domain(**domain_config)
        print(f"Public domain created: {response['DomainStatus']['DomainName']}")
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    create_public_opensearch_domain()