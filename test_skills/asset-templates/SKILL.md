---
name: asset-templates
description: Generate formatted reports and documents using templates. Use when the user needs to create structured reports, fill in templates, or format output according to specific patterns.
license: MIT
metadata:
  author: dspy-skills-test
  version: "1.0"
---

# Asset Templates

A skill for generating formatted output using template files.

## When to Use This Skill

Activate this skill when the user needs to:
- Generate a formatted report
- Use a template to structure output
- Create documents following a specific format

## Available Templates

Check the `assets/` directory for available templates:
- `template.txt` - Basic report template
- `config.json` - Configuration settings for reports
- `images/sample.png` - Sample image (binary file)

## How to Use Templates

**IMPORTANT**: You MUST read the template file before generating output.

1. Read `assets/template.txt` using `read_skill_resource`
2. Fill in the placeholders with the user's data
3. Return the formatted result

## Template Format

Templates use `{{placeholder}}` syntax for variable substitution.

## Example Workflow

User asks: "Generate a report for project Alpha with status Complete"

1. Read `assets/template.txt` to get the template structure
2. Substitute `{{PROJECT_NAME}}` with "Alpha"
3. Substitute `{{STATUS}}` with "Complete"
4. Return the filled template

## Binary Files

The `assets/images/` directory contains binary files like images.
When asked about binary files, report their path but do not attempt to read their contents.
