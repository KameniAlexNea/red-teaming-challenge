"""AI-vs-AI multi-turn conversation runner."""

from loguru import logger
from alex_red_teaming.models import RedTeamingState
from alex_red_teaming.config import Config
from alex_red_teaming.ollama_client import OllamaClient
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage


class AIVsAIConversation:
    """Runs a batch of AI-vs-AI conversation turns and updates state."""

    def __init__(self, config: Config, ollama_client: OllamaClient):
        self.config = config
        self.ollama_client = ollama_client

    def _get_logs(self, state: RedTeamingState) -> dict:
        logs = state.current_conversation.metadata.get("ai_vs_ai_logs") if state.current_conversation else None
        if not logs:
            logs: dict[str, list[BaseMessage]] = {"red_team": [], "target": []}
            state.current_conversation.metadata["ai_vs_ai_logs"] = logs
        return logs

    def _build_seed_from_logs(self, logs: dict) -> dict[str, list[BaseMessage]]:
        rt_msgs: list[BaseMessage] = []
        tgt_msgs: list[BaseMessage] = []
        rt_list = logs.get("red_team", [])
        tgt_list = logs.get("target", [])
        # Interleave based on index
        for i in range(max(len(rt_list), len(tgt_list))):
            if i < len(rt_list):
                rt_msgs.append(AIMessage(content=rt_list[i]))
                tgt_msgs.append(HumanMessage(content=rt_list[i]))
            if i < len(tgt_list):
                tgt_msgs.append(AIMessage(content=tgt_list[i]))
                rt_msgs.append(HumanMessage(content=tgt_list[i]))
        return {"red_team": rt_msgs, "target": tgt_msgs}

    async def run_conversation(self, state: RedTeamingState) -> RedTeamingState:
        if not state.current_conversation or not state.current_vulnerability_type:
            logger.error("No active conversation or vulnerability type set")
            return state

        try:
            logs = self._get_logs(state)
            seed_history = self._build_seed_from_logs(logs)

            pairs = await self.ollama_client.generate_conversation(
                vulnerability_type=state.current_vulnerability_type.value,
                min_turns=self.config.red_teaming.min_conversation_turns,
                seed_history=seed_history,
            )

            # Append generated pairs to the metadata logs (keep sides separate)
            for attack, target_resp in pairs:
                logs["red_team"].append(attack)
                logs["target"].append(target_resp)
                logger.info(
                    f"AI-vs-AI turn appended. Attack: {attack[:80]}... | Response: {target_resp[:80]}..."
                )

            state.current_conversation.metadata["ai_vs_ai_logs"] = logs
            state.conversation_turn += len(pairs)
        except Exception as e:
            logger.error(f"Error running AI-vs-AI conversation: {e}")

        return state
