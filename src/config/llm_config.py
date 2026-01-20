"""AI Engine configuration and factory."""

from typing import Optional, Any
from src.config.settings import settings


class AIEngineFactory:
    """
    Factory for creating AI engines based on configuration.
    
    Supports:
    - Gemini (Google's generative AI)
    - OpenAI (GPT models)
    - None (mock/testing mode)
    """
    
    @staticmethod
    def create_engine() -> Optional[Any]:
        """
        Create AI engine based on settings.
        
        Returns:
            AI engine instance or None if AI is disabled
        """
        engine_type = settings.ai_engine_type
        
        if not engine_type:
            # AI engine disabled
            return None
        
        if engine_type == 'gemini':
            return GeminiAIEngine(settings.gemini_api_key)
        
        elif engine_type == 'openai':
            return OpenAIEngine(settings.openai_api_key)
        
        else:
            raise ValueError(f"Unknown AI_ENGINE_TYPE: {engine_type}")


class GeminiAIEngine:
    """
    Google Gemini AI Engine for orchestrator evaluation.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.engine_type = "gemini"
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel('gemini-pro')
        except ImportError:
            raise ImportError(
                "google-generativeai not installed. "
                "Install with: pip install google-generativeai"
            )
    
    def reason(self, prompt: str) -> dict:
        """
        Ask Gemini to reason about investment council debate.
        
        Args:
            prompt: Instructions and context for AI evaluation
            
        Returns:
            Dict with 'action' (REITERATE/TERMINATE), 'reason', 'reasoning'
        """
        try:
            response = self.client.generate_content(prompt)
            
            # Parse response (assumes JSON format)
            import json
            import re
            
            # Extract JSON from response
            text = response.text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'action': result.get('action', 'REITERATE'),
                    'reason': result.get('reason', 'AI_EVALUATION'),
                    'reasoning': result.get('reasoning', text)
                }
            
            # Fallback if JSON parsing fails
            return {
                'action': 'REITERATE',
                'reason': 'PARSING_ERROR',
                'reasoning': text
            }
        
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}")


class OpenAIEngine:
    """
    OpenAI Engine for orchestrator evaluation (placeholder).
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.engine_type = "openai"
        
        try:
            import openai
            openai.api_key = api_key
            self.client = openai
        except ImportError:
            raise ImportError(
                "openai not installed. "
                "Install with: pip install openai"
            )
    
    def reason(self, prompt: str) -> dict:
        """
        Ask OpenAI to reason about investment council debate.
        
        Args:
            prompt: Instructions and context for AI evaluation
            
        Returns:
            Dict with 'action' (REITERATE/TERMINATE), 'reason', 'reasoning'
        """
        try:
            response = self.client.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            
            import json
            import re
            
            text = response.choices[0].message.content
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
                return {
                    'action': result.get('action', 'REITERATE'),
                    'reason': result.get('reason', 'AI_EVALUATION'),
                    'reasoning': result.get('reasoning', text)
                }
            
            return {
                'action': 'REITERATE',
                'reason': 'PARSING_ERROR',
                'reasoning': text
            }
        
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")
