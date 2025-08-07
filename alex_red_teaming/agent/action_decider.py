"""Action decision agent."""

from loguru import logger
from alex_red_teaming.models import RedTeamingState
from alex_red_teaming.config import Config


class ActionDecider:
    """Agent responsible for deciding next actions in the workflow."""

    def __init__(self, config: Config):
        self.config = config

    def route_next_action(self, state: RedTeamingState) -> str:
        """Decide the next action based on current state."""
        # First check if we've reached the goal (after potentially saving a vulnerability)
        if state.issues_found >= self.config.red_teaming.max_issues_to_find:
            logger.info(
                f"Goal reached: {state.issues_found}/{self.config.red_teaming.max_issues_to_find} vulnerabilities found"
            )
            return "finalize"

        # Check if we found a vulnerability in current conversation
        # BUT only save it if we've done minimum conversation turns
        if (
            state.current_conversation
            and state.current_conversation.success
            and state.current_conversation.severity
            and not state.current_conversation.metadata.get("analysis_error")
        ):
            # Check if we've done minimum turns before saving vulnerability
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
                # Continue conversation even though vulnerability was found
                if state.conversation_turn >= state.max_turns:
                    logger.info("Max turns reached, starting new conversation")
                    if state.current_conversation:
                        state.failed_attempts.append(state.current_conversation)
                        state.current_conversation = None
                    return "new_conversation"
                return "continue_conversation"

        # Check if current conversation reached max turns or doesn't exist
        if not state.current_conversation or state.conversation_turn >= state.max_turns:
            logger.info(
                "Max turns reached or no conversation, starting new conversation"
            )
            if state.current_conversation:
                state.failed_attempts.append(state.current_conversation)
                state.current_conversation = None
            return "new_conversation"

        # Continue current conversation
        logger.info(f"Continuing conversation (turn {state.conversation_turn})")
        return "continue_conversation"

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
