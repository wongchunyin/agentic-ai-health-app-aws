"""
Medical Search Manager using OpenSearch
"""

import json
import os
import logging
from typing import Dict, Any, List
from opensearchpy import OpenSearch, RequestsHttpConnection
from aws_requests_auth.aws_auth import AWSRequestsAuth
import boto3

logger = logging.getLogger()

class MedicalSearchManager:
    def __init__(self):
        endpoint_url = os.environ.get('OPENSEARCH_ENDPOINT', '')
        # Extract hostname from URL if it's a full URL
        if endpoint_url.startswith('https://'):
            self.endpoint = endpoint_url.replace('https://', '')
        else:
            self.endpoint = endpoint_url
        self.region = os.environ.get('AWS_REGION', 'us-east-1')
        self.index_name = os.environ.get('OPENSEARCH_INDEX', 'medical-qa')
        self.client = self._get_client()
    
    def _get_client(self):
        """Create OpenSearch client with AWS authentication"""
        try:
            credentials = boto3.Session().get_credentials()
            awsauth = AWSRequestsAuth(
                aws_access_key=credentials.access_key,
                aws_secret_access_key=credentials.secret_key,
                aws_token=credentials.token,
                aws_host=self.endpoint,
                aws_region=self.region,
                aws_service='es'
            )
            
            return OpenSearch(
                hosts=[{'host': self.endpoint, 'port': 443}],
                http_auth=awsauth,
                use_ssl=True,
                verify_certs=True,
                connection_class=RequestsHttpConnection
            )
        except Exception as e:
            logger.error(f"Error creating OpenSearch client: {str(e)}")
            raise
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant medical Q&A using text search"""
        try:
            # Use text search instead of vector search for simplicity
            search_body = {
                "size": top_k,
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["question^2", "answer", "topic^1.5"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                "_source": ["question", "answer", "topic", "source", "url"],
                "highlight": {
                    "fields": {
                        "question": {},
                        "answer": {"fragment_size": 150}
                    }
                }
            }
            
            response = self.client.search(index=self.index_name, body=search_body)
            
            results = []
            for hit in response['hits']['hits']:
                # Normalize score to 0-1 range for similarity
                max_score = response['hits']['max_score'] if response['hits']['max_score'] else 1.0
                similarity = hit['_score'] / max_score if max_score > 0 else 0.0
                
                result = {
                    'score': hit['_score'],
                    'similarity': similarity,
                    'question': hit['_source']['question'],
                    'answer': hit['_source']['answer'],
                    'topic': hit['_source']['topic'],
                    'source': hit['_source']['source'],
                    'url': hit['_source'].get('url', '')
                }
                
                # Add highlights if available
                if 'highlight' in hit:
                    result['highlights'] = hit['highlight']
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching medical data: {str(e)}")
            return []
    
    def search_by_topic(self, topic: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search for Q&A pairs by specific medical topic"""
        try:
            search_body = {
                "size": top_k,
                "query": {
                    "match": {
                        "topic": {
                            "query": topic,
                            "fuzziness": "AUTO"
                        }
                    }
                },
                "_source": ["question", "answer", "topic", "source", "url"]
            }
            
            response = self.client.search(index=self.index_name, body=search_body)
            
            results = []
            for hit in response['hits']['hits']:
                # Normalize score to 0-1 range for similarity
                max_score = response['hits']['max_score'] if response['hits']['max_score'] else 1.0
                similarity = hit['_score'] / max_score if max_score > 0 else 0.0
                
                results.append({
                    'score': hit['_score'],
                    'similarity': similarity,
                    'question': hit['_source']['question'],
                    'answer': hit['_source']['answer'],
                    'topic': hit['_source']['topic'],
                    'source': hit['_source']['source'],
                    'url': hit['_source'].get('url', '')
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching by topic: {str(e)}")
            return []