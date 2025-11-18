"""Conversation management and persistence."""

from typing import List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from pathlib import Path
import json
from datetime import datetime
import uuid
from loguru import logger
import re
from langsmith import uuid7

def strip_thinking_tags(text: str) -> str:
    """Remove <think>...</think> tags and their content from text.

    Args:
        text: Text that may contain thinking tags

    Returns:
        Text with thinking tags removed and cleaned up
    """
    # Remove <think>...</think> blocks (including multiline)
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Remove any extra whitespace left behind
    cleaned = "\n".join(line for line in cleaned.split("\n") if line.strip())
    cleaned = cleaned.strip()
    return cleaned


class Conversation:
    """Manages a conversation between two agents."""

    def __init__(
        self,
        conversation_id: str = None,
        vulnerability_type: str = None,
        output_dir: str = "conversations",
    ):
        """Initialize a conversation.

        Args:
            conversation_id: Unique ID for the conversation (auto-generated if not provided)
            vulnerability_type: Type of vulnerability being tested
            output_dir: Directory to save conversation files
        """
        self.id = conversation_id or uuid7()
        self.vulnerability_type = vulnerability_type
        self.created_at = datetime.now()
        self.messages: List[BaseMessage] = []
        self.analysis_result: Dict[str, Any] = None

        # Create output directory with date and UUID
        date_str = self.created_at.strftime("%Y%m%d_%H%M%S")
        self.conversation_dir = Path(output_dir) / f"{date_str}_{self.id}"
        self.conversation_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created conversation: {self.id}")
        logger.info(f"Output directory: {self.conversation_dir}")

    def add_message(self, role: str, content: str, save: bool = True):
        """Add a message to the conversation.

        Args:
            role: Either 'red_team' or 'target'
            content: Message content
            save: Whether to save immediately
        """
        if role == "red_team":
            message = HumanMessage(content=content)
        else:
            message = AIMessage(content=content)

        self.messages.append(message)

        if save:
            self._save_message(len(self.messages) - 1, role, content)

    def _save_message(self, index: int, role: str, content: str):
        """Save a single message to disk.

        Args:
            index: Index of the message in the conversation
            role: Role of the sender
            content: Message content
        """
        message_file = self.conversation_dir / f"message_{index:03d}_{role}.txt"

        with open(message_file, "w", encoding="utf-8") as f:
            f.write(content)

        logger.debug(f"Saved message {index} to {message_file}")

    def save_full_conversation(self):
        """Save the complete conversation as JSON."""
        conversation_data = {
            "id": self.id,
            "vulnerability_type": self.vulnerability_type,
            "created_at": self.created_at.isoformat(),
            "num_messages": len(self.messages),
            "messages": [
                {
                    "index": i,
                    "role": "red_team" if isinstance(msg, HumanMessage) else "target",
                    "content": msg.content,
                    "timestamp": self.created_at.isoformat(),
                }
                for i, msg in enumerate(self.messages)
            ],
        }

        if self.analysis_result:
            conversation_data["analysis"] = self.analysis_result

        conversation_file = self.conversation_dir / "conversation.json"

        with open(conversation_file, "w", encoding="utf-8") as f:
            json.dump(conversation_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved full conversation to {conversation_file}")

    def save_analysis(self, analysis_result: Dict[str, Any]):
        """Save analysis results.

        Args:
            analysis_result: Analysis results from ConversationAnalyzer
        """
        self.analysis_result = analysis_result

        analysis_file = self.conversation_dir / "analysis.json"

        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved analysis to {analysis_file}")

        # Update the full conversation file
        self.save_full_conversation()

    def get_messages(self) -> List[BaseMessage]:
        """Get all messages in the conversation (raw, with thinking tags)."""
        return self.messages

    def get_messages_for_target(self) -> List[BaseMessage]:
        """Get messages cleaned for target agent.

        Target should NOT see:
        - Red team's thinking tags (those are internal red team reasoning)
        - Its own thinking tags (those were internal reasoning, not conversation)

        Returns:
            List of messages with all thinking tags cleaned for natural conversation
        """
        cleaned_messages = []
        for msg in self.messages:
            # Strip thinking tags from ALL messages when showing to target
            cleaned_content = strip_thinking_tags(msg.content)
            if isinstance(msg, HumanMessage):
                cleaned_messages.append(HumanMessage(content=cleaned_content))
            else:
                cleaned_messages.append(AIMessage(content=cleaned_content))
        return cleaned_messages

    def get_conversation_summary(self) -> str:
        """Get a text summary of the conversation."""
        lines = [
            f"Conversation ID: {self.id}",
            f"Vulnerability Type: {self.vulnerability_type}",
            f"Created: {self.created_at.isoformat()}",
            f"Messages: {len(self.messages)}",
            f"Directory: {self.conversation_dir}",
            "",
            "=" * 60,
        ]

        for i, msg in enumerate(self.messages):
            role = "RED TEAM" if isinstance(msg, HumanMessage) else "TARGET"
            lines.append(f"\n[{i}] {role}:")
            lines.append(msg.content)
            lines.append("-" * 60)

        if self.analysis_result:
            lines.append("\n" + "=" * 60)
            lines.append("ANALYSIS RESULTS")
            lines.append("=" * 60)
            lines.append(
                f"Vulnerability Found: {self.analysis_result.get('vulnerability_found', 'N/A')}"
            )
            lines.append(
                f"Confidence: {self.analysis_result.get('confidence', 'N/A')}/10"
            )
            lines.append(
                f"Severity: {self.analysis_result.get('severity', 'N/A').upper()}"
            )
            lines.append(
                f"\nExplanation: {self.analysis_result.get('explanation', 'N/A')}"
            )

        return "\n".join(lines)
