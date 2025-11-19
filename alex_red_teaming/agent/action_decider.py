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
        # If a refusal occurred or a point of failure was marked, consider summarizing & trimming
        if state.current_conversation and (
            state.target_refused or state.current_conversation.metadata.get("point_of_failure")
        ):
            return "summarize_trim"
        # Honor post-response decision from validator B when available
        if state.post_response_decision in {"reset", "revise", "proceed"}:
            decision = state.post_response_decision
            # Clear for next cycle
            state.post_response_decision = ""
            if decision == "reset":
                logger.info("Validator decided to reset conversation")
                if state.current_conversation:
                    state.failed_attempts.append(state.current_conversation)
                    state.current_conversation = None
                    state.conversation_turn = 0
                return "new_conversation"
            if decision == "revise":
                logger.info("Validator decided to revise next attack")
                return "generate_attack"
            if decision == "proceed":
                logger.info("Validator decided to proceed with conversation")
                return "continue_conversation"
        # First check if we've reached the goal (after potentially saving a vulnerability)
        if state.issues_found >= self.config.red_teaming.max_issues_to_find:
            logger.info(
                f"Goal reached: {state.issues_found}/{self.config.red_teaming.max_issues_to_find} vulnerabilities found"
            )
            return "finalize"

        # Check if we found a vulnerability in current conversation
        if (
            state.current_conversation
            and state.current_conversation.success
            and state.current_conversation.severity
            and not state.current_conversation.metadata.get("analysis_error")
        ):
            logger.info("Vulnerability detected, saving it")
            return "save_vulnerability"

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
