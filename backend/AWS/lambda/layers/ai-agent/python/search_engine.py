import json
from bs4 import BeautifulSoup
import urllib.request
import urllib.error
import os 
import logging


# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class SearchEngine():

    def __init__(self):
        self.page_length_limit = 1500  # Reduced from 2000
        self.max_results = 3  # Limit to top 3 results
        self.API_URL = "https://google.serper.dev/search"
        self.API_KEY = os.environ.get("SERPER_API_KEY")
        self.serper_result = None
        if not self.API_KEY:
            raise ValueError("SERPER_API_KEY environment variable not set")
        

    def fetch_text(self, url):

        HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/"
        }

        
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=5) as response:  # Reduced from 10 to 5 seconds
                html = response.read().decode("utf-8", errors="ignore")
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            logger.warning(f"FETCH_TEXT_ERROR: Skipping {url} -> {e}")
            return None

        soup = BeautifulSoup(html, "html.parser")
        for s in soup(["script", "style", "noscript"]):
            s.decompose()
        text = " ".join(soup.get_text().split())
        return text[:self.page_length_limit]  # truncate long pages
                



    def fetch_all(self):
        results = []
        
        try:
            parsed_data = json.loads(self.serper_result)
            organic_results = parsed_data.get('organic', [])[:self.max_results]  # Limit results
            logger.info(f"🔄 FETCH_ALL_START: Processing {len(organic_results)} organic results (limited to {self.max_results})")
            
            for i, item in enumerate(organic_results):
                url = item.get("link", "")
                title = item.get("title", "")
                logger.info(f"🔗 FETCH_URL_{i+1}: Fetching content from {url}")
                
                # fetch the content from the link
                txt = self.fetch_text(url)
                if txt:
                    json_str = {
                        "Source": url,
                        "title": title,
                        "content": txt
                    } 
                    results.append(json_str)
                    logger.info(f"✅ FETCH_SUCCESS_{i+1}: Successfully fetched {len(txt)} characters from {title}")
                else:
                    logger.warning(f"⚠️ FETCH_FAILED_{i+1}: Failed to fetch content from {url}")
            
            logger.info(f"📊 FETCH_ALL_COMPLETE: Successfully processed {len(results)} out of {len(organic_results)} results")
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ FETCH_ALL_JSON_ERROR: Failed to parse serper result: {e}")
        except Exception as e:
            logger.error(f"❌ FETCH_ALL_ERROR: Unexpected error in fetch_all: {e}")

        return results
    

    def search(self, query):
        logger.info(f"🔍 SEARCH_START: Starting search for query: '{query}'")
        
        payload = json.dumps({
            "q": query,
            "gl": "au",
            "num": self.max_results  # Request fewer results from API
        }).encode("utf-8")
        
        logger.info(f"📤 SEARCH_REQUEST: Sending request to Serper API")
        logger.debug(f"📤 SEARCH_PAYLOAD: {payload.decode('utf-8')}")

        headers = {
            'X-API-KEY': self.API_KEY,
            'Content-Type': 'application/json'
        }

        req = urllib.request.Request(self.API_URL, data=payload, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req) as response:
                self.serper_result = response.read().decode("utf-8")
                logger.info(f"📥 SEARCH_RESPONSE: Received response from Serper API")
                logger.debug(f"📥 SEARCH_RAW_RESULT: {self.serper_result[:500]}...")  # First 500 chars
                
                # Parse and log search results count
                try:
                    parsed_result = json.loads(self.serper_result)
                    organic_count = len(parsed_result.get('organic', []))
                    logger.info(f"📊 SEARCH_RESULTS_COUNT: Found {organic_count} organic results")
                except json.JSONDecodeError:
                    logger.warning("⚠️ SEARCH_PARSE_ERROR: Could not parse Serper response as JSON")
        
        except Exception as e:
            logger.error(f"❌ SEARCH_API_ERROR: Failed to get results from Serper API: {e}")
            raise

        logger.info(f"🔄 SEARCH_FETCH: Starting to fetch content from result URLs")
        results = self.fetch_all()
        logger.info(f"✅ SEARCH_COMPLETE: Search completed with {len(results)} processed results")
        
        return results

searchEngine = SearchEngine()