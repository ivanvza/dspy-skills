---
name: reference-lookup
description: Look up error codes, status codes, and system messages. Use when the user asks about error codes, status meanings, or needs to decode system messages.
license: MIT
metadata:
  author: dspy-skills-test
  version: "1.0"
---

# Reference Lookup

A skill for looking up error codes and status messages.

## When to Use This Skill

Activate this skill when the user needs to:
- Look up what an error code means
- Find the description for a status code
- Understand system messages

## How to Answer Questions

**IMPORTANT**: To answer questions about codes, you MUST read the reference file first.

1. For error codes (E001, E002, etc.): Read `references/codes.md` to find the meaning
2. For response formats: Read `references/formats.md` to see how to structure answers

Do NOT guess or make up code meanings. Always look them up in the reference files.

## Example Workflow

User asks: "What does error code E002 mean?"

1. Read `references/codes.md` using `read_skill_resource`
2. Find E002 in the lookup table
3. Return the exact description from the reference
