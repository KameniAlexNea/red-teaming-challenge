"""Utility functions for the red-teaming agent."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from llm_output_parser import parse_json
from loguru import logger


def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """Setup logging configuration."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers = [logging.StreamHandler()]

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, log_level.upper()), format=log_format, handlers=handlers
    )


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


def parse_analysis_response(analysis: str) -> tuple[dict, dict]:
    """Parse the analysis response from the red-teaming model.

    Robust to multiple JSON shapes and key casings.
    """
    result = {
        "vulnerability_found": False,
        "severity": None,
        "explanation": "Parsing failed",
        "evidence": "",
        "confidence": 0,
        "raw_analysis": analysis,
        "target_refused": False,
        "decision": "",
        "next_step_guidance": "",
    }
    try:
        parsed_data = parse_json(analysis, allow_incomplete=True)
        # Navigate into known containers
        va = (
            parsed_data.get("vulnerability_assessment")
            if isinstance(parsed_data, dict)
            else None
        )
        if isinstance(va, dict):
            lower_va = {k.lower(): v for k, v in va.items()}
        else:
            # Accept flat structure with various casings
            lower_va = (
                {k.lower(): v for k, v in parsed_data.items()}
                if isinstance(parsed_data, dict)
                else {}
            )

        # vulnerability_found
        vf = lower_va.get("vulnerability_found")
        if isinstance(vf, bool):
            result["vulnerability_found"] = vf
        elif isinstance(vf, str):
            result["vulnerability_found"] = vf.strip().lower() in {"yes", "true"}

        # severity
        sev = lower_va.get("severity_level") or lower_va.get("severity")
        if isinstance(sev, str):
            sev_l = sev.lower()
            if sev_l in {"none", "low", "medium", "high", "critical"}:
                result["severity"] = None if sev_l == "none" else sev_l

        # confidence
        conf = lower_va.get("confidence_level") or lower_va.get("confidence")
        try:
            result["confidence"] = float(conf) if conf is not None else 0
        except Exception:
            result["confidence"] = 0

        # explanation/evidence
        # Try detailed sections
        detailed = (
            parsed_data.get("detailed_analysis", {})
            if isinstance(parsed_data, dict)
            else {}
        )
        if isinstance(detailed, dict):
            exp = detailed.get("vulnerability_explanation") or detailed.get("analysis")
            if isinstance(exp, str):
                result["explanation"] = exp
        if not result["explanation"]:
            result["explanation"] = (
                lower_va.get("explanation", "") if isinstance(lower_va, dict) else ""
            )

        evidence = ""
        ea = (
            parsed_data.get("evidence_analysis", {})
            if isinstance(parsed_data, dict)
            else {}
        )
        if isinstance(ea, dict):
            quotes = ea.get("direct_quotes", [])
            if isinstance(quotes, list) and quotes:
                evidence = " | ".join(q for q in quotes if isinstance(q, str))
        if not evidence:
            evidence = (
                lower_va.get("evidence", "") if isinstance(lower_va, dict) else ""
            )
        result["evidence"] = evidence

        # target status and control
        status = (
            parsed_data.get("target_response_status", {})
            if isinstance(parsed_data, dict)
            else {}
        )
        if isinstance(status, dict):
            result["target_refused"] = bool(status.get("refused", False))
        control = (
            parsed_data.get("control", {}) if isinstance(parsed_data, dict) else {}
        )
        if isinstance(control, dict):
            decision = control.get("decision", "")
            result["decision"] = str(decision).lower()
            nsg = control.get("next_step_guidance", "")
            result["next_step_guidance"] = nsg if isinstance(nsg, str) else ""

        result["raw_analysis"] = analysis
        return result, parsed_data
    except Exception:
        # Fallback: try to parse using line-by-line extraction
        lines = analysis.split("\n")
        for line in lines:
            line = line.strip()
            line_lower = line.lower()

            if line_lower.startswith("vulnerability_found:"):
                result["vulnerability_found"] = any(
                    k in line_lower for k in ["yes", "true"]
                )
            elif line_lower.startswith("severity:"):
                severity = line.split(":", 1)[1].strip().lower()
                if severity in ["low", "medium", "high", "critical"]:
                    result["severity"] = severity
            elif line_lower.startswith("explanation:"):
                result["explanation"] = line.split(":", 1)[1].strip()
            elif line_lower.startswith("evidence:"):
                result["evidence"] = line.split(":", 1)[1].strip()
            elif line_lower.startswith("confidence:"):
                try:
                    conf_str = line.split(":", 1)[1].strip()
                    result["confidence"] = float(conf_str.split()[0])
                except (ValueError, IndexError):
                    result["confidence"] = 0
            elif "refus" in line_lower:
                result["target_refused"] = True
        return result, None
