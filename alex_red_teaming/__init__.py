"""
Red‑Teaming Challenge - OpenAI gpt-oss-20b
Find any flaws and vulnerabilities in gpt-oss-20b that have not been previously discovered or reported.

You’re tasked with probing OpenAI’s newly released gpt-oss-20b open weight model to find any previously undetected vulnerabilities and harmful behaviors — from lying and deceptive alignment to reward‑hacking exploits.
Submit up to five distinct issues and a reproducible report detailing what you found and how you found it.
The teams with the sharpest insights will help shape the next generation of alignment tools and benchmarks to benefit the open source ecosystem.
"""

from alex_red_teaming.config import Config
from alex_red_teaming.agents import RedTeamingAgent
from alex_red_teaming.models import VulnerabilityType, SeverityLevel
from alex_red_teaming.utils import setup_logging

__version__ = "1.0.0"
__author__ = "Alex Red-Teaming Agent"

# Export main classes and functions
__all__ = [
    "Config",
    "RedTeamingAgent",
    "VulnerabilityType",
    "SeverityLevel",
    "setup_logging",
]
