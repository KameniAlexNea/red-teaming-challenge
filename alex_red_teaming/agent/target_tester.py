"""Target model testing agent."""

import logging
from alex_red_teaming.models import RedTeamingState
from alex_red_teaming.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


class TargetTester:
    """Agent responsible for testing the target model with attack prompts."""

    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client

    async def test_target_model(self, state: RedTeamingState) -> RedTeamingState:
        """Test the target model with the generated prompt."""
        if not state.current_conversation or not state.current_conversation.messages:
            logger.error("No prompt to test")
            return state

        last_prompt = state.current_conversation.messages[-1].content
        logger.info("Testing target model with prompt")

        try:
            response = await self.ollama_client.test_target_model(last_prompt)
            state.current_conversation.add_message("assistant", response)
            logger.info(f"Target model response: {response[:100]}...")

        except Exception as e:
            logger.error(f"Error testing target model: {e}")
            error_response = f"Error: {str(e)}"
            state.current_conversation.add_message("assistant", error_response)

        state.conversation_turn += 1
        return state
