"""
Content redaction utilities for the Ziz SDK.

Provides privacy-first content handling with configurable redaction rules.
"""

import re
from typing import Any, Dict, List, Optional, Pattern, Union

from .logging import get_logger

logger = get_logger("redaction")


class RedactionRule:
    """Represents a rule for redacting sensitive content."""

    def __init__(
        self,
        pattern: Union[str, Pattern],
        replacement: str = "[REDACTED]",
        description: str = "",
    ):
        """
        Initialize redaction rule.

        Args:
            pattern: Regex pattern to match sensitive content
            replacement: String to replace matches with
            description: Human-readable description of the rule
        """
        self.pattern = re.compile(pattern) if isinstance(pattern, str) else pattern
        self.replacement = replacement
        self.description = description

    def apply(self, text: str) -> str:
        """Apply this redaction rule to text."""
        if not isinstance(text, str):
            return text
        return self.pattern.sub(self.replacement, text)


class RedactionManager:
    """Manages content redaction with configurable rules."""

    DEFAULT_RULES = [
        # Email addresses
        RedactionRule(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "[EMAIL]",
            "Email addresses",
        ),
        # Phone numbers (US format)
        RedactionRule(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE]", "US phone numbers"),
        # Credit card numbers
        RedactionRule(
            r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            "[CARD]",
            "Credit card numbers",
        ),
        # Social Security Numbers
        RedactionRule(r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]", "Social Security Numbers"),
        # API Keys (generic pattern)
        RedactionRule(r"\b[A-Za-z0-9]{32,}\b", "[API_KEY]", "API keys and tokens"),
    ]

    def __init__(
        self,
        enabled: bool = True,
        rules: Optional[List[RedactionRule]] = None,
        redact_all_content: bool = False,
    ):
        """
        Initialize redaction manager.

        Args:
            enabled: Whether redaction is enabled
            rules: Custom redaction rules (defaults to DEFAULT_RULES)
            redact_all_content: If True, redact all content regardless of rules
        """
        self.enabled = enabled
        self.rules = rules if rules is not None else self.DEFAULT_RULES.copy()
        self.redact_all_content = redact_all_content

    def add_rule(self, rule: RedactionRule) -> None:
        """Add a custom redaction rule."""
        self.rules.append(rule)
        logger.debug(f"Added redaction rule: {rule.description}")

    def remove_rule(self, description: str) -> bool:
        """
        Remove a redaction rule by description.

        Args:
            description: Description of the rule to remove

        Returns:
            True if rule was found and removed, False otherwise
        """
        for i, rule in enumerate(self.rules):
            if rule.description == description:
                del self.rules[i]
                logger.debug(f"Removed redaction rule: {description}")
                return True
        return False

    def redact_text(self, text: str) -> str:
        """
        Apply redaction rules to text.

        Args:
            text: Text to redact

        Returns:
            Redacted text
        """
        if not self.enabled:
            return text

        if self.redact_all_content:
            return "[REDACTED_CONTENT]"

        if not isinstance(text, str):
            return text

        result = text
        for rule in self.rules:
            result = rule.apply(result)

        return result

    def redact_dict(
        self, data: Dict[str, Any], sensitive_keys: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Apply redaction to dictionary values.

        Args:
            data: Dictionary to redact
            sensitive_keys: Additional keys to redact completely

        Returns:
            Dictionary with redacted values
        """
        if not self.enabled:
            return data

        sensitive_keys = sensitive_keys or []
        sensitive_keys.extend(["password", "token", "key", "secret", "auth"])

        result = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                result[key] = "[REDACTED]"
            elif isinstance(value, str):
                result[key] = self.redact_text(value)
            elif isinstance(value, dict):
                result[key] = self.redact_dict(value, sensitive_keys)
            elif isinstance(value, list):
                result[key] = [
                    self.redact_text(item)
                    if isinstance(item, str)
                    else self.redact_dict(item, sensitive_keys)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value

        return result

    def redact_content(self, content: Any, allow_content: bool = False) -> Any:
        """
        Apply redaction to arbitrary content.

        Args:
            content: Content to potentially redact
            allow_content: Whether content logging is explicitly allowed

        Returns:
            Redacted or original content based on settings
        """
        if not self.enabled or allow_content:
            return content

        if self.redact_all_content:
            return "[CONTENT_REDACTED]"

        if isinstance(content, str):
            return self.redact_text(content)
        elif isinstance(content, dict):
            return self.redact_dict(content)
        elif isinstance(content, list):
            return [self.redact_content(item, allow_content) for item in content]
        else:
            # For other types, convert to string and redact if it looks sensitive
            str_content = str(content)
            if len(str_content) > 50:  # Likely contains sensitive data
                return "[CONTENT_REDACTED]"
            return self.redact_text(str_content)
