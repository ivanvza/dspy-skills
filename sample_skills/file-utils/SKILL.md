---
name: file-utils
description: File utility toolkit for searching, analyzing, and comparing files. Find files by pattern/size/date, count lines, get file statistics, and compare file contents. Use when working with file discovery, analysis, or comparison tasks.
metadata:
  author: dspy-skills
  version: "1.0"
allowed-tools: Bash(ls:*)
---

# File Utilities

A toolkit for common file operations using Python standard library only.

## When to Use This Skill

Activate this skill when the user needs to:
- Find files matching certain criteria (pattern, size, date)
- Count lines in files (with optional pattern matching)
- Get detailed file information (size, type, encoding)
- Compare two files (text or binary)

## Available Scripts

**Always run scripts with `--help` first** to see all available options.

| Script | Purpose |
|--------|---------|
| `find_files.py` | Find files by pattern, size, or date |
| `count_lines.py` | Count lines in files |
| `file_stats.py` | Get detailed file information |
| `compare_files.py` | Compare two files |

## Decision Tree

```
Task → What do you need?
    │
    ├─ Find files matching criteria?
    │   └─ Use: find_files.py <path> --pattern "*.py"
    │
    ├─ Count lines (or matches)?
    │   └─ Use: count_lines.py <file>
    │
    ├─ Get file information?
    │   └─ Use: file_stats.py <file>
    │
    └─ Compare two files?
        └─ Use: compare_files.py <file1> <file2>
```

## Quick Examples

**Find files:**
```bash
python scripts/find_files.py . --pattern "*.py"
python scripts/find_files.py /var/log --pattern "*.log" --size +1M
python scripts/find_files.py . --modified-within 7d
```

**Count lines:**
```bash
python scripts/count_lines.py myfile.txt
python scripts/count_lines.py src/ --pattern "*.py" --total
python scripts/count_lines.py code.py --match "TODO"
```

**File statistics:**
```bash
python scripts/file_stats.py document.txt
python scripts/file_stats.py image.png --checksum
```

**Compare files:**
```bash
python scripts/compare_files.py old.txt new.txt
python scripts/compare_files.py file1.bin file2.bin --binary
python scripts/compare_files.py config1.yaml config2.yaml --unified
```

## Size Suffixes

For `find_files.py --size`:
- `B` or no suffix: bytes
- `K`: kilobytes (1024 bytes)
- `M`: megabytes
- `G`: gigabytes

Prefixes:
- `+1M`: larger than 1 MB
- `-100K`: smaller than 100 KB
- `1M`: exactly 1 MB (rarely used)

## Time Formats

For `find_files.py` time filters:
- `7d`: 7 days
- `24h`: 24 hours
- `30m`: 30 minutes
- `2w`: 2 weeks

## Common Use Cases

1. **Find large log files**: `find_files.py /var/log --pattern "*.log" --size +100M`
2. **Count code lines**: `count_lines.py src/ --pattern "*.py" --total`
3. **Find recently modified**: `find_files.py . --modified-within 1d`
4. **Check file encoding**: `file_stats.py data.csv`
5. **Compare configs**: `compare_files.py old.conf new.conf`

## Notes

- All scripts use Python standard library only (no external dependencies)
- Handles both text and binary files appropriately
- Encoding detection is best-effort for text files
- Symbolic links are followed by default
