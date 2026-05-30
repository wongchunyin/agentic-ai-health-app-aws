import json
import os
from opensearchpy import OpenSearch, RequestsHttpConnection
from aws_requests_auth.aws_auth import AWSRequestsAuth
import boto3

# AWS OpenSearch configuration
OPENSEARCH_ENDPOINT = "your-opensearch-domain-endpoint.us-east-1.es.amazonaws.com"
REGION = "us-east-1"
INDEX_NAME = "medical-qa"

def get_opensearch_client():
    """Create OpenSearch client with AWS authentication"""
    credentials = boto3.Session().get_credentials()
    awsauth = AWSRequestsAuth(credentials, REGION, 'es')
    
    client = OpenSearch(
        hosts=[{'host': OPENSEARCH_ENDPOINT, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    return client

def create_index_mapping():
    """Create index with proper mapping for embeddings"""
    return {
        "mappings": {
            "properties": {
                "question": {"type": "text"},
                "answer": {"type": "text"},
                "topic": {"type": "keyword"},
                "source": {"type": "keyword"},
                "url": {"type": "keyword"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": 384  # all-MiniLM-L6-v2 dimension
                }
            }
        }
    }

def upload_embeddings(data_path):
    """Upload all embedding files to OpenSearch"""
    client = get_opensearch_client()
    
    # Create index if it doesn't exist
    if not client.indices.exists(INDEX_NAME):
        client.indices.create(INDEX_NAME, body=create_index_mapping())
        print(f"Created index: {INDEX_NAME}")
    
    folders = ["1_CancerGov_QA", "2_GARD_QA", "3_GHR_QA", "4_MPlus_Health_Topics_QA", 
               "5_NIDDK_QA", "6_NINDS_QA", "7_SeniorHealth_QA", "8_NHLBI_QA_XML", 
               "9_CDC_QA", "10_MPlus_ADAM_QA", "11_MPlusDrugs_QA", "12_MPlusHerbsSupplements_QA"]
    
    doc_id = 1
    for folder in folders:
        folder_path = os.path.join(data_path, folder)
        if os.path.exists(folder_path):
            embedding_files = [f for f in os.listdir(folder_path) if f.endswith('_embedding.json')]
            
            for file in embedding_files:
                filepath = os.path.join(folder_path, file)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Upload each Q&A pair
                for item in data:
                    try:
                        client.index(
                            index=INDEX_NAME,
                            id=doc_id,
                            body=item
                        )
                        doc_id += 1
                    except Exception as e:
                        print(f"Error uploading document {doc_id}: {e}")
                
                print(f"Uploaded {len(data)} documents from {file}")
    
    print(f"Upload completed. Total documents: {doc_id - 1}")

if __name__ == "__main__":
    # Update this path to your MedQuAD data location
    data_path = "/path/to/MedQuAD"
    upload_embeddings(data_path)