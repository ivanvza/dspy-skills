"""SkillsReActAgent - DSPy ReAct agent with integrated skill support."""

import re
from pathlib import Path
from typing import Any, Callable, Optional, Union

import dspy

from .config import SkillsConfig
from .manager import SkillManager
from .prompt import build_skills_aware_instructions
from .security import ScriptExecutor
from .tools import (
    create_activate_skill_tool,
    create_list_skills_tool,
    create_read_resource_tool,
    create_run_script_tool,
)


def create_skill_tools(
    manager: SkillManager,
    executor: ScriptExecutor,
) -> list[dspy.Tool]:
    """Create DSPy Tool instances for skill interaction.

    Args:
        manager: The SkillManager instance
        executor: The ScriptExecutor for safe script execution

    Returns:
        List of dspy.Tool instances ready for use with ReAct
    """
    return [
        dspy.Tool(
            func=create_list_skills_tool(manager),
            name="list_skills",
            desc=(
                "List all available skills with their names and descriptions. "
                "Use this to discover what capabilities are available for the current task."
            ),
        ),
        dspy.Tool(
            func=create_activate_skill_tool(manager),
            name="activate_skill",
            desc=(
                "Activate a skill to receive its full instructions. "
                "You must activate a skill before using its scripts or resources. "
                "Pass the skill name as the argument (e.g., 'pdf', 'docx')."
            ),
        ),
        dspy.Tool(
            func=create_run_script_tool(manager, executor),
            name="run_skill_script",
            desc=(
                "Run a script from an activated skill. "
                "Scripts perform specific operations like extracting data or processing files. "
                "Pass skill_name, script_name, and optional arguments."
            ),
        ),
        dspy.Tool(
            func=create_read_resource_tool(manager),
            name="read_skill_resource",
            desc=(
                "Read a reference document or asset file from a skill. "
                "Use this to get additional documentation or templates. "
                "Pass skill_name, resource_type ('references' or 'assets'), and filename."
            ),
        ),
    ]


class SkillsReActAgent:
    """A DSPy ReAct agent with integrated skill support.

    This agent wraps DSPy's ReAct module and adds:
    - Automatic skill discovery and loading
    - Meta-tools for skill interaction (list, activate, run, read)
    - System prompt injection with skill metadata
    - Secure script execution

    Example:
        >>> import dspy
        >>> from dspy_skills import SkillsReActAgent, SkillsConfig
        >>>
        >>> dspy.configure(lm=dspy.LM("openai/gpt-4"))
        >>>
        >>> config = SkillsConfig(
        ...     skill_directories=[Path("~/.skills"), Path("./skills")]
        ... )
        >>>
        >>> agent = SkillsReActAgent(
        ...     signature="request: str -> response: str",
        ...     config=config,
        ... )
        >>>
        >>> result = agent(request="Extract text from document.pdf")
        >>> print(result.response)
    """

    def __init__(
        self,
        signature: Union[type[dspy.Signature], str],
        config: Optional[SkillsConfig] = None,
        skill_directories: Optional[list[Path]] = None,
        additional_tools: Optional[list[Callable]] = None,
        max_iters: int = 10,
    ):
        """Initialize a skills-aware ReAct agent.

        Args:
            signature: DSPy signature defining inputs/outputs (e.g., "request -> response")
            config: Optional SkillsConfig. If not provided, uses skill_directories or defaults.
            skill_directories: Shorthand for config with just directories (ignored if config set)
            additional_tools: Optional additional tools beyond skill tools
            max_iters: Maximum ReAct iterations (default: 10)
        """
        # Build configuration
        if config is not None:
            self.config = config
        elif skill_directories is not None:
            self.config = SkillsConfig(skill_directories=skill_directories)
        else:
            self.config = SkillsConfig.default()

        # Initialize skill manager
        self.manager = SkillManager(
            skill_dirs=self.config.skill_directories,
            validate_on_load=self.config.validation.validate_on_load,
        )

        # Discover skills
        self._discovered_skills = self.manager.discover()

        # Initialize script executor with security settings
        self.executor = ScriptExecutor(
            sandbox_mode=self.config.scripts.sandbox,
            allowed_interpreters=self.config.scripts.allowed_interpreters,
            timeout=self.config.scripts.timeout,
            allow_network=self.config.security.allow_network,
            allow_filesystem_write=self.config.security.allow_filesystem_write,
        )

        # Create skill tools
        skill_tools = create_skill_tools(self.manager, self.executor)

        # Convert additional tools to dspy.Tool if needed
        all_tools = skill_tools.copy()
        if additional_tools:
            for tool in additional_tools:
                if isinstance(tool, dspy.Tool):
                    all_tools.append(tool)
                else:
                    all_tools.append(dspy.Tool(func=tool))

        # Add bash tool if any skill declares allowed-tools with Bash
        bash_tool = self._create_bash_tool()
        if bash_tool:
            all_tools.append(bash_tool)

        # Enhance signature with skill information
        enhanced_signature = self._enhance_signature(signature)

        # Create the ReAct agent
        self.react = dspy.ReAct(
            signature=enhanced_signature,
            tools=all_tools,
            max_iters=max_iters,
        )

        # Store for reference
        self._signature = signature
        self._max_iters = max_iters

    def _enhance_signature(
        self, signature: Union[type[dspy.Signature], str]
    ) -> Union[type[dspy.Signature], str]:
        """Enhance a signature with skill awareness information.

        Args:
            signature: Original DSPy signature

        Returns:
            Enhanced signature with skill metadata in instructions
        """
        if isinstance(signature, str):
            # For string signatures, we can't easily add instructions
            # The skill tools themselves provide context
            return signature

        # For class-based signatures, enhance the docstring
        original_instructions = signature.__doc__ or ""
        enhanced_instructions = build_skills_aware_instructions(
            original_instructions, self.manager
        )

        # Create a new signature class with enhanced instructions
        class EnhancedSignature(signature):
            pass

        EnhancedSignature.__doc__ = enhanced_instructions
        EnhancedSignature.__name__ = f"SkillsEnhanced{signature.__name__}"

        return EnhancedSignature

    def _any_skill_needs_bash(self) -> bool:
        """Check if any skill declares Bash in allowed-tools."""
        return any(
            skill.allowed_tools and "Bash(" in skill.allowed_tools
            for skill in self.manager.list_skills()
        )

    def _create_bash_tool(self) -> Optional[dspy.Tool]:
        """Create a bash tool scoped to the active skill's allowed-tools.

        Skills can declare allowed-tools in their frontmatter to indicate they need
        shell access. Example: `allowed-tools: Bash(nmap:*) Bash(nikto:*)`

        Only commands matching the ACTIVE skill's patterns will be allowed to run.
        Commands are executed through ScriptExecutor to enforce security settings.

        Returns:
            A dspy.Tool for bash execution, or None if no skill needs it
        """
        if not self._any_skill_needs_bash():
            return None

        # Pattern to extract command prefixes from Bash(command:*)
        bash_pattern = re.compile(r"Bash\(([^:]+):\*\)")

        # Capture references for closure
        manager = self.manager
        executor = self.executor

        def bash(command: str) -> str:
            """Execute a bash command if allowed by the active skill."""
            # Check active skill
            active_skill = manager.get_active_skill()
            if not active_skill:
                return "Error: No skill is active. Activate a skill first."

            if not active_skill.allowed_tools:
                return f"Error: Skill '{active_skill.name}' does not declare any allowed-tools."

            # Parse allowed commands from active skill only
            allowed_commands = set(bash_pattern.findall(active_skill.allowed_tools))
            if not allowed_commands:
                return f"Error: Skill '{active_skill.name}' does not allow any bash commands."

            # Get the first word (the command being run)
            cmd_parts = command.strip().split()
            if not cmd_parts:
                return "Error: Empty command"

            base_cmd = cmd_parts[0]

            # Check if command is allowed by active skill
            if base_cmd not in allowed_commands:
                return (
                    f"Error: Command '{base_cmd}' is not allowed by skill '{active_skill.name}'. "
                    f"Allowed commands: {', '.join(sorted(allowed_commands))}"
                )

            # Execute with sandboxing via ScriptExecutor
            return executor.run_command(command)

        return dspy.Tool(
            func=bash,
            name="bash",
            desc=(
                "Execute a bash command. Commands are restricted to those allowed "
                "by the currently active skill's allowed-tools declaration."
            ),
        )

    def __call__(self, **kwargs: Any) -> Any:
        """Forward calls to the underlying ReAct agent.

        Args:
            **kwargs: Arguments matching the signature's input fields

        Returns:
            Result from the ReAct agent
        """
        return self.react(**kwargs)

    @property
    def discovered_skills(self) -> list[str]:
        """Get the list of discovered skill names."""
        return self._discovered_skills.copy()

    @property
    def active_skill(self) -> Optional[str]:
        """Get the currently active skill name, if any."""
        skill = self.manager.get_active_skill()
        return skill.name if skill else None

