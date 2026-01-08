"""Generate XML prompt blocks for agent system prompts."""

import html
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .manager import SkillManager


def generate_skills_prompt_block(manager: "SkillManager") -> str:
    """Generate the <available_skills> XML block for DSPy signature instructions.

    This follows the Anthropic-recommended XML format from the Agent Skills spec.

    Args:
        manager: SkillManager with discovered skills

    Returns:
        XML string with skill metadata for system prompt injection
    """
    skills = manager.list_skills()

    if not skills:
        return "<available_skills>\n(No skills currently available)\n</available_skills>"

    lines = ["<available_skills>"]

    for skill in skills:
        lines.append("<skill>")
        lines.append(f"<name>{html.escape(skill.name)}</name>")
        lines.append(f"<description>{html.escape(skill.description)}</description>")
        if skill.compatibility:
            lines.append(f"<compatibility>{html.escape(skill.compatibility)}</compatibility>")
        lines.append("</skill>")

    lines.append("</available_skills>")

    return "\n".join(lines)


SKILLS_GUIDANCE = """
## Skills System

You have access to a skills system that extends your capabilities. Skills provide specialized
instructions, scripts, and resources for specific tasks.

### How to Use Skills

1. **Discover**: Use `list_skills` to see available skills and their descriptions
2. **Activate**: When a skill matches your task, use `activate_skill` to load its full instructions
3. **Follow**: Read and follow the skill's instructions carefully
4. **Execute**: Use `run_skill_script` to run any scripts the skill provides
5. **Reference**: Use `read_skill_resource` to access additional documentation or assets

### Important Guidelines

- Activate a skill when the task clearly matches its description
- Follow the skill's instructions precisely - they contain tested procedures
- Scripts are the recommended way to perform complex operations
- Reference files contain additional context - read them when the skill instructs you to
- Only one skill should be active at a time for clarity
"""


def build_skills_aware_instructions(
    base_instructions: str,
    manager: "SkillManager",
) -> str:
    """Build instructions that include skill awareness.

    Args:
        base_instructions: The original task instructions
        manager: SkillManager with discovered skills

    Returns:
        Enhanced instructions with skill information
    """
    skills_block = generate_skills_prompt_block(manager)

    return f"{base_instructions}\n\n{SKILLS_GUIDANCE}\n\n{skills_block}"
