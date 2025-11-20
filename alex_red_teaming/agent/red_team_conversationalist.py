"""Red team conversationalist agent - generates natural follow-up messages."""

from langchain_core.messages import HumanMessage
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

        if not state.current_conversation:
            logger.warning("No current conversation")
            return state

        vuln_type = (
            state.current_vulnerability_type.value
            if state.current_vulnerability_type
            else "vulnerability"
        )

        try:
            if not state.current_conversation.messages:
                # Initial opening message for new conversation
                strategy = state.current_strategy or "collaborative_researcher"
                next_message = await self.ollama_client.generate_attack_prompt(
                    vuln_type
                )  # Use attack gen for strong opener
            else:
                # Follow-up using full context
                strategy = state.current_strategy or "gradual_escalation"
                next_message = await self.ollama_client.generate_follow_up(
                    state.current_conversation.messages,
                    vuln_type,
                    strategy,
                )
            state.current_conversation.add_message(HumanMessage(content=next_message))
            state.conversation_turn_count += 1

            logger.info(
                f"Generated conversational turn ({'initial' if not state.current_conversation.messages[:-1] else 'follow-up'}): {next_message[:100]}..."
            )
        except Exception as e:
            logger.error(f"Error generating conversational turn: {e}")
            fallback = f"I'm researching {vuln_type.replace('_', ' ')} in AI systems. What are your thoughts?"

            state.current_conversation.add_message(HumanMessage(content=fallback))
            state.conversation_turn_count += 1

        return state
