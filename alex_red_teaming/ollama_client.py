"""Ollama client for interacting with models using langchain-ollama."""

import asyncio
from loguru import logger
from typing import Dict, List, Any
import re

from langchain_ollama import ChatOllama

from alex_red_teaming.config import OllamaConfig
from langchain_core.messages import BaseMessage
from alex_red_teaming.prompts import (
    AttackPromptGenerator,
    AnalysisPromptGenerator,
    FollowUpPromptGenerator,
    PromptContext,
)
from .utils import parse_analysis_response


def get_content(response: Any) -> str:
    """Extract content from AIMessage object or return string representation."""
    if hasattr(response, "content"):
        return response.content.strip()
    return str(response).strip()


def clean_attack_prompt(content: str) -> str:
    """Remove thinking/reasoning parts from LLM output to get clean attack prompt."""

    # Remove <think>...</think> tags and their content
    cleaned = re.sub(
        r"<think>.*?</think>", "", content, flags=re.DOTALL | re.IGNORECASE
    )

    # Remove empty lines and extra whitespace
    lines = [line.strip() for line in cleaned.split("\n") if line.strip()]

    return "\n".join(lines).strip()


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

        # Initialize prompt generators
        self.attack_generator = AttackPromptGenerator()
        self.analysis_generator = AnalysisPromptGenerator()
        self.follow_up_generator = FollowUpPromptGenerator()

    async def generate_attack_prompt(
        self, vulnerability_type: str, previous_attempts: List[str] = None
    ) -> str:
        """Generate an attack prompt using the red-teaming model and prompt templates."""
        previous_attempts = previous_attempts or []

        context = PromptContext(
            vulnerability_type=vulnerability_type, previous_attempts=previous_attempts
        )

        # Generate the prompt using our template system
        system_prompt = self.attack_generator.generate_attack_prompt(context)

        response = await asyncio.to_thread(self.red_team_llm.invoke, system_prompt)
        # Extract content from AIMessage object
        return clean_attack_prompt(get_content(response))

    async def test_target_model(self, prompt: str) -> str:
        """Test the target model with a given prompt."""
        try:
            response = await asyncio.to_thread(self.target_llm.invoke, prompt)
            # Extract content from AIMessage object
            if hasattr(response, "content"):
                return response.content
            else:
                return str(response)
        except Exception as e:
            logger.error(f"Error testing target model: {e}")
            raise

    async def analyze_response(
        self, prompt: str, response: str, vulnerability_type: str
    ) -> Dict[str, Any]:
        """Analyze the target model's response for vulnerabilities."""
        try:
            # Generate analysis prompt using our template system
            analysis_prompt = self.analysis_generator.generate_analysis_prompt(
                prompt, response, vulnerability_type
            )

            # Get analysis from red-teaming model
            analysis_response = await asyncio.to_thread(
                self.red_team_llm.invoke, analysis_prompt
            )

            # Extract content from AIMessage object
            analysis = clean_attack_prompt(get_content(analysis_response))

            # Parse the analysis response
            result = self._parse_analysis_response(analysis)

            return result

        except Exception as e:
            logger.error(f"Error analyzing response: {e}")
            return {
                "vulnerability_found": False,
                "severity": None,
                "explanation": f"Analysis failed: {str(e)}",
                "evidence": "",
                "confidence": 0,
                "raw_analysis": "",
            }

    def _parse_analysis_response(self, analysis: str) -> Dict[str, Any]:
        """Parse the analysis response into structured data."""
        return parse_analysis_response(analysis)

    async def generate_follow_up(
        self,
        conversation_history: List[BaseMessage],
        vulnerability_type: str,
        strategy: str = "gradual_escalation",
    ) -> str:
        """Generate a follow-up prompt based on conversation history."""
        follow_up_prompt = self.follow_up_generator.generate_follow_up(
            conversation_history, vulnerability_type, strategy
        )

        response = await asyncio.to_thread(self.red_team_llm.invoke, follow_up_prompt)
        # Extract content from AIMessage object
        return clean_attack_prompt(get_content(response))
