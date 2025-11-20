"""Data models for the red-teaming agent."""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage


class VulnerabilityType(Enum):
    """Types of vulnerabilities to test for."""

    REWARD_HACKING = "reward_hacking"
    DECEPTION = "deception"
    DECEPTIVE_ALIGNMENT = "deceptive_alignment"
    SABOTAGE = "sabotage"
    INAPPROPRIATE_TOOL_USE = "inappropriate_tool_use"
    DATA_EXFILTRATION = "data_exfiltration"
    SANDBAGGING = "sandbagging"
    EVALUATION_AWARENESS = "evaluation_awareness"
    CHAIN_OF_THOUGHT_ISSUES = "chain_of_thought_issues"


class SeverityLevel(Enum):
    """Severity levels for discovered vulnerabilities."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Conversation:
    """Represents a conversation between the red-teaming agent and target model."""

    id: str
    messages: List[BaseMessage] = field(default_factory=list)
    vulnerability_type: Optional[VulnerabilityType] = None
    attack_strategy: Optional[str] = None
    success: bool = False
    severity: Optional[SeverityLevel] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: BaseMessage):
        """Add a message to the conversation."""
        self.messages.append(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["messages"] = [msg.model_dump() for msg in self.messages]
        data["vulnerability_type"] = (
            self.vulnerability_type.value if self.vulnerability_type else None
        )
        data["severity"] = self.severity.value if self.severity else None
        data["created_at"] = self.created_at.isoformat()
        return data


@dataclass
class Vulnerability:
    """Represents a discovered vulnerability."""

    id: str
    type: VulnerabilityType
    severity: SeverityLevel
    title: str
    description: str
    attack_vector: str
    conversation_id: str
    proof_of_concept: str
    mitigation_suggestions: List[str] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["type"] = self.type.value
        data["severity"] = self.severity.value
        data["discovered_at"] = self.discovered_at.isoformat()
        return data


@dataclass
class RedTeamingState:
    """State for the red-teaming agent workflow."""

    current_conversation: Optional[Conversation] = None
    discovered_vulnerabilities: List[Vulnerability] = field(default_factory=list)
    failed_attempts: List[Conversation] = field(default_factory=list)
    current_vulnerability_type: Optional[VulnerabilityType] = None
    conversation_turn: int = 0
    max_turns: int = 10
    attempted_vulnerability_types: List[VulnerabilityType] = field(default_factory=list)
    # Validator (Red Team B) fields
    attack_aligned: bool = False
    validator_feedback: Dict[str, Any] = field(default_factory=dict)
    attack_guidance: str = ""
    validation_retries: int = 0
    # Post-response analysis fields
    target_refused: bool = False
    next_step_guidance: str = ""
    post_response_decision: str = ""  # "continue" | "revise" | "reset"
    # Validator can force a specific next strategy
    forced_strategy: str = ""

    # Conversational framework fields
    current_strategy: str = ""
    supervisor_guidance: str = ""
    conversation_turn_count: int = 0
    refusal_streak: int = 0

    @property
    def issues_found(self) -> int:
        """Return the number of issues found."""
        return len(self.discovered_vulnerabilities)

    @property
    def is_complete(self) -> bool:
        """Check if red-teaming is complete."""
        return self.issues_found >= 5

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert nested objects to dictionaries
        data["current_conversation"] = (
            self.current_conversation.to_dict() if self.current_conversation else None
        )
        data["discovered_vulnerabilities"] = [
            vuln.to_dict() for vuln in self.discovered_vulnerabilities
        ]
        data["failed_attempts"] = [conv.to_dict() for conv in self.failed_attempts]
        data["current_vulnerability_type"] = (
            self.current_vulnerability_type.value
            if self.current_vulnerability_type
            else None
        )
        # Convert attempted vulnerability types to plain values
        data["attempted_vulnerability_types"] = [
            t.value for t in self.attempted_vulnerability_types
        ]
        # Conversational fields are simple primitives, serialize as-is
        data["current_strategy"] = self.current_strategy
        data["supervisor_guidance"] = self.supervisor_guidance
        data["conversation_turn_count"] = self.conversation_turn_count
        # Add computed properties
        data["issues_found"] = self.issues_found
        data["is_complete"] = self.is_complete
        return data

    # Backward-compatibility alias for prior field name used incorrectly
    @property
    def attack_strategies_tried(self) -> List[VulnerabilityType]:
        return self.attempted_vulnerability_types


@dataclass
class AttackPrompt:
    """Represents an attack prompt to test the target model."""

    content: str
    vulnerability_type: VulnerabilityType
    strategy: str
    expected_outcome: str
    follow_up_prompts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["vulnerability_type"] = self.vulnerability_type.value
        return data
