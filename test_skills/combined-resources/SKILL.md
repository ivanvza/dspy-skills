---
name: combined-resources
description: Analyze data files using lookup guides. Use when the user needs to interpret CSV data with code lookups, or process data files that require reference documentation.
license: MIT
metadata:
  author: dspy-skills-test
  version: "1.0"
---

# Combined Resources

A skill that uses both references and assets together for data analysis.

## When to Use This Skill

Activate this skill when the user needs to:
- Analyze data files that contain codes requiring lookup
- Interpret CSV data using reference documentation
- Process data with the help of a guide

## Available Resources

### References
- `guide.md` - Documentation for interpreting the data file

### Assets
- `data.csv` - Sample data file containing codes

## How to Complete Tasks

**IMPORTANT**: You must use BOTH the reference guide AND the data file.

1. First, read `references/guide.md` to understand the data format
2. Then, read `assets/data.csv` to get the actual data
3. Use the guide to interpret the codes in the data

## Example Workflow

User asks: "Analyze the data and tell me what region R02 represents"

1. Read `references/guide.md` using `read_skill_resource` with resource_type='references'
2. Read `assets/data.csv` using `read_skill_resource` with resource_type='assets'
3. Look up region code R02 in the guide
4. Return the region name and any relevant data
