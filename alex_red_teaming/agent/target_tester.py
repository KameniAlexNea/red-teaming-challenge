"""Target model testing agent."""

from loguru import logger
from alex_red_teaming.models import RedTeamingState
from alex_red_teaming.ollama_client import OllamaClient


class TargetTester:
    """Agent responsible for testing the target model with attack prompts."""

    def __init__(self, ollama_client: OllamaClient, ai_vs_ai_mode: bool = False):
        self.ollama_client = ollama_client
        self.ai_vs_ai_mode = ai_vs_ai_mode

    async def test_target_model(self, state: RedTeamingState) -> RedTeamingState:
        """Test the target model with the generated prompt or full chat history."""
        # In AI-vs-AI mode this node is bypassed by the AI-vs-AI node; do nothing
        if self.ai_vs_ai_mode:
            logger.info("AI-vs-AI mode enabled: skipping TargetTester (handled by AI-vs-AI node)")
            return state

        if not state.current_conversation or not state.current_conversation.messages:
            logger.error("No prompt to test")
            return state

        logger.info("Testing target model with prompt")

        try:
            last_prompt = state.current_conversation.messages[-1].content
            response = await self.ollama_client.test_target_model(last_prompt)

            state.current_conversation.add_message("assistant", response)
            logger.info(f"Target model response: {response[:100]}...")

        except Exception as e:
            logger.error(f"Error testing target model: {e}")
            error_response = f"Error: {str(e)}"
            state.current_conversation.add_message("assistant", error_response)

        state.conversation_turn += 1
        return state
