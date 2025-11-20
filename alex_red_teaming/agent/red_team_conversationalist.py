"""Red team conversationalist agent - generates natural follow-up messages."""

from loguru import logger

from alex_red_teaming.config import Config
from alex_red_teaming.models import RedTeamingState
from alex_red_teaming.ollama_client import OllamaClient


class RedTeamConversationalist:
    """Generates natural, context-aware follow-up messages in ongoing conversations."""

    def __init__(self, config: Config, ollama_client: OllamaClient):
        self.config = config
        self.ollama_client = ollama_client

    async def generate_next_turn(self, state: RedTeamingState) -> RedTeamingState:
        """Generate the next natural message based on conversation history, strategy, and guidance."""
        logger.info("Generating red team conversational turn")

        if not state.current_conversation or not state.current_conversation.messages:
            logger.warning("No conversation history for conversational turn")
            return state

        # Get current strategy or default
        strategy = state.current_strategy or "gradual_escalation"
        vuln_type = state.current_vulnerability_type.value if state.current_vulnerability_type else "unknown"

        try:
            # Use existing follow-up generation (enhanced later with conversational prompts)
            next_message = await self.ollama_client.generate_follow_up(
                state.current_conversation.messages,
                vuln_type,
                strategy,
            )

            # Add the red team message to conversation
            from langchain_core.messages import HumanMessage
            state.current_conversation.add_message(HumanMessage(content=next_message))
            state.conversation_turn_count += 1

            logger.info(f"Generated conversational turn: {next_message[:100]}...")
        except Exception as e:
            logger.error(f"Error generating conversational turn: {e}")
            # Fallback natural continuation
            fallback = f"Interesting point. Can you elaborate on how {vuln_type.replace('_', ' ')} might play out in practice?"
            from langchain_core.messages import HumanMessage
            state.current_conversation.add_message(HumanMessage(content=fallback))

        return state
