"""activate_skill tool for loading skill instructions."""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ..manager import SkillManager

from ..errors import SkillNotFoundError


def create_activate_skill_tool(manager: "SkillManager") -> Callable[[str], str]:
    """Create the activate_skill tool function.

    Args:
        manager: The SkillManager instance

    Returns:
        A callable that activates a skill and returns its instructions
    """

    def activate_skill(skill_name: str) -> str:
        """Activate a skill to receive its full instructions.

        Call this when you've identified a skill that matches your current task.
        After activation, follow the skill's instructions carefully.

        Args:
            skill_name: The name of the skill to activate (e.g., 'pdf', 'docx')

        Returns:
            The full skill instructions, plus information about available resources
        """
        try:
            skill = manager.activate(skill_name)

            # Build response with instructions and available resources
            response_parts = [
                f"# Skill '{skill.name}' Activated\n",
            ]

            # Add the skill instructions
            if skill.instructions:
                response_parts.append(skill.instructions)
            else:
                response_parts.append("(No instructions available)")

            response_parts.append("\n---\n## Available Resources\n")

            # List scripts if available
            scripts = manager.list_scripts(skill_name)
            if scripts:
                response_parts.append("### Scripts")
                response_parts.append(
                    "Use `run_skill_script` to execute these. "
                    "Run with --help first to see usage."
                )
                for script in scripts:
                    response_parts.append(f"- `{script}`")
                response_parts.append("")

            # List references if available
            refs = manager.list_references(skill_name)
            if refs:
                response_parts.append("### References")
                response_parts.append(
                    "Use `read_skill_resource` with resource_type='references' to read these."
                )
                for ref in refs:
                    response_parts.append(f"- `{ref}`")
                response_parts.append("")

            # List assets if available
            assets = manager.list_assets(skill_name)
            if assets:
                response_parts.append("### Assets")
                response_parts.append(
                    "Use `read_skill_resource` with resource_type='assets' to read these."
                )
                # Limit to first 10 assets if there are many
                display_assets = assets[:10]
                for asset in display_assets:
                    response_parts.append(f"- `{asset}`")
                if len(assets) > 10:
                    response_parts.append(f"- ... and {len(assets) - 10} more")
                response_parts.append("")

            if not scripts and not refs and not assets:
                response_parts.append("(No additional resources available)")

            return "\n".join(response_parts)

        except SkillNotFoundError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error activating skill '{skill_name}': {str(e)}"

    return activate_skill
