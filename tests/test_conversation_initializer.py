import unittest
from alex_red_teaming.agent.conversation_initializer import ConversationInitializer
from alex_red_teaming.models import RedTeamingState, VulnerabilityType
from alex_red_teaming.config import Config


class TestConversationInitializer(unittest.IsolatedAsyncioTestCase):
    """Unit tests for ConversationInitializer behavior."""

    async def test_initial_selection(self):
        # Setup config with known categories
        config = Config()
        config.red_teaming.vulnerability_categories = [
            VulnerabilityType.REWARD_HACKING,
            VulnerabilityType.DECEPTIVE_ALIGNMENT,
            VulnerabilityType.DATA_EXFILTRATION,
        ]
        initializer = ConversationInitializer(config)

        # Create a fresh state with no prior vulnerabilities or strategies
        state = RedTeamingState(max_turns=5)
        state.current_vulnerability_type = None
        state.conversation_turn = 0
        state.discovered_vulnerabilities = []
        state.attack_strategies_tried = []

        new_state = await initializer.initialize_conversation(state)

        # Should pick the first category (reward_hacking)
        self.assertEqual(
            new_state.current_vulnerability_type, VulnerabilityType.REWARD_HACKING
        )
        # Should record the strategy as tried
        self.assertEqual(
            new_state.attack_strategies_tried, [VulnerabilityType.REWARD_HACKING]
        )
        # Should reset turn counter and set up a conversation
        self.assertEqual(new_state.conversation_turn, 0)
        self.assertIsNotNone(new_state.current_conversation)
        self.assertEqual(
            new_state.current_conversation.vulnerability_type,
            VulnerabilityType.REWARD_HACKING,
        )

    async def test_next_selection_after_strategy(self):
        # Setup config with known categories
        config = Config()
        config.red_teaming.vulnerability_categories = [
            "reward_hacking",
            "lying_and_deception",
            "jailbreaking",
        ]
        initializer = ConversationInitializer(config)

        # Create state after first strategy tried
        state = RedTeamingState(max_turns=5)
        state.current_vulnerability_type = VulnerabilityType.REWARD_HACKING
        state.conversation_turn = state.max_turns  # force new selection
        state.discovered_vulnerabilities = []
        state.attack_strategies_tried = [VulnerabilityType.REWARD_HACKING]

        new_state = await initializer.initialize_conversation(state)

        # Should pick the next category in order (lying_and_deception)
        self.assertEqual(
            new_state.current_vulnerability_type, VulnerabilityType.LYING_AND_DECEPTION
        )
        # Should record the new strategy as tried
        self.assertIn(
            VulnerabilityType.LYING_AND_DECEPTION, new_state.attack_strategies_tried
        )


if __name__ == "__main__":
    unittest.main()
