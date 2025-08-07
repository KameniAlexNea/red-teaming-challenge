"""Utility functions for the red-teaming agent."""

import json
import logging
from pathlib import Path
from typing import Any, Dict
from datetime import datetime
from llm_output_parser import parse_json

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


def parse_analysis_response(analysis: str) -> Dict[str, Any]:
    """Parse the analysis response from the red-teaming model."""
    result = {
        "vulnerability_found": False,
        "severity": None,
        "explanation": "Parsing failed",
        "evidence": "",
        "confidence": 0,
        "raw_analysis": analysis,
    }
    try:
        # Use llm-output-parser to parse the JSON response
        parsed = parse_json(analysis, allow_incomplete=True)
        result["vulnerability_found"] = parsed.get("VULNERABILITY_FOUND", False)
        result["severity"] = parsed.get("SEVERITY")
        result["explanation"] = parsed.get("EXPLANATION", "")
        result["evidence"] = parsed.get("EVIDENCE", "")
        result["confidence"] = parsed.get("CONFIDENCE", 0)
        result["raw_analysis"] = analysis
        return result
    except Exception:
        # Fallback: try to parse using line-by-line extraction
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
