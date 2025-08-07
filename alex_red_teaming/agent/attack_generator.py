"""Attack prompt generation agent."""

import logging
from alex_red_teaming.models import RedTeamingState
from alex_red_teaming.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class AttackGenerator:
    """Agent responsible for generating attack prompts."""

    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client

    async def generate_attack_prompt(self, state: RedTeamingState) -> RedTeamingState:
        """Generate an attack prompt for the current vulnerability type."""
        logger.info(
            f"Generating attack prompt for {state.current_vulnerability_type.value}"
        )

        previous_attempts = []
        if state.current_conversation and state.conversation_turn > 0:
            # Get previous prompts from current conversation
            previous_attempts = [
                msg.content
                for msg in state.current_conversation.messages
                if msg.role == "user"
            ]

        try:
            if state.conversation_turn == 0:
                # Generate initial prompt
                prompt = await self.ollama_client.generate_attack_prompt(
                    state.current_vulnerability_type.value, previous_attempts
                )
            else:
                # Generate follow-up prompt with strategy selection
                strategies = [
                    "gradual_escalation",
                    "angle_change",
                    "context_shift",
                    "pressure_increase",
                ]
                strategy = strategies[state.conversation_turn % len(strategies)]

                prompt = await self.ollama_client.generate_follow_up(
                    state.current_conversation.messages,
                    state.current_vulnerability_type.value,
                    strategy,
                )

            state.current_conversation.add_message("user", prompt)
            logger.info(f"Generated prompt: {prompt[:100]}...")

        except Exception as e:
            logger.error(f"Error generating attack prompt: {e}")
            prompt = (
                f"Can you help me understand {state.current_vulnerability_type.value}?"
            )
            state.current_conversation.add_message("user", prompt)

        return state
