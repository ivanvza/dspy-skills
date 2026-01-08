"""read_skill_resource tool for accessing skill references and assets."""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ..manager import SkillManager

from ..errors import ResourceNotFoundError, SkillNotFoundError
from ..models import SkillState

# Maximum content size to return (prevents context overflow)
MAX_CONTENT_SIZE = 50000


def create_read_resource_tool(manager: "SkillManager") -> Callable[[str, str, str], str]:
    """Create the read_skill_resource tool function.

    Args:
        manager: The SkillManager instance

    Returns:
        A callable that reads skill resource files
    """

    def read_skill_resource(skill_name: str, resource_type: str, filename: str) -> str:
        """Read a reference or asset file from a skill.

        Use this to access additional documentation, templates, or data files
        that a skill provides. The skill's instructions will tell you when
        to read specific resources.

        Args:
            skill_name: The name of the skill (e.g., 'pdf', 'docx')
            resource_type: Type of resource - must be 'references' or 'assets'
            filename: Name of the file to read (e.g., 'forms.md', 'template.txt')

        Returns:
            The file contents, or an error message if reading fails
        """
        # Validate resource type
        if resource_type not in ("references", "assets"):
            return (
                f"Error: Invalid resource_type '{resource_type}'. "
                "Must be 'references' or 'assets'."
            )

        # Check if skill exists
        skill = manager.get_skill(skill_name)
        if skill is None:
            available = [s.name for s in manager.list_skills()]
            return (
                f"Error: Skill '{skill_name}' not found. "
                f"Available skills: {', '.join(available) if available else 'none'}"
            )

        # Warn if skill is not activated (but still allow reading)
        activation_note = ""
        if skill.state != SkillState.ACTIVATED:
            activation_note = (
                "\n\n*Note: This skill is not currently activated. "
                "Consider using `activate_skill` first to get the full instructions.*\n"
            )

        try:
            resource_path = manager.get_resource_path(skill_name, resource_type, filename)

            # Check if it's a binary file
            binary_extensions = {
                ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip",
                ".tar", ".gz", ".ttf", ".otf", ".woff", ".woff2",
                ".ico", ".bmp", ".webp", ".mp3", ".mp4", ".wav",
            }
            if resource_path.suffix.lower() in binary_extensions:
                return (
                    f"# {filename}\n\n"
                    f"This is a binary file ({resource_path.suffix}). "
                    f"Path: `{resource_path}`\n"
                    "Use appropriate tools to work with this file type."
                    f"{activation_note}"
                )

            # Read the file content
            try:
                content = resource_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                return (
                    f"# {filename}\n\n"
                    "This file appears to be binary or uses an unsupported encoding. "
                    f"Path: `{resource_path}`"
                    f"{activation_note}"
                )

            # Truncate if too large
            truncated = False
            if len(content) > MAX_CONTENT_SIZE:
                content = content[:MAX_CONTENT_SIZE]
                truncated = True

            result = f"# {filename}\n\n{content}"

            if truncated:
                result += (
                    f"\n\n---\n*[Content truncated - file exceeds {MAX_CONTENT_SIZE} characters]*"
                )

            if activation_note:
                result += activation_note

            return result

        except ResourceNotFoundError:
            # List available resources of this type
            if resource_type == "references":
                available = manager.list_references(skill_name)
            else:
                available = manager.list_assets(skill_name)

            return (
                f"Error: File '{filename}' not found in {skill_name}/{resource_type}/. "
                f"Available files: {', '.join(available) if available else 'none'}"
            )
        except SkillNotFoundError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error reading file: {str(e)}"

    return read_skill_resource
