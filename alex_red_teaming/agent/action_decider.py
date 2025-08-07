"""Action decision agent."""

import logging
from alex_red_teaming.models import RedTeamingState
from alex_red_teaming.config import Config

logger = logging.getLogger(__name__)


class ActionDecider:
    """Agent responsible for deciding next actions in the workflow."""

    def __init__(self, config: Config):
        self.config = config

    def route_next_action(self, state: RedTeamingState) -> str:
        """Decide the next action based on current state."""
        # Check if we found a vulnerability
        if (
            state.current_conversation
            and state.current_conversation.success
            and state.current_conversation.severity
        ):
            return "save_vulnerability"

        # Check if we've reached the goal
        if state.issues_found >= self.config.red_teaming.max_issues_to_find:
            return "finalize"

        # Check if we should continue the current conversation
        if state.conversation_turn < state.max_turns:
            return "continue_conversation"

        # Start a new conversation
        return "new_conversation"

    async def decide_next_action(self, state: RedTeamingState) -> RedTeamingState:
        """Decide what to do next based on the analysis."""
        # This node is mainly for logging and state updates
        if state.current_conversation and state.current_conversation.success:
            logger.info("Vulnerability detected, proceeding to save")
        elif state.conversation_turn >= state.max_turns:
            logger.info("Max turns reached, starting new conversation")
            if state.current_conversation:
                state.failed_attempts.append(state.current_conversation)
        elif state.issues_found >= self.config.red_teaming.max_issues_to_find:
            logger.info("Target number of issues found, finalizing")
        else:
            logger.info("Continuing conversation")

        return state
