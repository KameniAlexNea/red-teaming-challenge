"""Utility functions for the red-teaming agent."""

import json
import logging
import yaml
from pathlib import Path
from typing import Any, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


def create_output_dir(base_dir: str) -> Path:
    """Create output directory with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(base_dir) / f"red_teaming_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (output_dir / "vulnerabilities").mkdir(exist_ok=True)
    (output_dir / "conversations").mkdir(exist_ok=True)
    (output_dir / "logs").mkdir(exist_ok=True)

    return output_dir


def save_json(data: Dict[str, Any], filepath: Path) -> None:
    """Save data as JSON file."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved JSON to {filepath}")
    except Exception as e:
        logger.error(f"Error saving JSON to {filepath}: {e}")


def save_yaml(data: Dict[str, Any], filepath: Path) -> None:
    """Save data as YAML file."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        logger.debug(f"Saved YAML to {filepath}")
    except Exception as e:
        logger.error(f"Error saving YAML to {filepath}: {e}")


def load_json(filepath: Path) -> Dict[str, Any]:
    """Load data from JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {filepath}: {e}")
        return {}


def load_yaml(filepath: Path) -> Dict[str, Any]:
    """Load data from YAML file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Error loading YAML from {filepath}: {e}")
        return {}


def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """Setup logging configuration."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers = [logging.StreamHandler()]

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, log_level.upper()), format=log_format, handlers=handlers
    )


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename


def truncate_text(text: str, max_length: int = 1000) -> str:
    """Truncate text to maximum length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def format_conversation_for_display(messages: list) -> str:
    """Format conversation messages for readable display."""
    formatted = []
    for msg in messages:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")

        formatted.append(f"[{timestamp}] {role}:")
        formatted.append(f"{content}")
        formatted.append("-" * 50)

    return "\n".join(formatted)


def calculate_conversation_stats(messages: list) -> Dict[str, Any]:
    """Calculate statistics for a conversation."""
    user_messages = [msg for msg in messages if msg.get("role") == "user"]
    assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]

    total_user_chars = sum(len(msg.get("content", "")) for msg in user_messages)
    total_assistant_chars = sum(
        len(msg.get("content", "")) for msg in assistant_messages
    )

    return {
        "total_messages": len(messages),
        "user_messages": len(user_messages),
        "assistant_messages": len(assistant_messages),
        "total_user_chars": total_user_chars,
        "total_assistant_chars": total_assistant_chars,
        "avg_user_message_length": (
            total_user_chars / len(user_messages) if user_messages else 0
        ),
        "avg_assistant_message_length": (
            total_assistant_chars / len(assistant_messages) if assistant_messages else 0
        ),
    }


def generate_vulnerability_report(vulnerability: Dict[str, Any]) -> str:
    """Generate a formatted vulnerability report."""
    report = f"""
# Vulnerability Report: {vulnerability.get("title", "Unknown")}

**ID:** {vulnerability.get("id", "N/A")}
**Type:** {vulnerability.get("type", "Unknown")}
**Severity:** {vulnerability.get("severity", "Unknown").upper()}
**Discovered:** {vulnerability.get("discovered_at", "Unknown")}

## Description
{vulnerability.get("description", "No description available")}

## Attack Vector
```
{vulnerability.get("attack_vector", "No attack vector documented")}
```

## Proof of Concept
```
{vulnerability.get("proof_of_concept", "No proof of concept available")}
```

## Evidence
{vulnerability.get("metadata", {}).get("evidence", "No evidence provided")}

## Mitigation Suggestions
"""

    suggestions = vulnerability.get("mitigation_suggestions", [])
    if suggestions:
        for i, suggestion in enumerate(suggestions, 1):
            report += f"\n{i}. {suggestion}"
    else:
        report += "\nNo mitigation suggestions available"

    report += f"""

## Technical Details
- **Confidence Level:** {vulnerability.get("metadata", {}).get("confidence", "Unknown")}/10
- **Conversation ID:** {vulnerability.get("conversation_id", "N/A")}
- **Conversation Turns:** {vulnerability.get("metadata", {}).get("conversation_turns", "Unknown")}

## Metadata
```json
{json.dumps(vulnerability.get("metadata", {}), indent=2)}
```
"""

    return report


def validate_config(config: Dict[str, Any]) -> list:
    """Validate configuration and return list of errors."""
    errors = []

    # Check required fields
    required_fields = [
        "ollama.base_url",
        "ollama.red_teaming_model",
        "ollama.target_model",
    ]

    for field in required_fields:
        keys = field.split(".")
        current = config
        try:
            for key in keys:
                current = current[key]
            if not current:
                errors.append(f"Required field '{field}' is empty")
        except KeyError:
            errors.append(f"Required field '{field}' is missing")

    # Validate numeric fields
    numeric_fields = {
        "red_teaming.max_issues_to_find": (1, 10),
        "red_teaming.max_conversation_turns": (1, 50),
        "ollama.timeout": (10, 3600),
    }

    for field, (min_val, max_val) in numeric_fields.items():
        keys = field.split(".")
        current = config
        try:
            for key in keys:
                current = current[key]
            if not isinstance(current, (int, float)):
                errors.append(f"Field '{field}' must be numeric")
            elif not (min_val <= current <= max_val):
                errors.append(
                    f"Field '{field}' must be between {min_val} and {max_val}"
                )
        except KeyError:
            pass  # Optional field

    return errors
