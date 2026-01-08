"""Configuration schema and loading for dspy-skills."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .errors import ConfigurationError


@dataclass
class ScriptConfig:
    """Configuration for script execution."""

    enabled: bool = True
    sandbox: bool = True
    timeout: int = 30
    allowed_interpreters: list[str] = field(
        default_factory=lambda: ["python3", "python", "bash", "sh"]
    )
    require_confirmation: bool = False


@dataclass
class SecurityConfig:
    """Security settings for script execution."""

    allow_network: bool = False
    allow_filesystem_write: bool = False
    working_dir_only: bool = True


@dataclass
class ValidationConfig:
    """Configuration for skill validation."""

    validate_on_load: bool = True
    strict_mode: bool = False


@dataclass
class PromptConfig:
    """Configuration for prompt generation."""

    max_skill_description: int = 200
    include_compatibility: bool = True


@dataclass
class SkillsConfig:
    """Main configuration for dspy-skills.

    Attributes:
        skill_directories: List of directories to scan for skills
        validation: Validation settings
        scripts: Script execution settings
        security: Security settings
        prompt: Prompt generation settings

    Example:
        >>> config = SkillsConfig(
        ...     skill_directories=[Path("~/.skills"), Path("./skills")]
        ... )
        >>> # Or load from YAML
        >>> config = SkillsConfig.from_yaml("skills_config.yaml")
    """

    skill_directories: list[Path]
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    scripts: ScriptConfig = field(default_factory=ScriptConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    prompt: PromptConfig = field(default_factory=PromptConfig)

    @classmethod
    def from_yaml(cls, path: Path) -> "SkillsConfig":
        """Load configuration from a YAML file.

        Args:
            path: Path to the YAML configuration file

        Returns:
            SkillsConfig instance

        Raises:
            ConfigurationError: If the file is invalid or missing required fields
        """
        path = Path(path)

        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {path}")

        try:
            with open(path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")

        if not isinstance(data, dict):
            raise ConfigurationError("Configuration must be a YAML mapping")

        # Extract and expand skill directories
        raw_dirs = data.get("skill_directories", [])
        if not raw_dirs:
            raise ConfigurationError("skill_directories is required and cannot be empty")

        skill_dirs = []
        for d in raw_dirs:
            path_obj = Path(d).expanduser().resolve()
            skill_dirs.append(path_obj)

        # Build config objects from nested data
        validation_data = data.get("validation", {})
        scripts_data = data.get("scripts", {})
        security_data = data.get("security", {})
        prompt_data = data.get("prompt", {})

        return cls(
            skill_directories=skill_dirs,
            validation=ValidationConfig(**validation_data),
            scripts=ScriptConfig(**scripts_data),
            security=SecurityConfig(**security_data),
            prompt=PromptConfig(**prompt_data),
        )

    @classmethod
    def from_dict(cls, data: dict) -> "SkillsConfig":
        """Create configuration from a dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            SkillsConfig instance
        """
        raw_dirs = data.get("skill_directories", [])
        skill_dirs = [Path(d).expanduser().resolve() for d in raw_dirs]

        return cls(
            skill_directories=skill_dirs,
            validation=ValidationConfig(**data.get("validation", {})),
            scripts=ScriptConfig(**data.get("scripts", {})),
            security=SecurityConfig(**data.get("security", {})),
            prompt=PromptConfig(**data.get("prompt", {})),
        )

    @classmethod
    def default(cls) -> "SkillsConfig":
        """Create default configuration.

        Returns:
            SkillsConfig with default settings
        """
        return cls(
            skill_directories=[
                Path("~/.skills").expanduser().resolve(),
                Path("./skills").resolve(),
            ]
        )

    def to_dict(self) -> dict:
        """Convert configuration to a dictionary.

        Returns:
            Dictionary representation of the configuration
        """
        return {
            "skill_directories": [str(d) for d in self.skill_directories],
            "validation": {
                "validate_on_load": self.validation.validate_on_load,
                "strict_mode": self.validation.strict_mode,
            },
            "scripts": {
                "enabled": self.scripts.enabled,
                "sandbox": self.scripts.sandbox,
                "timeout": self.scripts.timeout,
                "allowed_interpreters": self.scripts.allowed_interpreters,
                "require_confirmation": self.scripts.require_confirmation,
            },
            "security": {
                "allow_network": self.security.allow_network,
                "allow_filesystem_write": self.security.allow_filesystem_write,
                "working_dir_only": self.security.working_dir_only,
            },
            "prompt": {
                "max_skill_description": self.prompt.max_skill_description,
                "include_compatibility": self.prompt.include_compatibility,
            },
        }

    def save_yaml(self, path: Path) -> None:
        """Save configuration to a YAML file.

        Args:
            path: Path to save the configuration
        """
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)
