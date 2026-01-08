"""run_skill_script tool for executing skill scripts."""

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ..manager import SkillManager
    from ..security import ScriptExecutor

from ..errors import ExecutionError, ResourceNotFoundError, SecurityError, SkillNotFoundError
from ..models import SkillState


def create_run_script_tool(
    manager: "SkillManager",
    executor: "ScriptExecutor",
) -> Callable[[str, str, str], str]:
    """Create the run_skill_script tool function.

    Args:
        manager: The SkillManager instance
        executor: The ScriptExecutor for safe script execution

    Returns:
        A callable that runs skill scripts
    """

    def run_skill_script(skill_name: str, script_name: str, arguments: str = "") -> str:
        """Run a script from an activated skill.

        Scripts perform specific operations like extracting data, validating files,
        or processing documents. Always run a script with --help first to understand
        its usage before running with actual arguments.

        Args:
            skill_name: The name of the skill containing the script (e.g., 'pdf')
            script_name: The name of the script file (e.g., 'extract.py', 'validate.sh')
            arguments: Space-separated arguments to pass to the script (default: "")

        Returns:
            The script's output (stdout), or an error message if execution fails
        """
        # Check if skill exists
        skill = manager.get_skill(skill_name)
        if skill is None:
            available = [s.name for s in manager.list_skills()]
            return (
                f"Error: Skill '{skill_name}' not found. "
                f"Available skills: {', '.join(available) if available else 'none'}"
            )

        # Verify skill is activated
        if skill.state != SkillState.ACTIVATED:
            return (
                f"Error: Skill '{skill_name}' must be activated before running scripts. "
                f"Use `activate_skill('{skill_name}')` first."
            )

        # Get script path
        try:
            script_path = manager.get_resource_path(skill_name, "scripts", script_name)
        except ResourceNotFoundError:
            available = manager.list_scripts(skill_name)
            return (
                f"Error: Script '{script_name}' not found. "
                f"Available scripts: {', '.join(available) if available else 'none'}"
            )
        except SkillNotFoundError as e:
            return f"Error: {e}"

        # Parse arguments
        args = arguments.split() if arguments.strip() else []

        # Execute the script
        try:
            result = executor.run(
                script_path=script_path,
                arguments=args,
                working_dir=skill.path,
            )

            # Build response
            if result.timed_out:
                return f"Error: Script timed out after {executor.timeout} seconds"

            if result.returncode == 0:
                output = result.stdout.strip() if result.stdout else "(no output)"
                return f"Script executed successfully:\n\n{output}"
            else:
                error_output = result.stderr.strip() if result.stderr else result.stdout.strip()
                return (
                    f"Script exited with code {result.returncode}:\n\n"
                    f"{error_output if error_output else '(no error output)'}"
                )

        except SecurityError as e:
            return f"Security error: {e}"
        except ExecutionError as e:
            return f"Execution error: {e}"
        except Exception as e:
            return f"Error running script: {str(e)}"

    return run_skill_script
