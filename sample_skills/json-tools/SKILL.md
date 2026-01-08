---
name: json-tools
description: JSON processing toolkit for validating, formatting, querying, and comparing JSON data. Use when working with JSON files, API responses, configuration files, or any structured JSON data that needs parsing, validation, transformation, or comparison.
license: MIT
metadata:
  author: dspy-skills
  version: "1.0"
---

# JSON Tools

A toolkit for working with JSON data using Python standard library only.

## When to Use This Skill

Activate this skill when the user needs to:
- Validate JSON syntax
- Format/pretty-print JSON
- Query JSON with path expressions
- Compare two JSON files
- Transform JSON data

## Available Scripts

**Always run scripts with `--help` first** to see all available options.

| Script | Purpose |
|--------|---------|
| `validate_json.py` | Check if JSON is valid |
| `format_json.py` | Pretty-print or minify JSON |
| `query_json.py` | Extract data using path expressions |
| `diff_json.py` | Compare two JSON files |

## Decision Tree

```
Task → What do you need?
    │
    ├─ Check if JSON is valid?
    │   └─ Use: validate_json.py <file>
    │
    ├─ Format/beautify JSON?
    │   └─ Use: format_json.py <file>
    │
    ├─ Extract specific data?
    │   └─ Use: query_json.py <file> <path>
    │
    └─ Compare two JSON files?
        └─ Use: diff_json.py <file1> <file2>
```

## Quick Examples

**Validate JSON:**
```bash
python scripts/validate_json.py data.json
echo '{"key": "value"}' | python scripts/validate_json.py -
```

**Format JSON:**
```bash
python scripts/format_json.py data.json
python scripts/format_json.py data.json --indent 4
python scripts/format_json.py data.json --minify
```

**Query JSON:**
```bash
python scripts/query_json.py data.json "users"
python scripts/query_json.py data.json "users.0.name"
python scripts/query_json.py data.json "config.database.host"
```

**Compare JSON:**
```bash
python scripts/diff_json.py old.json new.json
python scripts/diff_json.py config1.json config2.json --keys-only
```

## Path Expression Syntax

The `query_json.py` script uses dot-notation paths:

| Path | Description |
|------|-------------|
| `key` | Access object key |
| `0`, `1`, `2` | Access array index |
| `key.subkey` | Nested access |
| `items.0.name` | Mixed access |
| `.` or empty | Root element |

### Examples

Given JSON:
```json
{
  "users": [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25}
  ],
  "config": {
    "debug": true
  }
}
```

| Path | Result |
|------|--------|
| `users` | The users array |
| `users.0` | First user object |
| `users.0.name` | `"Alice"` |
| `users.1.age` | `25` |
| `config.debug` | `true` |

## Input Sources

All scripts accept input from:
- **File**: `script.py data.json`
- **Stdin**: `echo '{}' | script.py -`
- **String**: `script.py --string '{"key": "value"}'`

## Common Use Cases

1. **Validate API response**: `validate_json.py response.json`
2. **Pretty-print minified JSON**: `format_json.py api_response.json`
3. **Extract config value**: `query_json.py config.json "database.host"`
4. **Find config differences**: `diff_json.py prod.json staging.json`

## Notes

- All scripts use Python standard library only (no external dependencies)
- Unicode is fully supported
- Large files are handled efficiently
- Exit codes: 0 = success, 1 = error/invalid, 2 = differences found (diff)
