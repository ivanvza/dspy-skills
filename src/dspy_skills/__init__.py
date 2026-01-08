"""DSPy Skills - Universal Agent Skills integration for DSPy ReAct agents.

This package provides seamless integration of the Agent Skills specification
(https://agentskills.io) with DSPy ReAct agents, enabling agents to discover,
activate, and use skills dynamically.

Example:
    >>> import dspy
    >>> from dspy_skills import SkillsReActAgent, SkillsConfig
    >>>
    >>> # Configure DSPy with your LLM
    >>> dspy.configure(lm=dspy.LM("openai/gpt-4"))
    >>>
    >>> # Create a skills-aware agent
    >>> agent = SkillsReActAgent(
    ...     signature="request: str -> response: str",
    ...     skill_directories=[Path("~/.skills"), Path("./skills")],
    ... )
    >>>
    >>> # Use the agent - it will automatically discover and use skills
    >>> result = agent(request="Extract text from document.pdf")
    >>> print(result.response)

For more control, use SkillsConfig:
    >>> config = SkillsConfig.from_yaml("skills_config.yaml")
    >>> agent = SkillsReActAgent(signature="request -> response", config=config)
"""

from .agent import SkillsReActAgent, create_skill_tools
from .config import (
    PromptConfig,
    ScriptConfig,
    SecurityConfig,
    SkillsConfig,
    ValidationConfig,
)
from .errors import (
    ConfigurationError,
    ExecutionError,
    ParseError,
    ResourceNotFoundError,
    SecurityError,
    SkillError,
    SkillNotFoundError,
    ValidationError,
)
from .manager import SkillManager
from .models import LoadedSkill, SkillState
from .parser import find_skill_md, parse_frontmatter, read_instructions, read_skill
from .prompt import build_skills_aware_instructions, generate_skills_prompt_block
from .security import ExecutionResult, ScriptExecutor
from .validator import is_valid_skill, validate, validate_metadata

__version__ = "0.1.0"

__all__ = [
    # Main agent class
    "SkillsReActAgent",
    "create_skill_tools",
    # Configuration
    "SkillsConfig",
    "ScriptConfig",
    "SecurityConfig",
    "ValidationConfig",
    "PromptConfig",
    # Core classes
    "SkillManager",
    "LoadedSkill",
    "SkillState",
    "ScriptExecutor",
    "ExecutionResult",
    # Parsing and validation
    "find_skill_md",
    "parse_frontmatter",
    "read_skill",
    "read_instructions",
    "validate",
    "validate_metadata",
    "is_valid_skill",
    # Prompt generation
    "generate_skills_prompt_block",
    "build_skills_aware_instructions",
    # Exceptions
    "SkillError",
    "ParseError",
    "ValidationError",
    "SkillNotFoundError",
    "ResourceNotFoundError",
    "ExecutionError",
    "SecurityError",
    "ConfigurationError",
]
