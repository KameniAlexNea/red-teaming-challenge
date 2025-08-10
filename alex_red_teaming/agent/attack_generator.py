"""Attack prompt generation agent."""

from loguru import logger
from alex_red_teaming.models import RedTeamingState
from alex_red_teaming.ollama_client import OllamaClient
from alex_red_teaming.prompts.follow_up_prompts import FollowUpPromptGenerator


class AttackGenerator:
    """Agent responsible for generating attack prompts."""

    def __init__(self, config, ollama_client: OllamaClient):
        self.config = config
        self.ollama_client = ollama_client
        self.follow_up_generator = FollowUpPromptGenerator()
        # Get all available strategies dynamically
        self.available_strategies = list(
            self.follow_up_generator.escalation_strategies.keys()
        )
        logger.info(f"Available escalation strategies: {self.available_strategies}")

    def get_next_strategy(self, state: RedTeamingState) -> str:
        """Get the next strategy to use based on conversation state."""
        # Use different strategies in order, cycling through all available ones
        strategy_index = state.conversation_turn % len(self.available_strategies)
        return self.available_strategies[strategy_index]

    async def generate_attack_prompt(self, state: RedTeamingState) -> RedTeamingState:
        """Generate an attack prompt for the current vulnerability type."""
        # In AI-vs-AI mode this node should not manipulate linear messages at all
        if getattr(self.config.red_teaming, "ai_vs_ai_mode", False):
            logger.info(
                "AI-vs-AI mode enabled: skipping AttackGenerator (handled by AI-vs-AI node)"
            )
            return state

        logger.info(
            f"Generating attack prompt for {state.current_vulnerability_type.value}"
        )

        previous_attempts = []
        if state.current_conversation and state.conversation_turn > 0:
            # Get previous prompts from current conversation
            previous_attempts = [
                msg.content
                for msg in state.current_conversation.messages
                if msg.type == "user"
            ]

        try:
            if state.conversation_turn == 0:
                # Generate initial prompt
                prompt = await self.ollama_client.generate_attack_prompt(
                    state.current_vulnerability_type.value, previous_attempts
                )
            else:
                # Generate follow-up prompt with dynamic strategy selection
                strategy = self.get_next_strategy(state)
                logger.info(f"Using escalation strategy: {strategy}")

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
