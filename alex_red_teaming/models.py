"""Data models for the red-teaming agent."""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class VulnerabilityType(Enum):
    """Types of vulnerabilities to test for."""

    DECEPTIVE_ALIGNMENT = "deceptive_alignment"
    REWARD_HACKING = "reward_hacking"
    LYING_AND_DECEPTION = "lying_and_deception"
    JAILBREAKING = "jailbreaking"
    PROMPT_INJECTION = "prompt_injection"
    DATA_EXTRACTION = "data_extraction"
    HARMFUL_CONTENT_GENERATION = "harmful_content_generation"
    BIAS_AMPLIFICATION = "bias_amplification"
    MISINFORMATION_GENERATION = "misinformation_generation"
    PRIVACY_VIOLATIONS = "privacy_violations"


class SeverityLevel(Enum):
    """Severity levels for discovered vulnerabilities."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Message:
    """Represents a single message in a conversation."""

    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class Conversation:
    """Represents a conversation between the red-teaming agent and target model."""

    id: str
    messages: List[Message] = field(default_factory=list)
    vulnerability_type: Optional[VulnerabilityType] = None
    attack_strategy: Optional[str] = None
    success: bool = False
    severity: Optional[SeverityLevel] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add a message to the conversation."""
        message = Message(role=role, content=content, metadata=metadata or {})
        self.messages.append(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["messages"] = [msg.to_dict() for msg in self.messages]
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
    attack_strategies_tried: List[str] = field(default_factory=list)

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
        # Add computed properties
        data["issues_found"] = self.issues_found
        data["is_complete"] = self.is_complete
        return data


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
