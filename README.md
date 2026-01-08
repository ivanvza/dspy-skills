# DSPy Skills

Universal Agent Skills integration for DSPy ReAct agents.

This package provides seamless integration of the [Agent Skills](https://agentskills.io) specification with DSPy ReAct agents, enabling agents to discover, activate, and use skills dynamically.

> **Read the blog post**: [Replicating Anthropic's Agent Skills with DSPy](https://blog.navcore.io/AI-Agents/Replicating-Anthropic-Agent-Skills-with-DSPy) - A deep dive into the architecture, progressive disclosure pattern, and lessons learned from building this integration.

## Installation

```bash
# Install from GitHub
pip install git+https://github.com/ivanvza/dspy-skills.git

# Or clone and install locally
git clone https://github.com/ivanvza/dspy-skills.git
cd dspy-skills
pip install .
```

## Quick Start

```python
import dspy
from pathlib import Path
from dspy_skills import SkillsReActAgent, SkillsConfig

# Configure DSPy with your LLM
dspy.configure(lm=dspy.LM("openai/gpt-4"))

# Create a skills-aware agent
agent = SkillsReActAgent(
    signature="request: str -> response: str",
    skill_directories=[Path("~/.skills"), Path("./skills")],
)

# Use the agent - it will automatically discover and use skills
result = agent(request="Extract text from document.pdf")
print(result.response)
```

## Configuration

### Option 1: Configure via Code

```python
from dspy_skills import SkillsReActAgent, SkillsConfig, ScriptConfig, SecurityConfig
from pathlib import Path

config = SkillsConfig(
    skill_directories=[Path("./skills")],
    scripts=ScriptConfig(
        sandbox=True,
        timeout=30,
        allowed_interpreters=["python3", "bash"],
    ),
    security=SecurityConfig(
        allow_network=True,   # Required for network-based skills
        allow_filesystem_write=False,
    ),
)

agent = SkillsReActAgent(
    signature="request: str -> response: str",
    config=config,
)
```

### Option 2: Configure via YAML File

```python
from dspy_skills import SkillsReActAgent, SkillsConfig
from pathlib import Path

config = SkillsConfig.from_yaml(Path("skills_config.yaml"))

agent = SkillsReActAgent(
    signature="request: str -> response: str",
    config=config,
)
```

**skills_config.yaml:**

```yaml
skill_directories:
  - ./skills

validation:
  validate_on_load: true
  strict_mode: false

scripts:
  enabled: true
  sandbox: true
  timeout: 30
  allowed_interpreters:
    - python3
    - bash

security:
  allow_network: true
  allow_filesystem_write: false
  working_dir_only: true

prompt:
  max_skill_description: 200
  include_compatibility: true
```

### Configuration Reference

| Section | Option | Default | Description |
|---------|--------|---------|-------------|
| `scripts` | `sandbox` | `true` | Use firejail sandboxing (Linux) |
| | `timeout` | `30` | Script timeout in seconds |
| | `allowed_interpreters` | `["python3", "bash"]` | Permitted script runners |
| `security` | `allow_network` | `false` | Allow network access |
| | `allow_filesystem_write` | `false` | Allow file writes |
| | `working_dir_only` | `true` | Restrict to working directory |

## How It Works

This package implements the [Agent Skills specification](https://agentskills.io/specification) for DSPy:

1. **Discovery**: At startup, the agent scans configured directories for valid skills
2. **Metadata Loading**: Only skill names and descriptions are loaded initially (~100 tokens per skill)
3. **Activation**: When a task matches a skill, the agent loads full instructions
4. **Execution**: The agent follows instructions and can run bundled scripts

### Meta-Tools

The agent has access to four meta-tools for skill interaction:

- **list_skills**: Discover available skills
- **activate_skill**: Load full instructions for a skill
- **run_skill_script**: Execute scripts from a skill
- **read_skill_resource**: Access reference documents or assets

## What is an Agent Skill?

A skill is a folder containing a `SKILL.md` file with YAML frontmatter and Markdown instructions:

```
my-skill/
├── SKILL.md          # Required: instructions + metadata
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
└── assets/           # Optional: templates, resources
```

Example `SKILL.md`:

```markdown
---
name: pdf-processing
description: Extract text and tables from PDF files, fill forms, merge documents.
---

# PDF Processing

## When to use this skill
Use this skill when the user needs to work with PDF files...

## How to extract text
1. Use pdfplumber for text extraction...
```

### Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Skill identifier (lowercase, hyphens only) |
| `description` | Yes | What the skill does and when to use it |
| `allowed-tools` | No | Space-delimited tools the skill may use |
| `license` | No | License name or reference |
| `compatibility` | No | Environment requirements |
| `metadata` | No | Arbitrary key-value pairs |

### allowed-tools

Skills can declare which external tools they need. The agent will only allow those tools when the skill is active:

```markdown
---
name: pentest-commands
description: Network scanning and security testing commands.
allowed-tools: Bash(nmap:*) Bash(nikto:*) Bash(sqlmap:*)
---
```

This enables a `bash` tool scoped to the active skill - `nmap` commands work when `pentest-commands` is active, but `ls` would be rejected.

### Skill Template

```markdown
---
name: my-skill
description: Brief description of what this skill does and when to use it.
# Optional fields below
allowed-tools: Bash(command:*) Bash(other:*)
license: MIT
compatibility: Requires python3, curl
metadata:
  author: your-name
  version: "1.0"
---

# My Skill

## Purpose
What this skill accomplishes.

## Instructions
Step-by-step guidance for the agent.

## Examples
Example inputs and expected outputs.
```

## API Reference

### SkillsReActAgent

The main agent class that wraps DSPy's ReAct with skill support.

```python
agent = SkillsReActAgent(
    signature="request: str -> response: str",
    config=SkillsConfig(...),
    additional_tools=[...],  # Optional extra tools
    max_iters=10,
)
```

### SkillManager

Low-level API for skill management:

```python
from dspy_skills import SkillManager

manager = SkillManager([Path("./skills")])
manager.discover()
manager.activate("pdf")
manager.list_scripts("pdf")
```

### Validation

Validate skills against the specification:

```python
from dspy_skills import validate, is_valid_skill

errors = validate(Path("./my-skill"))
if errors:
    print("Validation failed:", errors)

# Quick check
if is_valid_skill(Path("./my-skill")):
    print("Skill is valid")
```

## Security

Script execution includes several safety features:

- **Sandboxing**: Optional firejail integration on Linux
- **Interpreter allowlist**: Only configured interpreters can run
- **Timeout enforcement**: Prevent runaway scripts
- **Path validation**: Prevent directory traversal
- **Environment sanitization**: Minimal environment variables

Configure security in `SkillsConfig`:

```python
config = SkillsConfig(
    skill_directories=[...],
    scripts=ScriptConfig(
        sandbox=True,
        timeout=30,
        allowed_interpreters=["python3", "bash"],
    ),
    security=SecurityConfig(
        allow_network=False,
        allow_filesystem_write=False,
    ),
)
```

## Sample Skills

The repository includes sample skills in `sample_skills/` demonstrating various features:

| Skill | Description | Features Used |
|-------|-------------|---------------|
| `file-utils` | File operations (find, count, stats) | scripts/, allowed-tools |
| `json-tools` | JSON validation, formatting, querying | scripts/ |
| `web-scraper` | Web content extraction | scripts/, references/ |
| `network-check` | Network diagnostics | scripts/ |
| `system-info` | System information gathering | scripts/ |
| `web-fingerprint` | Web server fingerprinting | scripts/, allowed-tools |

Use these as templates for creating your own skills.

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run only fast tests (no LLM calls)
pytest -k "not slow"

# Run LLM integration tests (requires API key)
export OPENAI_API_KEY="your-key"
pytest -m slow -v
```

### Project Structure

```
dspy-skills/
├── src/dspy_skills/       # Main package
│   ├── agent.py           # SkillsReActAgent
│   ├── manager.py         # SkillManager
│   ├── tools/             # Meta-tools (list, activate, run, read)
│   ├── security.py        # Script execution sandbox
│   └── ...
├── sample_skills/         # Example skills
├── test_skills/           # Skills for integration testing
└── tests/                 # Test suite
```
