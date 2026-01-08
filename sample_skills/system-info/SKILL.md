---
name: system-info
description: System information toolkit for gathering CPU, memory, disk, and process information. Use when diagnosing system performance, checking resource usage, monitoring processes, or troubleshooting system issues.
license: MIT
compatibility: Works best on Linux. Some features may be limited on macOS/Windows.
metadata:
  author: dspy-skills
  version: "1.0"
---

# System Information

A toolkit for gathering system information using Python.

## When to Use This Skill

Activate this skill when the user needs to:
- Check CPU usage and information
- Monitor memory usage
- View disk space and partitions
- List running processes
- Diagnose system performance issues

## Requirements

For full functionality, install psutil:
```bash
pip install psutil
```

Scripts will gracefully degrade to use standard library methods if psutil is not available.

## Available Scripts

**Always run scripts with `--help` first** to see all available options.

| Script | Purpose |
|--------|---------|
| `cpu_info.py` | CPU usage and information |
| `memory_info.py` | Memory usage statistics |
| `disk_info.py` | Disk usage and partitions |
| `process_list.py` | List running processes |

## Decision Tree

```
Task → What do you need?
    │
    ├─ CPU information/usage?
    │   └─ Use: cpu_info.py
    │
    ├─ Memory usage?
    │   └─ Use: memory_info.py
    │
    ├─ Disk space?
    │   └─ Use: disk_info.py
    │
    └─ Process information?
        └─ Use: process_list.py
```

## Quick Examples

**CPU information:**
```bash
python scripts/cpu_info.py
python scripts/cpu_info.py --watch 2  # Update every 2 seconds
```

**Memory usage:**
```bash
python scripts/memory_info.py
python scripts/memory_info.py --human
```

**Disk information:**
```bash
python scripts/disk_info.py
python scripts/disk_info.py --all  # Include all filesystems
```

**Process list:**
```bash
python scripts/process_list.py
python scripts/process_list.py --sort cpu
python scripts/process_list.py --filter python
```

## Common Use Cases

1. **Check if system is overloaded**: `cpu_info.py` + `memory_info.py`
2. **Find memory-hungry processes**: `process_list.py --sort memory`
3. **Check available disk space**: `disk_info.py`
4. **Find process by name**: `process_list.py --filter nginx`
5. **Monitor system in real-time**: `cpu_info.py --watch 1`

## Output Formats

Most scripts support:
- **Human-readable** (default): Formatted output with units
- **JSON** (`--json`): Machine-readable JSON format
- **Compact** (`--compact`): Minimal output

## Platform Notes

- **Linux**: Full functionality
- **macOS**: Most features work, some Linux-specific info unavailable
- **Windows**: Basic functionality, some features may differ

## Notes

- Scripts attempt to use psutil for accurate information
- Without psutil, fallback to /proc filesystem (Linux) or system commands
- Resource monitoring may require appropriate permissions
- Watch mode (`--watch`) runs until interrupted with Ctrl+C
