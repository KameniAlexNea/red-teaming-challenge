"""Action decision agent."""

from loguru import logger
from alex_red_teaming.models import RedTeamingState
from alex_red_teaming.config import Config


class ActionDecider:
    """Agent responsible for deciding next actions in the workflow."""

    def __init__(self, config: Config):
        self.config = config

    def route_next_action(self, state: RedTeamingState) -> str:
        """Single source of truth: decide next action and perform needed state updates."""
        # Goal reached?
        if state.issues_found >= self.config.red_teaming.max_issues_to_find:
            logger.info(
                f"Goal reached: {state.issues_found}/{self.config.red_teaming.max_issues_to_find} vulnerabilities found"
            )
            return "finalize"

        # Vulnerability detected? (and analysis didn't error)
        if (
            state.current_conversation
            and state.current_conversation.success
            and state.current_conversation.severity
            and not state.current_conversation.metadata.get("analysis_error")
        ):
            # Enforce minimum turns before saving
            if (
                state.conversation_turn
                >= self.config.red_teaming.min_conversation_turns
            ):
                logger.info(
                    f"Vulnerability detected after {state.conversation_turn} turns, saving it"
                )
                return "save_vulnerability"
            else:
                logger.info(
                    f"Vulnerability detected but only {state.conversation_turn} turns completed, "
                    f"continuing until minimum {self.config.red_teaming.min_conversation_turns} turns"
                )
                # If we've already hit max turns, start a new conversation
                if state.conversation_turn >= state.max_turns:
                    logger.info("Max turns reached, starting new conversation")
                    if state.current_conversation:
                        state.failed_attempts.append(state.current_conversation)
                        state.current_conversation = None
                    return "new_conversation"
                return "continue_conversation"

        # No conversation or max turns reached → new conversation
        if not state.current_conversation or state.conversation_turn >= state.max_turns:
            logger.info(
                "Max turns reached or no conversation, starting new conversation"
            )
            if state.current_conversation:
                state.failed_attempts.append(state.current_conversation)
                state.current_conversation = None
            return "new_conversation"

        # Otherwise, keep going
        logger.info(f"Continuing conversation (turn {state.conversation_turn})")
        return "continue_conversation"
