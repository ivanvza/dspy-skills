"""Secure script execution with sandboxing support."""

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .errors import ExecutionError, SecurityError


@dataclass
class ExecutionResult:
    """Result of script execution."""

    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


class ScriptExecutor:
    """Secure script executor with sandboxing support.

    Features:
    - Interpreter allowlisting
    - Path traversal prevention
    - Timeout enforcement
    - Optional firejail sandboxing on Linux
    - Environment sanitization

    Example:
        >>> executor = ScriptExecutor(timeout=30, sandbox=True)
        >>> result = executor.run(
        ...     script_path=Path("/path/to/skill/scripts/process.py"),
        ...     arguments=["--input", "file.pdf"],
        ...     working_dir=Path("/path/to/skill"),
        ... )
        >>> print(result.stdout)
    """

    def __init__(
        self,
        sandbox_mode: bool = True,
        allowed_interpreters: Optional[list[str]] = None,
        timeout: int = 30,
        allow_network: bool = False,
        allow_filesystem_write: bool = False,
    ):
        """Initialize the ScriptExecutor.

        Args:
            sandbox_mode: Whether to use sandboxing (firejail on Linux)
            allowed_interpreters: List of allowed script interpreters
            timeout: Default timeout in seconds
            allow_network: Whether scripts can access the network
            allow_filesystem_write: Whether scripts can write to the filesystem
        """
        self.sandbox_mode = sandbox_mode
        self.allowed_interpreters = allowed_interpreters or [
            "python3",
            "python",
            "bash",
            "sh",
            "node",
        ]
        self.timeout = timeout
        self.allow_network = allow_network
        self.allow_filesystem_write = allow_filesystem_write

        # Check for firejail availability
        self._has_firejail = shutil.which("firejail") is not None

    def _get_interpreter(self, script_path: Path) -> str:
        """Determine the appropriate interpreter for a script.

        Args:
            script_path: Path to the script

        Returns:
            Interpreter command to use

        Raises:
            SecurityError: If the interpreter is not allowed
        """
        suffix = script_path.suffix.lower()

        interpreter_map = {
            ".py": "python3",
            ".sh": "bash",
            ".bash": "bash",
            ".js": "node",
        }

        interpreter = interpreter_map.get(suffix)

        if not interpreter:
            # Try to read shebang
            try:
                with open(script_path) as f:
                    first_line = f.readline()
                    if first_line.startswith("#!"):
                        # Extract interpreter from shebang
                        shebang_parts = first_line[2:].strip().split()
                        if shebang_parts:
                            # Handle /usr/bin/env python3 style shebangs
                            if "env" in shebang_parts[0]:
                                interpreter = shebang_parts[1] if len(shebang_parts) > 1 else None
                            else:
                                interpreter = shebang_parts[0].split("/")[-1]
            except Exception:
                pass

        if not interpreter:
            raise SecurityError(
                f"Could not determine interpreter for {script_path}. "
                f"Supported extensions: {list(interpreter_map.keys())}"
            )

        # Normalize interpreter name
        if interpreter.startswith("python"):
            interpreter = "python3" if "3" in interpreter else "python"

        if interpreter not in self.allowed_interpreters:
            raise SecurityError(
                f"Interpreter '{interpreter}' not allowed. "
                f"Allowed: {', '.join(self.allowed_interpreters)}"
            )

        return interpreter

    def _validate_script_path(self, script_path: Path, skill_dir: Path) -> None:
        """Validate that the script path is within the skill directory.

        Args:
            script_path: Path to the script
            skill_dir: Path to the skill directory

        Raises:
            SecurityError: If the path is outside the skill directory
        """
        try:
            script_resolved = script_path.resolve()
            skill_resolved = skill_dir.resolve()

            if not str(script_resolved).startswith(str(skill_resolved) + os.sep):
                if script_resolved != skill_resolved:
                    raise SecurityError(
                        f"Script path '{script_path}' is outside skill directory"
                    )
        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(f"Invalid script path: {e}")

    def _build_command(
        self,
        interpreter: str,
        script_path: Path,
        arguments: list[str],
        working_dir: Path,
    ) -> list[str]:
        """Build the command to execute, optionally with sandboxing.

        Args:
            interpreter: Interpreter to use
            script_path: Path to the script
            arguments: Arguments to pass to the script
            working_dir: Working directory for execution

        Returns:
            Command as a list of strings
        """
        cmd = []

        # Add firejail sandboxing on Linux if available and enabled
        if self.sandbox_mode and self._has_firejail:
            cmd = ["firejail", "--quiet", "--noprofile"]

            if not self.allow_network:
                cmd.append("--net=none")

            if not self.allow_filesystem_write:
                cmd.append("--read-only=/")
                cmd.append(f"--whitelist={working_dir}")

            cmd.append("--")

        # Find the interpreter path
        interpreter_path = shutil.which(interpreter)
        if not interpreter_path:
            interpreter_path = interpreter

        cmd.extend([interpreter_path, str(script_path)])
        cmd.extend(arguments)

        return cmd

    def _get_restricted_env(self, working_dir: Path) -> dict:
        """Get a restricted environment for script execution.

        Args:
            working_dir: Working directory for the script

        Returns:
            Environment dictionary
        """
        # Start with minimal environment
        env = {
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "HOME": os.environ.get("HOME", "/tmp"),
            "LANG": os.environ.get("LANG", "en_US.UTF-8"),
            "LC_ALL": os.environ.get("LC_ALL", "en_US.UTF-8"),
            "PWD": str(working_dir),
        }

        # Add Python-specific variables if in a virtualenv
        if "VIRTUAL_ENV" in os.environ:
            env["VIRTUAL_ENV"] = os.environ["VIRTUAL_ENV"]
            env["PATH"] = os.environ["VIRTUAL_ENV"] + "/bin:" + env["PATH"]

        # Add PYTHONPATH for the skill directory
        env["PYTHONPATH"] = str(working_dir)

        return env

    def run(
        self,
        script_path: Path,
        arguments: list[str],
        working_dir: Path,
        timeout: Optional[int] = None,
    ) -> ExecutionResult:
        """Execute a script with sandboxing.

        Args:
            script_path: Path to the script
            arguments: Command-line arguments
            working_dir: Working directory for execution
            timeout: Override default timeout

        Returns:
            ExecutionResult with stdout, stderr, and return code

        Raises:
            SecurityError: If script path or interpreter is invalid
            ExecutionError: If execution fails
        """
        timeout = timeout or self.timeout

        # Security validations
        self._validate_script_path(script_path, working_dir)
        interpreter = self._get_interpreter(script_path)

        # Verify script exists and is readable
        if not script_path.exists():
            raise ExecutionError(script_path, "Script file does not exist")
        if not script_path.is_file():
            raise ExecutionError(script_path, "Script path is not a file")

        # Build command
        cmd = self._build_command(interpreter, script_path, arguments, working_dir)

        # Get restricted environment
        env = self._get_restricted_env(working_dir)

        # Execute
        try:
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
            )
            return ExecutionResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                returncode=-1,
                stdout="",
                stderr=f"Script timed out after {timeout} seconds",
                timed_out=True,
            )
        except FileNotFoundError as e:
            raise ExecutionError(script_path, f"Interpreter not found: {e}")
        except PermissionError as e:
            raise ExecutionError(script_path, f"Permission denied: {e}")
        except Exception as e:
            raise ExecutionError(script_path, str(e))

    def run_command(self, command: str, timeout: Optional[int] = None) -> str:
        """Execute a shell command with sandboxing.

        Uses firejail if available and sandbox_mode is enabled.
        Respects allow_network and allow_filesystem_write settings.

        Args:
            command: Shell command to execute
            timeout: Override default timeout

        Returns:
            Command output as string (stdout + stderr)
        """
        timeout = timeout or self.timeout

        # Fail-safe: if restrictions requested but can't enforce, refuse to run
        if self.sandbox_mode:
            if not self.allow_network and not self._has_firejail:
                return (
                    "Error: Network access is disabled but firejail is not installed "
                    "to enforce it. Install firejail or set allow_network=True."
                )
            if not self.allow_filesystem_write and not self._has_firejail:
                return (
                    "Error: Filesystem write is disabled but firejail is not installed "
                    "to enforce it. Install firejail or set allow_filesystem_write=True."
                )

        cmd: list[str] = []

        if self.sandbox_mode and self._has_firejail:
            cmd = ["firejail", "--quiet", "--noprofile"]
            if not self.allow_network:
                cmd.append("--net=none")
            if not self.allow_filesystem_write:
                cmd.append("--read-only=/")
            cmd.append("--")

        cmd.extend(["bash", "-c", command])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = result.stdout
            if result.stderr:
                output += f"\n{result.stderr}"
            if result.returncode != 0:
                output += f"\n[Exit code: {result.returncode}]"
            return output.strip() if output.strip() else "(no output)"
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout} seconds"
        except Exception as e:
            return f"Error: {e}"
