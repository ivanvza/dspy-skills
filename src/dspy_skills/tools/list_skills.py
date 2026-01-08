"""list_skills tool for discovering available skills."""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ..manager import SkillManager

from ..models import SkillState


def create_list_skills_tool(manager: "SkillManager") -> Callable[[], str]:
    """Create the list_skills tool function.

    Args:
        manager: The SkillManager instance

    Returns:
        A callable that lists available skills
    """

    def list_skills() -> str:
        """List all available skills with their names and descriptions.

        Use this to discover what skills are available before activating one.
        Call this first when starting a task to see if any skills can help.

        Returns:
            A formatted list of available skills with descriptions
        """
        skills = manager.list_skills()

        if not skills:
            return "No skills are currently available."

        lines = ["Available skills:\n"]

        for skill in skills:
            status = " [ACTIVE]" if skill.state == SkillState.ACTIVATED else ""
            lines.append(f"**{skill.name}**{status}")
            lines.append(f"  {skill.description}")

            if skill.compatibility:
                lines.append(f"  Compatibility: {skill.compatibility}")

            # Show available resources for active skills
            if skill.state == SkillState.ACTIVATED:
                resources = []
                if skill.has_scripts():
                    scripts = manager.list_scripts(skill.name)
                    if scripts:
                        resources.append(f"scripts: {', '.join(scripts)}")
                if skill.has_references():
                    refs = manager.list_references(skill.name)
                    if refs:
                        resources.append(f"references: {', '.join(refs)}")
                if resources:
                    lines.append(f"  Resources: {'; '.join(resources)}")

            lines.append("")

        return "\n".join(lines)

    return list_skills
