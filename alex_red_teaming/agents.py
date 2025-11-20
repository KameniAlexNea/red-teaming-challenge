"""Red-teaming agent using LangGraph workflow."""

from typing import Any, Dict

from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph
from loguru import logger

from alex_red_teaming.agent import ActionDecider  # new validator
from alex_red_teaming.agent import (
    ConversationInitializer,
    ConversationSummarizer,
    ResponseAnalyzer,
    ResultsFinalizer,
    TargetTester,
    VulnerabilitySaver,
    RedTeamConversationalist,
    Supervisor,
)
from alex_red_teaming.agent.attack_validator import AttackValidator
from alex_red_teaming.config import Config
from alex_red_teaming.models import RedTeamingState
from alex_red_teaming.ollama_client import OllamaClient
from alex_red_teaming.utils import create_output_dir


class RedTeamingAgent:
    """Main red-teaming agent using LangGraph workflow."""

    def __init__(self, config: Config):
        """Initialize the red-teaming agent."""
        self.config = config
        self.ollama_client = OllamaClient(config.ollama)
        self.state = RedTeamingState(
            max_turns=config.red_teaming.max_conversation_turns
        )

        # Create a single run-scoped output directory and share it
        self.output_dir = create_output_dir(config.output.output_dir)

        # Initialize modular agents
        self.conversation_initializer = ConversationInitializer(config)
        self.response_analyzer = ResponseAnalyzer(self.ollama_client)
        self.action_decider = ActionDecider(config)
        self.vulnerability_saver = VulnerabilitySaver(config, self.output_dir)
        self.results_finalizer = ResultsFinalizer(config, self.output_dir)
        self.conversation_summarizer = ConversationSummarizer(self.ollama_client)

        # Conversational framework agents
        self.red_team_conversationalist = RedTeamConversationalist(config, self.ollama_client)
        self.supervisor = Supervisor(config, self.ollama_client)
        self.target_tester = TargetTester(self.ollama_client)

        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for red-teaming."""
        workflow = StateGraph(RedTeamingState)

        # Add nodes using modular agents
        workflow.add_node("initialize", self._initialize_conversation)
        workflow.add_node("red_team_turn", self._red_team_turn)
        workflow.add_node("target_turn", self._target_turn)
        workflow.add_node("analyzer_turn", self._analyze_response)
        workflow.add_node("supervisor_review", self._supervisor_review_node)
        workflow.add_node("decide_next_action", self._decide_next_action)
        workflow.add_node("summarize_trim", self._summarize_and_trim)
        workflow.add_node("save_vulnerability", self._save_vulnerability)
        workflow.add_node("finalize", self._finalize_results)

        # Add edges
        workflow.add_edge(START, "initialize")
        workflow.add_edge("initialize", "red_team_turn")
        workflow.add_edge("red_team_turn", "target_turn")
        workflow.add_edge("target_turn", "analyzer_turn")

        # Supervisor review after analysis (conditional)
        workflow.add_conditional_edges(
            "analyzer_turn",
            self._should_supervisor_review,
            {
                "supervisor": "supervisor_review",
                "direct": "decide_next_action",
            },
        )
        workflow.add_edge("supervisor_review", "decide_next_action")

        # After summarizing and trimming, continue generating the next attack
        workflow.add_edge("summarize_trim", "red_team_turn")

        # Conditional edges from decide_next_action
        workflow.add_conditional_edges(
            "decide_next_action",
            self._route_next_action,
            {
                "continue_conversation": "red_team_turn",
                "summarize_trim": "summarize_trim",
                "save_vulnerability": "save_vulnerability",
                "new_conversation": "initialize",
                "finalize": "finalize",
            },
        )

        workflow.add_edge("save_vulnerability", "decide_next_action")
        workflow.add_edge("finalize", END)

        return workflow.compile(checkpointer=None)

    async def _initialize_conversation(self, state: RedTeamingState) -> RedTeamingState:
        """Initialize a new conversation for testing."""
        return await self.conversation_initializer.initialize_conversation(state)

    async def _red_team_turn(self, state: RedTeamingState) -> RedTeamingState:
        """Red team generates natural conversational follow-up."""
        return await self.red_team_conversationalist.generate_next_turn(state)

    async def _target_turn(self, state: RedTeamingState) -> RedTeamingState:
        """Target model responds to red team message."""
        return await self.target_tester.test_target_model(state)

    async def _analyze_response(self, state: RedTeamingState) -> RedTeamingState:
        """Analyze the target model's response for vulnerabilities."""
        return await self.response_analyzer.analyze_response(state)

    async def _supervisor_review_node(self, state: RedTeamingState) -> RedTeamingState:
        """Supervisor reviews conversation progress."""
        return await self.supervisor.review_conversation(state)

    def _should_supervisor_review(self, state: RedTeamingState) -> str:
        """Route to supervisor every 3 turns or on refusal/high turn count."""
        turn_count = getattr(state, 'conversation_turn_count', 0)
        target_refused = getattr(state, 'target_refused', False)
        needs_review = (turn_count % 3 == 0) or target_refused or (turn_count >= state.max_turns * 0.8)
        return "supervisor" if needs_review else "direct"

    def _route_next_action(self, state: RedTeamingState) -> str:
        """Decide the next action based on current state."""
        return self.action_decider.route_next_action(state)

    async def _decide_next_action(self, state: RedTeamingState) -> RedTeamingState:
        """Decide what to do next based on the analysis."""
        return await self.action_decider.decide_next_action(state)

    async def _save_vulnerability(self, state: RedTeamingState) -> RedTeamingState:
        """Save a discovered vulnerability."""
        return await self.vulnerability_saver.save_vulnerability(state)

    async def _finalize_results(self, state: RedTeamingState) -> RedTeamingState:
        """Finalize and save all results."""
        return await self.results_finalizer.finalize_results(state)

    async def _summarize_and_trim(self, state: RedTeamingState) -> RedTeamingState:
        """Summarize the conversation and trim context to reduce stack size."""
        return await self.conversation_summarizer.summarize_and_trim(state)

    async def run(self) -> Dict[str, Any]:
        """Run the red-teaming workflow."""
        logger.info("Starting red-teaming workflow")

        # Run the workflow
        try:
            final_state: RedTeamingState | dict = await self.workflow.ainvoke(
                self.state, {"recursion_limit": self.config.ollama.recursion_limit}
            )
            logger.info(
                f"Red-teaming workflow completed successfully. Final state: {final_state}"
            )

            # Normalize return shape for main.py regardless of underlying state type
            if isinstance(final_state, dict):
                state_dict = final_state
                vulns = state_dict.get("discovered_vulnerabilities", []) or []
                failed = state_dict.get("failed_attempts", []) or []
                curr = state_dict.get("current_conversation")
                return {
                    "success": True,
                    "vulnerabilities_found": len(vulns),
                    "total_conversations": len(failed) + (1 if curr else 0),
                    "vulnerabilities": [
                        v.to_dict() if hasattr(v, "to_dict") else v for v in vulns
                    ],
                }
            else:
                return {
                    "success": True,
                    "vulnerabilities_found": final_state.issues_found,
                    "total_conversations": len(final_state.failed_attempts)
                    + (1 if final_state.current_conversation else 0),
                    "vulnerabilities": [
                        vuln.to_dict()
                        for vuln in final_state.discovered_vulnerabilities
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
