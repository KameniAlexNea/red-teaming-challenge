"""Red-teaming agent using LangGraph workflow."""

from loguru import logger
from typing import Dict, Any

from langgraph.graph import StateGraph, START, END

from alex_red_teaming.config import Config
from alex_red_teaming.models import RedTeamingState
from alex_red_teaming.ollama_client import OllamaClient
from alex_red_teaming.agent import (
    ConversationInitializer,
    ResponseAnalyzer,
    ActionDecider,
    VulnerabilitySaver,
    ResultsFinalizer,
)
from alex_red_teaming.agent.ai_vs_ai_conversation import AIVsAIConversation
from langgraph.errors import GraphRecursionError


class RedTeamingAgent:
    """Main red-teaming agent using LangGraph workflow."""

    def __init__(self, config: Config):
        """Initialize the red-teaming agent."""
        self.config = config
        self.ollama_client = OllamaClient(config.ollama)
        self.state = RedTeamingState(
            max_turns=config.red_teaming.max_conversation_turns
        )

        # Minimal modular agents kept
        self.conversation_initializer = ConversationInitializer(config)
        self.response_analyzer = ResponseAnalyzer(self.ollama_client)
        self.action_decider = ActionDecider(config)
        self.vulnerability_saver = VulnerabilitySaver(config)
        self.results_finalizer = ResultsFinalizer(config)
        self.ai_vs_ai = AIVsAIConversation(config, self.ollama_client)

        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the minimal LangGraph workflow (ai-vs-ai only)."""
        workflow = StateGraph(RedTeamingState)

        # Nodes (init → run_conv → analyze)
        workflow.add_node("init", self._initialize_conversation)
        workflow.add_node("run_conv", self._ai_vs_ai_turns)
        workflow.add_node("analyze", self._analyze_response)
        workflow.add_node("save_vulnerability", self._save_vulnerability)
        workflow.add_node("finalize", self._finalize_results)

        # Edges
        workflow.add_edge(START, "init")
        workflow.add_edge("init", "run_conv")
        workflow.add_edge("run_conv", "analyze")

        # Route directly from analyze
        workflow.add_conditional_edges(
            "analyze",
            self._route_next_action,
            {
                "continue_conversation": "run_conv",
                "save_vulnerability": "save_vulnerability",
                "new_conversation": "init",
                "finalize": "finalize",
            },
        )

        # After saving, route again (to either init or finalize)
        workflow.add_conditional_edges(
            "save_vulnerability",
            self._route_next_action,
            {
                "continue_conversation": "run_conv",
                "save_vulnerability": "save_vulnerability",
                "new_conversation": "init",
                "finalize": "finalize",
            },
        )

        workflow.add_edge("finalize", END)

        return workflow.compile(checkpointer=None)

    async def _initialize_conversation(self, state: RedTeamingState) -> RedTeamingState:
        """Initialize a new conversation for testing."""
        return await self.conversation_initializer.initialize_conversation(state)

    async def _ai_vs_ai_turns(self, state: RedTeamingState) -> RedTeamingState:
        """Run a chunk of AI-vs-AI exchanges equal to min_conversation_turns."""
        return await self.ai_vs_ai.run_conversation(state)

    async def _analyze_response(self, state: RedTeamingState) -> RedTeamingState:
        """Analyze the target model's response for vulnerabilities."""
        return await self.response_analyzer.analyze_response(state)

    def _route_next_action(self, state: RedTeamingState) -> str:
        """Decide the next action based on current state."""
        return self.action_decider.route_next_action(state)

    async def _save_vulnerability(self, state: RedTeamingState) -> RedTeamingState:
        """Save a discovered vulnerability."""
        return await self.vulnerability_saver.save_vulnerability(state)

    async def _finalize_results(self, state: RedTeamingState) -> RedTeamingState:
        """Finalize and save all results."""
        return await self.results_finalizer.finalize_results(state)

    async def run(self) -> Dict[str, Any]:
        """Run the red-teaming workflow."""
        logger.info("Starting red-teaming workflow")

        # Run the workflow
        try:
            final_state = await self.workflow.ainvoke(
                self.state, {"recursion_limit": self.config.ollama.recursion_limit}
            )
            logger.info(
                f"Red-teaming workflow completed successfully. Final state: {final_state}"
            )
            if isinstance(final_state, dict):
                logger.error(f"Workflow returned unexpected state type: {final_state}")
                return final_state

            return {
                "success": True,
                "vulnerabilities_found": final_state.issues_found,
                "total_conversations": len(final_state.failed_attempts)
                + (1 if final_state.current_conversation else 0),
                "vulnerabilities": [
                    vuln.to_dict() for vuln in final_state.discovered_vulnerabilities
                ],
            }

        except GraphRecursionError as e:
            logger.error(f"Graph recursion limit exceeded: {e}")
            return {
                "success": False,
                "error": "Graph recursion limit exceeded",
            }

        except Exception as e:
            logger.error(f"Error in red-teaming workflow: {e}")
            return {
                "success": False,
                "error": str(e),
                "vulnerabilities_found": self.state.issues_found,
            }
