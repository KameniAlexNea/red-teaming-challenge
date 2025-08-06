"""Base prompt templates and utilities."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from jinja2 import Template
from dataclasses import dataclass


@dataclass
class PromptContext:
    """Context for prompt generation."""
    vulnerability_type: str
    previous_attempts: List[str] = None
    conversation_history: List[Dict[str, str]] = None
    target_model: str = ""
    additional_context: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.previous_attempts is None:
            self.previous_attempts = []
        if self.conversation_history is None:
            self.conversation_history = []
        if self.additional_context is None:
            self.additional_context = {}


class BasePromptTemplate(ABC):
    """Base class for prompt templates."""
    
    def __init__(self, template_string: str):
        """Initialize with a Jinja2 template string."""
        self.template = Template(template_string)
    
    @abstractmethod
    def generate(self, context: PromptContext) -> str:
        """Generate a prompt based on the context."""
        pass
    
    def render_template(self, **kwargs) -> str:
        """Render the template with provided variables."""
        return self.template.render(**kwargs)


class PromptValidator:
    """Validator for generated prompts."""
    
    @staticmethod
    def validate_length(prompt: str, min_length: int = 10, max_length: int = 5000) -> bool:
        """Validate prompt length."""
        return min_length <= len(prompt) <= max_length
    
    @staticmethod
    def validate_content(prompt: str, forbidden_words: List[str] = None) -> bool:
        """Validate prompt content doesn't contain forbidden words."""
        if forbidden_words is None:
            forbidden_words = []
        
        prompt_lower = prompt.lower()
        return not any(word.lower() in prompt_lower for word in forbidden_words)
    
    @staticmethod
    def validate_prompt(prompt: str, context: PromptContext) -> Dict[str, Any]:
        """Comprehensive prompt validation."""
        return {
            "valid": True,
            "length_valid": PromptValidator.validate_length(prompt),
            "content_valid": PromptValidator.validate_content(prompt),
            "prompt_length": len(prompt),
            "validation_errors": []
        }
