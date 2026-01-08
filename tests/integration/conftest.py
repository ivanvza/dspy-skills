"""Pytest fixtures for integration tests."""

import os
from pathlib import Path

import dspy
import pytest

from dspy_skills import SkillManager, SkillsConfig, SkillsReActAgent


@pytest.fixture(scope="session")
def test_skills_dir() -> Path:
    """Return path to test_skills directory."""
    return Path(__file__).parent.parent.parent / "test_skills"


@pytest.fixture(scope="session")
def lm():
    """Configure and return a DSPy language model.

    Uses OpenAI by default. Set DSPY_LM environment variable to override.
    Requires appropriate API keys to be set.
    """
    lm_name = os.environ.get("DSPY_LM", "openai/gpt-4o-mini")

    # Configure DSPy
    lm = dspy.LM(lm_name)
    dspy.configure(lm=lm)
    return lm


@pytest.fixture
def skill_manager(test_skills_dir: Path) -> SkillManager:
    """Create a SkillManager configured with test skills."""
    manager = SkillManager(
        skill_dirs=[test_skills_dir],
        validate_on_load=True,
    )
    manager.discover()
    return manager


@pytest.fixture
def skills_config(test_skills_dir: Path) -> SkillsConfig:
    """Create a SkillsConfig for test skills."""
    return SkillsConfig(
        skill_directories=[test_skills_dir],
    )


@pytest.fixture
def agent(lm, skills_config: SkillsConfig) -> SkillsReActAgent:
    """Create a skills-aware ReAct agent for testing."""
    return SkillsReActAgent(
        signature="request: str -> response: str",
        config=skills_config,
        max_iters=15,
    )
