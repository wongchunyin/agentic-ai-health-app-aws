import urllib.request
import json
from functools import wraps

def handle_cors(func):
    """Decorator to automatically handle CORS OPTIONS requests"""
    @wraps(func)
    def wrapper(event, context):
        if event.get("httpMethod") == "OPTIONS":
            msg_helper = MsgHelper()
            return msg_helper.handle_options_request()
        return func(event, context)
    return wrapper



class MsgHelper():
        
    def __init__(self):
        pass

    def format_api_gateway_response(self, status_code, body, headers={}, methods='GET,POST,OPTIONS'):
        """
        Formats a response object for AWS API Gateway.
        """
        default_headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': methods,
            'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Requested-With,Accept,Origin,User-Agent,Cache-Control,Pragma',
            'Access-Control-Allow-Credentials': 'false',
            'Access-Control-Max-Age': '86400'
        }
        return {
            'statusCode': status_code,
            'headers': {
                **default_headers,
                **headers
            },
            'body': json.dumps(body)
        }

    def success_response(self, data, headers={}, methods='GET,POST,OPTIONS'):
        """
        Returns a success (200 OK) response.
        """
        return self.format_api_gateway_response(200, data, headers, methods)

    def error_response(self, message, status_code=500, headers={}, methods='GET,POST,OPTIONS'):
        """
        Returns an error response.
        """
        return self.format_api_gateway_response(status_code, {"error": message}, headers, methods)

    def handle_options_request(self, allowed_methods='GET,POST,PUT,DELETE,OPTIONS'):
        """
        Handles CORS preflight OPTIONS requests with proper headers.
        """
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': allowed_methods,
                'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Requested-With,Accept,Origin,User-Agent,Cache-Control,Pragma',
                'Access-Control-Allow-Credentials': 'false',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }


    def send_get_request(self, url):
        """
        Sends a GET request to the specified URL and returns the decoded JSON response.
        """
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    data = response.read().decode('utf-8')
                    return json.loads(data)
                else:
                    return {"error": f"Request failed with status code: {response.status}"}
        except urllib.error.URLError as e:
            return {"error": f"URLError: {e.reason}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {e}"}

    def send_post_request(self, url, data, headers={}):
        """
        Sends a POST request with JSON data to the specified URL.
        """
        try:
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    response_data = response.read().decode('utf-8')
                    return json.loads(response_data)
                else:
                    return {"error": f"Request failed with status code: {response.status}"}
        except urllib.error.URLError as e:
            return {"error": f"URLError: {e.reason}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {e}"}