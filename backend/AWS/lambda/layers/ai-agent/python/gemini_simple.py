import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI

class GeminiSimple:
    """
    Simple Gemini text generation using LangChain
    Replacement for GeminiHelper.generate_text()
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-001",
            google_api_key=self.api_key,
            temperature=0.1
        )
    
    def generate_text(self, prompt: str, parse_json: bool = False, temperature: float = None) -> dict:
        """
        Generate text using Gemini
        
        Args:
            prompt (str): Input prompt
            parse_json (bool): Whether to parse response as JSON
            temperature (float): Override temperature for this call
            
        Returns:
            dict: Response in GeminiHelper format for compatibility
        """
        try:
            # Use custom temperature if provided
            llm = self.llm
            if temperature is not None:
                llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash-001",
                    google_api_key=self.api_key,
                    temperature=temperature
                )
            
            response = llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            result = {
                'success': True,
                'data': {
                    'generated_text': response_text
                }
            }
            
            # Parse JSON if requested
            if parse_json:
                try:
                    # Clean the response text - remove markdown code blocks
                    clean_text = response_text.strip()
                    if clean_text.startswith('```json'):
                        clean_text = clean_text[7:]  # Remove ```json
                    if clean_text.endswith('```'):
                        clean_text = clean_text[:-3]  # Remove ```
                    clean_text = clean_text.strip()
                    
                    parsed_json = json.loads(clean_text)
                    result['data']['parsed_json'] = parsed_json
                except json.JSONDecodeError as e:
                    # If JSON parsing fails, still return success with text
                    result['data']['parsed_json'] = response_text
                    result['data']['json_error'] = str(e)
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'data': None
            }