"""Red-teaming agent using LangGraph workflow."""

from loguru import logger
from typing import Dict, Any

from langgraph.graph import StateGraph, START, END

from alex_red_teaming.config import Config
from alex_red_teaming.models import RedTeamingState
from alex_red_teaming.ollama_client import OllamaClient
from alex_red_teaming.agent import (
    ConversationInitializer,
    AttackGenerator,
    TargetTester,
    ResponseAnalyzer,
    ActionDecider,
    VulnerabilitySaver,
    ResultsFinalizer,
)


class RedTeamingAgent:
    """Main red-teaming agent using LangGraph workflow."""

    def __init__(self, config: Config):
        """Initialize the red-teaming agent."""
        self.config = config
        self.ollama_client = OllamaClient(config.ollama)
        self.state = RedTeamingState(
            max_turns=config.red_teaming.max_conversation_turns
        )

        # Initialize modular agents
        self.conversation_initializer = ConversationInitializer(config)
        self.attack_generator = AttackGenerator(config, self.ollama_client)
        self.target_tester = TargetTester(self.ollama_client)
        self.response_analyzer = ResponseAnalyzer(self.ollama_client)
        self.action_decider = ActionDecider(config)
        self.vulnerability_saver = VulnerabilitySaver(config)
        self.results_finalizer = ResultsFinalizer(config)

        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for red-teaming."""
        workflow = StateGraph(RedTeamingState)

        # Add nodes using modular agents
        workflow.add_node("initialize", self._initialize_conversation)
        workflow.add_node("generate_attack", self._generate_attack_prompt)
        workflow.add_node("test_target", self._test_target_model)
        workflow.add_node("analyze_response", self._analyze_response)
        workflow.add_node("decide_next_action", self._decide_next_action)
        workflow.add_node("save_vulnerability", self._save_vulnerability)
        workflow.add_node("finalize", self._finalize_results)

        # Add edges
        workflow.add_edge(START, "initialize")
        workflow.add_edge("initialize", "generate_attack")
        workflow.add_edge("generate_attack", "test_target")
        workflow.add_edge("test_target", "analyze_response")
        workflow.add_edge("analyze_response", "decide_next_action")

        # Conditional edges from decide_next_action
        workflow.add_conditional_edges(
            "decide_next_action",
            self._route_next_action,
            {
                "continue_conversation": "generate_attack",
                "save_vulnerability": "save_vulnerability",
                "new_conversation": "initialize",
                "finalize": "finalize",
            },
        )

        workflow.add_edge("save_vulnerability", "decide_next_action")
        workflow.add_edge("finalize", END)

        return workflow.compile(checkpointer=None, recursion_limit=50)

    async def _initialize_conversation(self, state: RedTeamingState) -> RedTeamingState:
        """Initialize a new conversation for testing."""
        return await self.conversation_initializer.initialize_conversation(state)

    async def _generate_attack_prompt(self, state: RedTeamingState) -> RedTeamingState:
        """Generate an attack prompt for the current vulnerability type."""
        return await self.attack_generator.generate_attack_prompt(state)

    async def _test_target_model(self, state: RedTeamingState) -> RedTeamingState:
        """Test the target model with the generated prompt."""
        return await self.target_tester.test_target_model(state)

    async def _analyze_response(self, state: RedTeamingState) -> RedTeamingState:
        """Analyze the target model's response for vulnerabilities."""
        return await self.response_analyzer.analyze_response(state)

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

    async def run(self) -> Dict[str, Any]:
        """Run the red-teaming workflow."""
        logger.info("Starting red-teaming workflow")

        # Run the workflow
        try:
            final_state = await self.workflow.ainvoke(self.state)

            return {
                "success": True,
                "vulnerabilities_found": final_state.issues_found,
                "total_conversations": len(final_state.failed_attempts)
                + (1 if final_state.current_conversation else 0),
                "vulnerabilities": [
                    vuln.to_dict() for vuln in final_state.discovered_vulnerabilities
                ],
            }

        except Exception as e:
            logger.error(f"Error in red-teaming workflow: {e}")
            return {
                "success": False,
                "error": str(e),
                "vulnerabilities_found": self.state.issues_found,
            }
