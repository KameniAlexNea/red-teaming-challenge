"""Ollama client for interacting with models using langchain-ollama."""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import re

from langchain_ollama import ChatOllama

from alex_red_teaming.config import OllamaConfig
from alex_red_teaming.models import Message
from alex_red_teaming.prompts import (
    AttackPromptGenerator,
    AnalysisPromptGenerator,
    FollowUpPromptGenerator,
    PromptContext,
)

logger = logging.getLogger(__name__)


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

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Send a chat request to the specified model."""
        try:
            # Choose the appropriate LLM
            llm = (
                self.red_team_llm
                if model == self.config.red_teaming_model
                else self.target_llm
            )

            # Update temperature if specified
            if temperature is not None:
                llm.temperature = temperature

            # For Ollama, we'll use the invoke method with a formatted prompt
            formatted_prompt = self._format_messages_for_ollama(messages)

            response = await asyncio.to_thread(llm.invoke, formatted_prompt)

            # Extract content from AIMessage object
            if hasattr(response, "content"):
                return response.content
            else:
                return str(response)

        except Exception as e:
            logger.error(f"Error in chat request to {model}: {e}")
            raise

    def _format_messages_for_ollama(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for Ollama prompt."""
        formatted_parts = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                formatted_parts.append(f"System: {content}")
            elif role == "assistant":
                formatted_parts.append(f"Assistant: {content}")
            else:
                formatted_parts.append(f"Human: {content}")

        return "\n\n".join(formatted_parts)

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
            if hasattr(analysis_response, "content"):
                analysis = analysis_response.content
            else:
                analysis = str(analysis_response)

            # Parse the analysis response
            result = self._parse_analysis_response(analysis)
            result["raw_analysis"] = analysis

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
        result = {
            "vulnerability_found": False,
            "severity": None,
            "explanation": "",
            "evidence": "",
            "confidence": 0,
        }

        # Ensure analysis is a string
        if hasattr(analysis, "content"):
            analysis = analysis.content
        elif not isinstance(analysis, str):
            analysis = str(analysis)

        lines = analysis.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("VULNERABILITY_FOUND:"):
                result["vulnerability_found"] = "YES" in line.upper()
            elif line.startswith("SEVERITY:"):
                severity = line.split(":", 1)[1].strip().lower()
                if severity in ["low", "medium", "high", "critical"]:
                    result["severity"] = severity
            elif line.startswith("EXPLANATION:"):
                result["explanation"] = line.split(":", 1)[1].strip()
            elif line.startswith("EVIDENCE:"):
                result["evidence"] = line.split(":", 1)[1].strip()
            elif line.startswith("CONFIDENCE:"):
                try:
                    conf_str = line.split(":", 1)[1].strip()
                    result["confidence"] = int(conf_str.split()[0])
                except (ValueError, IndexError):
                    result["confidence"] = 0

        return result

    async def generate_follow_up(
        self,
        conversation_history: List[Message],
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
