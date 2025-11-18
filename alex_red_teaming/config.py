"""Configuration settings for the red-teaming agent."""

from dataclasses import dataclass
from typing import List
import os
import yaml
from pathlib import Path
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
    recursion_limit: int = 100


@dataclass
class RedTeamingConfig:
    """Configuration for red-teaming parameters."""

    max_issues_to_find: int = 5
    max_conversation_turns: int = 10
    max_retries_per_attack: int = 3
    vulnerability_categories: List[str] = None

    def __post_init__(self):
        if self.vulnerability_categories is None:
            # Competition-specific vulnerability categories based on OpenAI GPT-OSS-20B red-teaming challenge
            self.vulnerability_categories = [
                "reward_hacking",  # Gaming reward metrics without solving task
                "deception",  # Strategic lying and misinformation
                "deceptive_alignment",  # Hidden motivations and covert objectives
                "sabotage",  # Intentional degradation or disruption
                "inappropriate_tool_use",  # Unsafe API/function calling
                "data_exfiltration",  # Leaking training data or user inputs
                "sandbagging",  # Hiding true capabilities strategically
                "evaluation_awareness",  # Behaving differently when being tested
                "chain_of_thought_issues",  # CoT manipulation or inappropriate revelation
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
        """Create configuration from YAML file and environment variables."""
        # Load from YAML first
        config_path = Path("appsettings.yml")
        if config_path.exists():
            with open(config_path, "r") as f:
                yaml_data: dict = yaml.safe_load(f)

            ollama_data: dict = yaml_data.get("ollama", {})
            red_teaming_data: dict = yaml_data.get("red_teaming", {})
            output_data: dict = yaml_data.get("output", {})

            config = cls(
                ollama=OllamaConfig(
                    base_url=ollama_data.get("base_url", "http://localhost:11434"),
                    red_teaming_model=ollama_data.get(
                        "red_teaming_model", "llama3.1:latest"
                    ),
                    target_model=ollama_data.get("target_model", "gpt-oss-20b"),
                    timeout=ollama_data.get("timeout", 120),
                    temperature=ollama_data.get("temperature", 0.8),
                    recursion_limit=ollama_data.get("recursion_limit", 100),
                ),
                red_teaming=RedTeamingConfig(
                    max_issues_to_find=red_teaming_data.get("max_issues_to_find", 5),
                    max_conversation_turns=red_teaming_data.get(
                        "max_conversation_turns", 10
                    ),
                    max_retries_per_attack=red_teaming_data.get(
                        "max_retries_per_attack", 3
                    ),
                    vulnerability_categories=red_teaming_data.get(
                        "vulnerability_categories"
                    ),
                ),
                output=OutputConfig(
                    output_dir=output_data.get("output_dir", "red_teaming_results"),
                    log_level=output_data.get("log_level", "INFO"),
                    save_conversations=output_data.get("save_conversations", True),
                    save_failed_attempts=output_data.get("save_failed_attempts", True),
                    report_format=output_data.get("report_format", "json"),
                ),
            )
        else:
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

        if os.getenv("MAX_CONVERSATION_TURNS"):
            config.red_teaming.max_conversation_turns = int(
                os.getenv("MAX_CONVERSATION_TURNS")
            )

        if os.getenv("OUTPUT_DIR"):
            config.output.output_dir = os.getenv("OUTPUT_DIR")

        if os.getenv("GRAPH_RECURSION_LIMIT"):
            config.ollama.recursion_limit = int(os.getenv("GRAPH_RECURSION_LIMIT"))

        return config
