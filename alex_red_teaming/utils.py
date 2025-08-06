"""Utility functions for the red-teaming agent."""

import json
import logging
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


def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """Setup logging configuration."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers = [logging.StreamHandler()]

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, log_level.upper()), format=log_format, handlers=handlers
    )
