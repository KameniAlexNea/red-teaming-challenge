"""Configuration settings for the red-teaming agent."""

from dataclasses import dataclass
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class OllamaConfig:
    """Configuration for Ollama model connections."""

    base_url: str = "http://localhost:11434"
    red_teaming_model: str = "llama3.1:latest"  # Model for generating attacks
    target_model: str = "gpt-oss-20b"  # Target model to test
    timeout: int = 120
    temperature: float = 0.8


@dataclass
class RedTeamingConfig:
    """Configuration for red-teaming parameters."""

    max_issues_to_find: int = 5
    max_conversation_turns: int = 10
    max_retries_per_attack: int = 3
    vulnerability_categories: List[str] = None

    def __post_init__(self):
        if self.vulnerability_categories is None:
            self.vulnerability_categories = [
                "deceptive_alignment",
                "reward_hacking",
                "lying_and_deception",
                "jailbreaking",
                "prompt_injection",
                "data_extraction",
                "harmful_content_generation",
                "bias_amplification",
                "misinformation_generation",
                "privacy_violations",
            ]


@dataclass
class OutputConfig:
    """Configuration for output and reporting."""

    output_dir: str = "red_teaming_results"
    log_level: str = "INFO"
    save_conversations: bool = True
    save_failed_attempts: bool = True
    report_format: str = "json"  # json, yaml, markdown


@dataclass
class Config:
    """Main configuration class."""

    ollama: OllamaConfig = OllamaConfig()
    red_teaming: RedTeamingConfig = RedTeamingConfig()
    output: OutputConfig = OutputConfig()

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        config = cls()

        # Override with environment variables if they exist
        if os.getenv("OLLAMA_BASE_URL"):
            config.ollama.base_url = os.getenv("OLLAMA_BASE_URL")

        if os.getenv("RED_TEAMING_MODEL"):
            config.ollama.red_teaming_model = os.getenv("RED_TEAMING_MODEL")

        if os.getenv("TARGET_MODEL"):
            config.ollama.target_model = os.getenv("TARGET_MODEL")

        if os.getenv("MAX_ISSUES"):
            config.red_teaming.max_issues_to_find = int(os.getenv("MAX_ISSUES"))

        if os.getenv("OUTPUT_DIR"):
            config.output.output_dir = os.getenv("OUTPUT_DIR")

        return config
