import logging
from typing import List, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage
from src.core.config import settings

logger = logging.getLogger(__name__)

_llm_client = None

class SmartLLMClient:
    def __init__(self, temperature: float = 0.1):
        self.gemini = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.gemini_api_key,
            temperature=temperature
        )
        
        self.groq = ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=settings.groq_api_key,
            temperature=temperature
        )

    async def invoke(self, messages: List[BaseMessage]):
        """
        Standard invoke with fallback logic.
        """
        try:
            return await self.gemini.ainvoke(messages)
        except Exception as e:
            logger.warning(f"Gemini invoke failed, falling back to Groq: {e}")
            return await self.groq.ainvoke(messages)

    def bind_tools(self, tools: List[Any]):
        """
        [NEW] Binds tools to the primary model (Gemini).
        Returns a Runnable that supports tool calling.
        """
        # We bind to Gemini by default. 
        # Note: If Gemini fails, fallback with tools is complex, 
        # so for this version, we bind strictly to Gemini.
        return self.gemini.bind_tools(tools)

def get_llm_client(temperature: float = 0.1) -> SmartLLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = SmartLLMClient(temperature=temperature)
    return _llm_client