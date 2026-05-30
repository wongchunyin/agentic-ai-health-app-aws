import boto3

def check_domain_status():
    """Check OpenSearch domain status and get endpoint"""
    session = boto3.Session(profile_name='account2')
    client = session.client('opensearch', region_name='us-east-1')
    
    try:
        response = client.describe_domain(DomainName='livewell-medical-search')
        domain = response['DomainStatus']
        
        print(f"Domain: {domain['DomainName']}")
        print(f"Status: {domain['Processing']}")
        print(f"Endpoint: {domain.get('Endpoint', 'Not ready yet')}")
        print(f"Created: {domain.get('Created', False)}")
        
        return domain.get('Endpoint')
        
    except Exception as e:
        print(f"Error checking domain: {e}")
        return None

if __name__ == "__main__":
    check_domain_status()