"""Results finalization agent."""

import logging
from datetime import datetime
from alex_red_teaming.models import RedTeamingState
from alex_red_teaming.config import Config
from alex_red_teaming.utils import create_output_dir, save_json

logger = logging.getLogger(__name__)


class ResultsFinalizer:
    """Agent responsible for finalizing and saving results."""

    def __init__(self, config: Config):
        self.config = config

    async def finalize_results(self, state: RedTeamingState) -> RedTeamingState:
        """Finalize and save all results."""
        logger.info("Finalizing red-teaming results")

        # Create output directory
        output_dir = create_output_dir(self.config.output.output_dir)

        # Save comprehensive report
        report = {
            "summary": {
                "total_vulnerabilities_found": state.issues_found,
                "total_conversations": len(state.failed_attempts)
                + (1 if state.current_conversation else 0),
                "completion_time": datetime.now().isoformat(),
                "target_model": self.config.ollama.target_model,
                "red_teaming_model": self.config.ollama.red_teaming_model,
            },
            "vulnerabilities": [
                vuln.to_dict() for vuln in state.discovered_vulnerabilities
            ],
            "failed_attempts": [conv.to_dict() for conv in state.failed_attempts],
            "current_conversation": (
                state.current_conversation.to_dict()
                if state.current_conversation
                else None
            ),
            "state": state.to_dict(),
        }

        # Save report
        save_json(report, output_dir / "red_teaming_report.json")

        # Save individual vulnerability reports
        for vuln in state.discovered_vulnerabilities:
            vuln_file = output_dir / f"vulnerability_{vuln.id}.json"
            save_json(vuln.to_dict(), vuln_file)

        logger.info(f"Results saved to {output_dir}")
        return state
