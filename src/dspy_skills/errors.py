"""Custom exceptions for dspy-skills."""

from pathlib import Path
from typing import Optional


class SkillError(Exception):
    """Base exception for all skill-related errors."""

    pass


class ParseError(SkillError):
    """Raised when SKILL.md parsing fails."""

    pass


class ValidationError(SkillError):
    """Raised when skill validation fails."""

    def __init__(self, message: str, errors: Optional[list[str]] = None):
        super().__init__(message)
        self.errors = errors or [message]


class SkillNotFoundError(SkillError):
    """Raised when a requested skill doesn't exist."""

    def __init__(self, skill_name: str, available: Optional[list[str]] = None):
        self.skill_name = skill_name
        self.available = available or []
        msg = f"Skill '{skill_name}' not found"
        if available:
            msg += f". Available: {', '.join(available)}"
        super().__init__(msg)


class ResourceNotFoundError(SkillError):
    """Raised when a skill resource (script/reference/asset) doesn't exist."""

    def __init__(self, skill_name: str, resource_type: str, filename: str):
        self.skill_name = skill_name
        self.resource_type = resource_type
        self.filename = filename
        super().__init__(f"Resource '{filename}' not found in {skill_name}/{resource_type}/")


class ExecutionError(SkillError):
    """Raised when script execution fails."""

    def __init__(self, script_path: Path, reason: str, stderr: Optional[str] = None):
        self.script_path = script_path
        self.reason = reason
        self.stderr = stderr
        super().__init__(f"Execution of {script_path} failed: {reason}")


class SecurityError(SkillError):
    """Raised when a security violation is detected."""

    pass


class ConfigurationError(SkillError):
    """Raised when configuration is invalid."""

    pass
