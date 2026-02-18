import logging
from typing import List, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage
from src.core.config import settings

logger = logging.getLogger("MultiKeyClient")

_llm_client = None

class MultiKeyToolRunner:
    """
    A custom Runnable that holds multiple Groq clients.
    If one client fails (429/RateLimit), it automatically retries with the next.
    """
    def __init__(self, clients: List[ChatGroq], tools: List[Any] = None):
        self.clients = clients
        self.tools = tools

    async def ainvoke(self, messages: List[BaseMessage]):
        """
        The Failover Loop: Tries keys sequentially until one works.
        """
        last_exception = None
        
        for i, client in enumerate(self.clients):
            try:
                # 1. Bind tools to the specific client instance if tools exist
                if self.tools:
                    runnable = client.bind_tools(self.tools)
                else:
                    runnable = client
                
                # 2. Attempt execution
                # logger.info(f"Attempting LLM call with Key #{i+1}...")
                return await runnable.ainvoke(messages)
            
            except Exception as e:
                # 3. Log failure and continue to next key
                logger.warning(f"⚠️ Key #{i+1} failed (Rate Limit or Error). Switching to backup...")
                last_exception = e
                continue
        
        # 4. If ALL keys fail, raise the last error
        logger.error("❌ All API keys exhausted. Transaction failed.")
        raise last_exception

class SmartLLMClient:
    def __init__(self, temperature: float = 0.1):
        """
        Initializes the Multi-Key Architecture.
        """
        self.groq_clients = []
        
        # 1. Load Primary Key
        if settings.groq_api_key:
            self.groq_clients.append(self._create_groq_client(settings.groq_api_key, temperature))
            
        # 2. Load Backup Key 2
        if settings.groq_api_key_2:
            self.groq_clients.append(self._create_groq_client(settings.groq_api_key_2, temperature))
            
        # 3. Load Backup Key 3
        if settings.groq_api_key_3:
            self.groq_clients.append(self._create_groq_client(settings.groq_api_key_3, temperature))
            
        if not self.groq_clients:
            logger.error("CRITICAL: No Groq API keys found in .env!")

        # 4. Initialize Gemini (Hail Mary Fallback)
        gemini_key = settings.gemini_api_key if settings.gemini_api_key else "MISSING_KEY"
        self.gemini = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=gemini_key,
            temperature=temperature
        )

    def _create_groq_client(self, key: str, temp: float) -> ChatGroq:
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            groq_api_key=key,
            temperature=temp,
            max_retries=1 # We handle retries ourselves, so fail fast
        )

    async def invoke(self, messages: List[BaseMessage]):
        """
        Standard text generation (No Tools) with Failover.
        """
        runner = MultiKeyToolRunner(self.groq_clients, tools=None)
        try:
            return await runner.ainvoke(messages)
        except Exception:
            # If all Groq keys fail, try Gemini
            logger.critical("All Groq keys dead. Falling back to Gemini.")
            return await self.gemini.ainvoke(messages)

    def bind_tools(self, tools: List[Any]):
        """
        Returns our custom MultiKeyRunner instead of a standard LangChain runnable.
        This injects the failover logic into the agents.
        """
        return MultiKeyToolRunner(self.groq_clients, tools=tools)

def get_llm_client(temperature: float = 0.1) -> SmartLLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = SmartLLMClient(temperature=temperature)
    return _llm_client