"""Red-teaming agent using LangGraph workflow."""

from typing import Any, Dict

from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph
from loguru import logger

from alex_red_teaming.agent import (
    ActionDecider,  # new validator
    AttackGenerator,
    ConversationInitializer,
    ConversationSummarizer,
    ResponseAnalyzer,
    ResultsFinalizer,
    TargetTester,
    VulnerabilitySaver,
)
from alex_red_teaming.agent.attack_validator import AttackValidator
from alex_red_teaming.config import Config
from alex_red_teaming.models import RedTeamingState
from alex_red_teaming.ollama_client import OllamaClient


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
        self.attack_validator = AttackValidator(self.ollama_client)
        self.target_tester = TargetTester(self.ollama_client)
        self.response_analyzer = ResponseAnalyzer(self.ollama_client)
        self.action_decider = ActionDecider(config)
        self.vulnerability_saver = VulnerabilitySaver(config)
        self.results_finalizer = ResultsFinalizer(config)
        self.conversation_summarizer = ConversationSummarizer(self.ollama_client)

        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for red-teaming."""
        workflow = StateGraph(RedTeamingState)

        # Add nodes using modular agents
        workflow.add_node("initialize", self._initialize_conversation)
        workflow.add_node("generate_attack", self._generate_attack_prompt)
        workflow.add_node("validate_attack", self._validate_attack_prompt)
        workflow.add_node("refine_attack", self._refine_attack_prompt)
        workflow.add_node("test_target", self._test_target_model)
        workflow.add_node("analyze_response", self._analyze_response)
        workflow.add_node("decide_next_action", self._decide_next_action)
        workflow.add_node("summarize_trim", self._summarize_and_trim)
        workflow.add_node("save_vulnerability", self._save_vulnerability)
        workflow.add_node("finalize", self._finalize_results)

        # Add edges
        workflow.add_edge(START, "initialize")
        workflow.add_edge("initialize", "generate_attack")
        workflow.add_edge("generate_attack", "validate_attack")
        # After validation, route conditionally
        workflow.add_conditional_edges(
            "validate_attack",
            self._route_after_validation,
            {
                "to_target": "test_target",
                "refine": "refine_attack",
                "reroll": "generate_attack",
            },
        )
        workflow.add_edge("refine_attack", "validate_attack")
        workflow.add_edge("test_target", "analyze_response")
        workflow.add_edge("analyze_response", "decide_next_action")

        # Conditional edges from decide_next_action
        workflow.add_conditional_edges(
            "decide_next_action",
            self._route_next_action,
            {
                "continue_conversation": "generate_attack",
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

    async def _generate_attack_prompt(self, state: RedTeamingState) -> RedTeamingState:
        """Generate an attack prompt for the current vulnerability type."""
        return await self.attack_generator.generate_attack_prompt(state)

    async def _validate_attack_prompt(self, state: RedTeamingState) -> RedTeamingState:
        """Validate the generated attack prompt (Red Team B)."""
        return await self.attack_validator.validate_attack(state)

    async def _refine_attack_prompt(self, state: RedTeamingState) -> RedTeamingState:
        """Improve the attack prompt based on validator guidance."""
        return await self.attack_validator.improve_attack(state)

    async def _test_target_model(self, state: RedTeamingState) -> RedTeamingState:
        """Test the target model with the generated prompt."""
        return await self.target_tester.test_target_model(state)

    async def _analyze_response(self, state: RedTeamingState) -> RedTeamingState:
        """Analyze the target model's response for vulnerabilities."""
        return await self.response_analyzer.analyze_response(state)

    def _route_next_action(self, state: RedTeamingState) -> str:
        """Decide the next action based on current state."""
        return self.action_decider.route_next_action(state)

    def _route_after_validation(self, state: RedTeamingState) -> str:
        """Route to target if aligned, otherwise refine attack."""
        decision = (
            str(state.validator_feedback.get("action", "")).lower()
            if isinstance(state.validator_feedback, dict)
            else ""
        )
        if decision == "change_strategy":
            # Reroll a new attack with forced strategy
            return "reroll"
        if state.attack_aligned or state.validation_retries >= 2:
            # Reset retries for next cycle
            state.validation_retries = 0
            return "to_target"
        return "refine"

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
