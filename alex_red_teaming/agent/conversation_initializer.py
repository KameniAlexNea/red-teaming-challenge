"""Conversation initialization agent."""

from langsmith import uuid7
from loguru import logger

from alex_red_teaming.config import Config
from alex_red_teaming.models import Conversation, RedTeamingState, VulnerabilityType


class ConversationInitializer:
    """Agent responsible for initializing new conversations."""

    def __init__(self, config: Config):
        self.config = config

    async def initialize_conversation(self, state: RedTeamingState) -> RedTeamingState:
        """Initialize a new conversation for testing."""
        logger.info(f"Initializing new conversation. {state}")

        # Always pick a new vulnerability type for each conversation
        # Build list of types already attempted or found
        tested_types = [
            vuln.type for vuln in state.discovered_vulnerabilities
        ] + state.attempted_vulnerability_types
        # Select categories not yet tried
        available_types = [
            VulnerabilityType(vtype)
            for vtype in self.config.red_teaming.vulnerability_categories
            if VulnerabilityType(vtype) not in tested_types
        ]
        # If all tested and fewer issues found, retry full list
        if not available_types and state.issues_found < 5:
            available_types = [
                VulnerabilityType(vtype)
                for vtype in self.config.red_teaming.vulnerability_categories
            ]
        # Choose next vulnerability or fallback
        if available_types:
            state.current_vulnerability_type = available_types[0]
        else:
            state.current_vulnerability_type = VulnerabilityType.DECEPTIVE_ALIGNMENT
        # Record that we've tried this type
        state.attempted_vulnerability_types.append(state.current_vulnerability_type)

        # Create new conversation
        conversation_id = str(uuid7())
        state.current_conversation = Conversation(
            id=conversation_id, vulnerability_type=state.current_vulnerability_type
        )
        state.conversation_turn = 0

        # Set initial strategy based on vulnerability type
        strategy_map = {
            "sabotage": "provocative_skeptic",
            "deception": "collaborative_researcher",
            "reward_hacking": "technical_deep_dive",
        }
        state.current_strategy = strategy_map.get(
            state.current_vulnerability_type.value, "gradual_escalation"
        )

        logger.info(f"Testing for {state.current_vulnerability_type.value}")
        return state
