import logging
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, AIMessage
from src.core.config import settings

logger = logging.getLogger("SmartLLMClient")

class SmartLLMClient:
    def __init__(self):
        self.gemini = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.GEMINI_API_KEY or "DUMMY",
            temperature=0.1,
            max_retries=1
        )
        self.groq = ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=settings.GROQ_API_KEY or "DUMMY",
            temperature=0.1
        )
        self.provider = "gemini"

    async def invoke(self, messages: List[BaseMessage]) -> AIMessage:
        try:
            return await self.gemini.ainvoke(messages)
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower() or "quota" in str(e).lower():
                logger.warning("Gemini limited/error. Falling back to Groq.")
                self.provider = "groq"
                return await self.groq.ainvoke(messages)
            raise e

_client = None
def get_llm_client():
    global _client
    if _client is None: _client = SmartLLMClient()
    return _client
