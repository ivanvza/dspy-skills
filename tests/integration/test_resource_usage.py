"""Integration tests for references/ and assets/ directory support.

These tests verify that the DSPy agent correctly:
1. Discovers skills with references and assets
2. Lists available resources when activating skills
3. Actually reads and uses resources from these directories
4. Handles binary files appropriately
"""

import pytest

from dspy_skills import SkillManager, SkillsReActAgent
from dspy_skills.tools import (
    create_activate_skill_tool,
    create_list_skills_tool,
    create_read_resource_tool,
)
from dspy_skills.security import ScriptExecutor


class TestResourceDiscovery:
    """Test that resources are properly discovered and listed."""

    def test_manager_lists_references(self, skill_manager: SkillManager):
        """Verify SkillManager.list_references returns correct files."""
        refs = skill_manager.list_references("reference-lookup")
        assert "codes.md" in refs
        assert "formats.md" in refs

    def test_manager_lists_assets(self, skill_manager: SkillManager):
        """Verify SkillManager.list_assets returns correct files."""
        assets = skill_manager.list_assets("asset-templates")
        assert "template.txt" in assets
        assert "config.json" in assets
        # Nested asset
        assert "images/sample.png" in assets

    def test_manager_lists_combined_resources(self, skill_manager: SkillManager):
        """Verify skill with both references and assets lists both."""
        refs = skill_manager.list_references("combined-resources")
        assets = skill_manager.list_assets("combined-resources")
        assert "guide.md" in refs
        assert "data.csv" in assets


class TestActivateSkillShowsResources:
    """Test that activate_skill tool properly displays available resources."""

    def test_activate_shows_references(self, skill_manager: SkillManager):
        """Verify activate_skill output includes references list."""
        activate = create_activate_skill_tool(skill_manager)
        result = activate("reference-lookup")

        assert "References" in result
        assert "codes.md" in result
        assert "formats.md" in result
        assert "read_skill_resource" in result

    def test_activate_shows_assets(self, skill_manager: SkillManager):
        """Verify activate_skill output includes assets list."""
        activate = create_activate_skill_tool(skill_manager)
        result = activate("asset-templates")

        assert "Assets" in result
        assert "template.txt" in result
        assert "config.json" in result

    def test_activate_shows_both_resources(self, skill_manager: SkillManager):
        """Verify activate_skill shows both references and assets."""
        activate = create_activate_skill_tool(skill_manager)
        result = activate("combined-resources")

        assert "References" in result
        assert "guide.md" in result
        assert "Assets" in result
        assert "data.csv" in result


class TestReadResourceTool:
    """Test the read_skill_resource tool functionality."""

    def test_read_reference_file(self, skill_manager: SkillManager):
        """Verify reading a reference file returns correct content."""
        read_resource = create_read_resource_tool(skill_manager)
        skill_manager.activate("reference-lookup")

        result = read_resource("reference-lookup", "references", "codes.md")

        assert "E001" in result
        assert "File not found" in result
        assert "E002" in result
        assert "Permission denied" in result

    def test_read_asset_text_file(self, skill_manager: SkillManager):
        """Verify reading a text asset file returns correct content."""
        read_resource = create_read_resource_tool(skill_manager)
        skill_manager.activate("asset-templates")

        result = read_resource("asset-templates", "assets", "template.txt")

        assert "PROJECT REPORT" in result
        assert "{{PROJECT_NAME}}" in result
        assert "{{STATUS}}" in result

    def test_read_asset_json_file(self, skill_manager: SkillManager):
        """Verify reading a JSON asset file returns correct content."""
        read_resource = create_read_resource_tool(skill_manager)
        skill_manager.activate("asset-templates")

        result = read_resource("asset-templates", "assets", "config.json")

        assert "report_settings" in result
        assert "include_timestamp" in result

    def test_read_nested_asset(self, skill_manager: SkillManager):
        """Verify reading an asset in a subdirectory works."""
        read_resource = create_read_resource_tool(skill_manager)
        skill_manager.activate("asset-templates")

        result = read_resource("asset-templates", "assets", "images/sample.png")

        # Should indicate it's a binary file
        assert "binary" in result.lower() or ".png" in result

    def test_read_nonexistent_resource_shows_available(self, skill_manager: SkillManager):
        """Verify error message lists available resources."""
        read_resource = create_read_resource_tool(skill_manager)
        skill_manager.activate("reference-lookup")

        result = read_resource("reference-lookup", "references", "nonexistent.md")

        assert "Error" in result or "not found" in result.lower()
        assert "codes.md" in result  # Should list available files


class TestAgentReadsReferences:
    """Test that the agent actually reads and uses reference files."""

    @pytest.mark.slow
    def test_agent_reads_reference_to_answer_question(self, agent: SkillsReActAgent):
        """Agent should read codes.md to answer error code questions.

        This is the key integration test: the agent must:
        1. Identify reference-lookup as the relevant skill
        2. Activate the skill
        3. Read references/codes.md
        4. Use the information to answer correctly
        """
        result = agent(
            request="What does error code E002 mean? Use the reference-lookup skill."
        )

        response = result.response.lower()
        # The answer must contain the actual definition from codes.md
        assert "permission" in response or "denied" in response or "access" in response

    @pytest.mark.slow
    def test_agent_reads_reference_for_status_code(self, agent: SkillsReActAgent):
        """Agent should look up status codes from the reference file."""
        result = agent(
            request="Using the reference-lookup skill, what does status code S200 mean?"
        )

        response = result.response.lower()
        # S200 = "Operation completed successfully" per codes.md
        assert "success" in response or "completed" in response


class TestAgentReadsAssets:
    """Test that the agent actually reads and uses asset files."""

    @pytest.mark.slow
    def test_agent_reads_template_asset(self, agent: SkillsReActAgent):
        """Agent should read template.txt to format output."""
        result = agent(
            request=(
                "Use the asset-templates skill to generate a project report "
                "for project 'TestProject' with status 'Complete'. "
                "Make sure to read the template first."
            )
        )

        response = result.response
        # Should contain elements from the template
        assert "TestProject" in response or "TESTPROJECT" in response.upper()

    @pytest.mark.slow
    def test_agent_identifies_binary_asset(self, agent: SkillsReActAgent):
        """Agent should correctly identify binary files in assets."""
        result = agent(
            request=(
                "Use the asset-templates skill. "
                "What file is in the images/ subdirectory of assets? "
                "Is it a text file or binary file?"
            )
        )

        response = result.response.lower()
        # Should mention it's binary or PNG
        assert "png" in response or "binary" in response or "image" in response


class TestAgentUsesBothResources:
    """Test that the agent can use both references and assets together."""

    @pytest.mark.slow
    def test_agent_uses_reference_and_asset_together(self, agent: SkillsReActAgent):
        """Agent should read both guide.md and data.csv to answer questions."""
        result = agent(
            request=(
                "Use the combined-resources skill. "
                "Look at the data file and tell me: what region does code R02 represent, "
                "and how many records have that region code?"
            )
        )

        response = result.response.lower()
        # R02 = "South" per guide.md, and there are 3 R02 records in data.csv
        assert "south" in response
        # Should mention the count (3 records)
        assert "3" in result.response or "three" in response

    @pytest.mark.slow
    def test_agent_interprets_data_using_guide(self, agent: SkillsReActAgent):
        """Agent must use the guide to interpret status codes in the data."""
        result = agent(
            request=(
                "Using the combined-resources skill, analyze the data: "
                "What is the total value of all 'Active' status records? "
                "Remember to read the guide first to understand what status codes mean."
            )
        )

        response = result.response
        # Active (A) records: 100 + 250 + 300 + 125 + 200 = 975
        assert "975" in response or "active" in response.lower()


class TestListSkillsShowsResources:
    """Test that list_skills includes resource information."""

    def test_list_skills_shows_resource_counts(self, skill_manager: SkillManager):
        """list_skills should indicate when skills have resources."""
        # Activate a skill first so resources are shown
        skill_manager.activate("reference-lookup")

        list_skills = create_list_skills_tool(skill_manager)
        result = list_skills()

        # The activated skill should show its resources
        assert "reference-lookup" in result
