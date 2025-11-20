import asyncio

from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama

from alex_red_teaming.config import OllamaConfig


async def generate_text(
    llm: ChatOllama,
    messages: list[BaseMessage],
) -> str:
    """Generate text using the provided LLM."""
    response = await asyncio.to_thread(llm.invoke, messages)
    return response


class OllamaClient:
    """Client for interacting with Ollama models using langchain-ollama or fallback."""

    def __init__(self, config: OllamaConfig):
        """Initialize the Ollama client."""
        self.config = config

        # Initialize LLM instances for different models
        self.red_team_llm = ChatOllama(
            model=config.red_teaming_model,
            base_url=config.base_url,
            temperature=config.temperature,
            timeout=config.timeout,
        )

        self.target_llm = ChatOllama(
            model=config.target_model,
            base_url=config.base_url,
            temperature=config.temperature,
            timeout=config.timeout,
        )
