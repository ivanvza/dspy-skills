"""Data models for dspy-skills."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class SkillState(Enum):
    """Represents the loading state of a skill."""

    DISCOVERED = "discovered"  # Metadata loaded only
    ACTIVATED = "activated"  # Full instructions loaded


@dataclass
class LoadedSkill:
    """Represents a skill with its current load state.

    Attributes:
        name: The skill name (from frontmatter)
        description: What the skill does and when to use it
        path: Path to the skill directory
        state: Current loading state (DISCOVERED or ACTIVATED)
        license: Optional license information
        compatibility: Optional environment requirements
        allowed_tools: Optional space-delimited list of pre-approved tools
        metadata: Optional key-value metadata mapping
        instructions: Full skill instructions (loaded on activation)
    """

    name: str
    description: str
    path: Path
    state: SkillState = SkillState.DISCOVERED
    license: Optional[str] = None
    compatibility: Optional[str] = None
    allowed_tools: Optional[str] = None
    metadata: dict[str, str] = field(default_factory=dict)
    instructions: Optional[str] = None

    @property
    def scripts_dir(self) -> Optional[Path]:
        """Return scripts/ directory if it exists."""
        scripts = self.path / "scripts"
        return scripts if scripts.is_dir() else None

    @property
    def references_dir(self) -> Optional[Path]:
        """Return references/ directory if it exists."""
        refs = self.path / "references"
        return refs if refs.is_dir() else None

    @property
    def assets_dir(self) -> Optional[Path]:
        """Return assets/ directory if it exists."""
        assets = self.path / "assets"
        return assets if assets.is_dir() else None

    def has_scripts(self) -> bool:
        """Check if the skill has a scripts directory."""
        return self.scripts_dir is not None

    def has_references(self) -> bool:
        """Check if the skill has a references directory."""
        return self.references_dir is not None
