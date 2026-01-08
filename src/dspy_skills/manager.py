"""Skill discovery, loading, and state management."""

import logging
from pathlib import Path
from typing import Optional

from .errors import ResourceNotFoundError, SkillNotFoundError, ValidationError
from .models import LoadedSkill, SkillState
from .parser import read_instructions, read_skill
from .validator import validate

logger = logging.getLogger(__name__)


class SkillManager:
    """Manages skill discovery, loading, and state.

    Implements progressive disclosure:
    1. Discovery: Load only metadata (name, description) for all skills
    2. Activation: Load full instructions when a skill is needed
    3. Resources: Access scripts/references/assets on demand

    Example:
        >>> manager = SkillManager([Path("~/.skills").expanduser()])
        >>> manager.discover()
        ['pdf', 'docx', 'webapp-testing']
        >>> skill = manager.activate("pdf")
        >>> print(skill.instructions[:100])
        # PDF Processing...
    """

    def __init__(
        self,
        skill_dirs: list[Path],
        validate_on_load: bool = True,
    ):
        """Initialize the SkillManager.

        Args:
            skill_dirs: List of directories to scan for skills
            validate_on_load: Whether to validate skills during discovery
        """
        self._skill_dirs = [Path(d).expanduser().resolve() for d in skill_dirs]
        self._validate_on_load = validate_on_load
        self._skills: dict[str, LoadedSkill] = {}
        self._active_skill: Optional[str] = None

    def discover(self) -> list[str]:
        """Scan all configured directories for valid skills.

        Loads metadata only (progressive disclosure level 1).

        Returns:
            List of discovered skill names
        """
        self._skills.clear()
        discovered = []

        for skill_dir in self._skill_dirs:
            if not skill_dir.exists():
                logger.warning(f"Skill directory does not exist: {skill_dir}")
                continue

            if not skill_dir.is_dir():
                logger.warning(f"Skill path is not a directory: {skill_dir}")
                continue

            # Find all subdirectories that contain SKILL.md
            for subdir in skill_dir.iterdir():
                if not subdir.is_dir():
                    continue

                skill_md = subdir / "SKILL.md"
                if not skill_md.exists():
                    skill_md = subdir / "skill.md"
                    if not skill_md.exists():
                        continue

                # Validate if requested
                if self._validate_on_load:
                    errors = validate(subdir)
                    if errors:
                        logger.warning(
                            f"Skipping invalid skill at {subdir}: {'; '.join(errors)}"
                        )
                        continue

                # Load metadata only
                try:
                    skill = read_skill(subdir, load_instructions=False)
                    if skill.name in self._skills:
                        logger.warning(
                            f"Duplicate skill name '{skill.name}' at {subdir}, "
                            f"keeping first from {self._skills[skill.name].path}"
                        )
                        continue
                    self._skills[skill.name] = skill
                    discovered.append(skill.name)
                except Exception as e:
                    logger.warning(f"Failed to load skill from {subdir}: {e}")
                    continue

        logger.info(f"Discovered {len(discovered)} skills: {discovered}")
        return discovered

    def list_skills(self) -> list[LoadedSkill]:
        """Return all discovered skills with their metadata.

        Returns:
            List of LoadedSkill objects (metadata only, unless activated)
        """
        return list(self._skills.values())

    def get_skill(self, name: str) -> Optional[LoadedSkill]:
        """Get a skill by name.

        Args:
            name: The skill name

        Returns:
            The LoadedSkill if found, None otherwise
        """
        return self._skills.get(name)

    def activate(self, name: str) -> LoadedSkill:
        """Activate a skill by loading its full instructions.

        Implements progressive disclosure level 2.

        Args:
            name: Skill name to activate

        Returns:
            The activated LoadedSkill with instructions populated

        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        skill = self._skills.get(name)
        if skill is None:
            raise SkillNotFoundError(name, list(self._skills.keys()))

        if skill.state == SkillState.ACTIVATED:
            # Already activated
            self._active_skill = name
            return skill

        # Load full instructions
        try:
            instructions = read_instructions(skill.path)
            skill.instructions = instructions
            skill.state = SkillState.ACTIVATED
            self._active_skill = name
            logger.info(f"Activated skill: {name}")
            return skill
        except Exception as e:
            raise ValidationError(f"Failed to load instructions for skill '{name}': {e}")

    def get_active_skill(self) -> Optional[LoadedSkill]:
        """Return the currently active skill, if any.

        Returns:
            The active LoadedSkill, or None if no skill is active
        """
        if self._active_skill:
            return self._skills.get(self._active_skill)
        return None

    def list_scripts(self, skill_name: str) -> list[str]:
        """List available scripts for a skill.

        Args:
            skill_name: Name of the skill

        Returns:
            List of script filenames

        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        skill = self._skills.get(skill_name)
        if skill is None:
            raise SkillNotFoundError(skill_name, list(self._skills.keys()))

        scripts_dir = skill.scripts_dir
        if scripts_dir is None:
            return []

        return [f.name for f in scripts_dir.iterdir() if f.is_file()]

    def list_references(self, skill_name: str) -> list[str]:
        """List available reference files for a skill.

        Args:
            skill_name: Name of the skill

        Returns:
            List of reference filenames

        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        skill = self._skills.get(skill_name)
        if skill is None:
            raise SkillNotFoundError(skill_name, list(self._skills.keys()))

        refs_dir = skill.references_dir
        if refs_dir is None:
            return []

        return [f.name for f in refs_dir.iterdir() if f.is_file()]

    def list_assets(self, skill_name: str) -> list[str]:
        """List available asset files for a skill.

        Args:
            skill_name: Name of the skill

        Returns:
            List of asset filenames

        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        skill = self._skills.get(skill_name)
        if skill is None:
            raise SkillNotFoundError(skill_name, list(self._skills.keys()))

        assets_dir = skill.assets_dir
        if assets_dir is None:
            return []

        # For assets, we might want to recurse into subdirectories
        assets = []
        for item in assets_dir.rglob("*"):
            if item.is_file():
                # Return relative path from assets_dir
                assets.append(str(item.relative_to(assets_dir)))
        return assets

    def get_resource_path(
        self, skill_name: str, resource_type: str, filename: str
    ) -> Path:
        """Get the full path to a skill resource.

        Args:
            skill_name: Name of the skill
            resource_type: One of 'scripts', 'references', 'assets'
            filename: Name of the file (can include subdirectory for assets)

        Returns:
            Absolute path to the resource

        Raises:
            SkillNotFoundError: If skill doesn't exist
            ResourceNotFoundError: If resource doesn't exist
        """
        skill = self._skills.get(skill_name)
        if skill is None:
            raise SkillNotFoundError(skill_name, list(self._skills.keys()))

        if resource_type == "scripts":
            base_dir = skill.scripts_dir
        elif resource_type == "references":
            base_dir = skill.references_dir
        elif resource_type == "assets":
            base_dir = skill.assets_dir
        else:
            raise ValueError(
                f"Invalid resource_type '{resource_type}'. "
                "Must be 'scripts', 'references', or 'assets'."
            )

        if base_dir is None:
            raise ResourceNotFoundError(
                skill_name, resource_type, filename
            )

        resource_path = base_dir / filename

        # Security: ensure path doesn't escape the resource directory
        try:
            resource_path = resource_path.resolve()
            base_dir_resolved = base_dir.resolve()
            if not str(resource_path).startswith(str(base_dir_resolved)):
                raise ResourceNotFoundError(skill_name, resource_type, filename)
        except Exception:
            raise ResourceNotFoundError(skill_name, resource_type, filename)

        if not resource_path.exists():
            raise ResourceNotFoundError(skill_name, resource_type, filename)

        return resource_path
