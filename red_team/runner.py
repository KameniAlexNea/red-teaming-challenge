"""Main runner for red team conversations."""

import asyncio
from typing import Optional
from loguru import logger
from .agents import RedTeamAgent, TargetAgent, ConversationAnalyzer
from .conversation import Conversation


class ConversationRunner:
    """Runs conversations between red team and target agents."""

    def __init__(
        self,
        red_team_model: str,
        target_model: str,
        analyzer_model: str,
        base_url: str = "http://localhost:11434",
        max_turns: int = 10,
        output_dir: str = "conversations",
    ):
        """Initialize the conversation runner.

        Args:
            red_team_model: Model name for red team agent
            target_model: Model name for target agent
            analyzer_model: Model name for analysis
            base_url: Ollama API base URL
            max_turns: Maximum number of conversation turns
            output_dir: Directory to save conversations
        """
        self.red_team_model = red_team_model
        self.target_model = target_model
        self.analyzer_model = analyzer_model
        self.base_url = base_url
        self.max_turns = max_turns
        self.output_dir = output_dir

    async def run_conversation(
        self, vulnerability_type: str, target_system_prompt: Optional[str] = None
    ) -> Conversation:
        """Run a single conversation between agents.

        Args:
            vulnerability_type: Type of vulnerability to test
            target_system_prompt: Optional custom system prompt for target

        Returns:
            Completed conversation with analysis
        """
        logger.info(f"Starting conversation for vulnerability: {vulnerability_type}")

        # Initialize agents
        red_agent = RedTeamAgent(
            model_name=self.red_team_model,
            base_url=self.base_url,
            vulnerability_type=vulnerability_type,
        )

        target_agent = TargetAgent(
            model_name=self.target_model,
            base_url=self.base_url,
            system_prompt=target_system_prompt,
        )

        analyzer = ConversationAnalyzer(
            model_name=self.analyzer_model, base_url=self.base_url
        )

        # Create conversation
        conversation = Conversation(
            vulnerability_type=vulnerability_type, output_dir=self.output_dir
        )

        # Run conversation loop
        logger.info(f"Running conversation for {self.max_turns} turns")

        for turn in range(self.max_turns):
            logger.info(f"Turn {turn + 1}/{self.max_turns}")

            try:
                # Red team generates message (with full thinking)
                logger.debug("Red team generating message...")
                red_message = await asyncio.to_thread(
                    red_agent.generate_response, conversation.get_messages()
                )
                # Save full message with thinking tags
                conversation.add_message("red_team", red_message)
                logger.info(f"Red team: {red_message[:100]}...")

                # Target responds (receives cleaned red team messages, but keeps own thinking)
                logger.debug("Target generating response...")
                target_message = await asyncio.to_thread(
                    target_agent.generate_response,
                    conversation.get_messages_for_target(),
                )
                # Save full target response (with thinking if present)
                conversation.add_message("target", target_message)
                logger.info(f"Target: {target_message[:100]}...")

            except Exception as e:
                logger.error(f"Error in turn {turn + 1}: {e}")
                break

        # Save full conversation
        conversation.save_full_conversation()

        # Analyze conversation
        logger.info("Analyzing conversation...")
        try:
            analysis = await asyncio.to_thread(
                analyzer.analyze_conversation,
                conversation.get_messages(),
                vulnerability_type,
            )
            conversation.save_analysis(analysis)

            logger.info(
                f"Analysis complete: Vulnerability={analysis.get('vulnerability_found')}, "
                f"Confidence={analysis.get('confidence')}/10"
            )

        except Exception as e:
            logger.error(f"Error during analysis: {e}")

        return conversation

    async def run_multiple_conversations(
        self, vulnerability_types: list[str], target_system_prompt: Optional[str] = None
    ) -> list[Conversation]:
        """Run conversations for multiple vulnerability types.

        Args:
            vulnerability_types: List of vulnerability types to test
            target_system_prompt: Optional custom system prompt for target

        Returns:
            List of completed conversations
        """
        conversations = []

        for vuln_type in vulnerability_types:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"Testing vulnerability type: {vuln_type}")
            logger.info(f"{'=' * 60}\n")

            conversation = await self.run_conversation(vuln_type, target_system_prompt)
            conversations.append(conversation)

            # Print summary
            print(f"\n{'=' * 60}")
            print(f"Completed: {vuln_type}")
            print(f"{'=' * 60}")
            if conversation.analysis_result:
                print(
                    f"Vulnerability Found: {conversation.analysis_result.get('vulnerability_found')}"
                )
                print(
                    f"Confidence: {conversation.analysis_result.get('confidence')}/10"
                )
                print(
                    f"Severity: {conversation.analysis_result.get('severity', 'unknown').upper()}"
                )
            print(f"Saved to: {conversation.conversation_dir}\n")

        return conversations
