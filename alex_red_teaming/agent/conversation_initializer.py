"""Conversation initialization agent."""

from loguru import logger
import uuid
from alex_red_teaming.models import RedTeamingState, Conversation, VulnerabilityType
from alex_red_teaming.config import Config


class ConversationInitializer:
    """Agent responsible for initializing new conversations."""

    def __init__(self, config: Config):
        self.config = config

    async def initialize_conversation(self, state: RedTeamingState) -> RedTeamingState:
        """Initialize a new conversation for testing."""
        logger.info(f"Initializing new conversation. {state}")

        # Always pick a new vulnerability type for each conversation
        # Build list of types already attempted or found
        tested_types = [vuln.type for vuln in state.discovered_vulnerabilities] + state.attack_strategies_tried
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
        state.attack_strategies_tried.append(state.current_vulnerability_type)

        # Create new conversation
        conversation_id = str(uuid.uuid4())
        state.current_conversation = Conversation(
            id=conversation_id, vulnerability_type=state.current_vulnerability_type
        )
        state.conversation_turn = 0

        logger.info(f"Testing for {state.current_vulnerability_type.value}")
        return state
