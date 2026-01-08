#!/usr/bin/env python3
"""Find files by pattern, size, or date."""

import argparse
import fnmatch
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path


def parse_size(size_str: str) -> tuple[str, int]:
    """Parse size string like '+1M' or '-100K'.

    Returns:
        Tuple of (operator, bytes)
    """
    match = re.match(r"([+-]?)(\d+)([BKMG]?)", size_str.upper())
    if not match:
        raise ValueError(f"Invalid size format: {size_str}")

    operator = match.group(1) or "="
    number = int(match.group(2))
    suffix = match.group(3) or "B"

    multipliers = {"B": 1, "K": 1024, "M": 1024**2, "G": 1024**3}
    size_bytes = number * multipliers[suffix]

    return operator, size_bytes


def parse_time(time_str: str) -> timedelta:
    """Parse time string like '7d' or '24h'.

    Returns:
        timedelta object
    """
    match = re.match(r"(\d+)([mhdw])", time_str.lower())
    if not match:
        raise ValueError(f"Invalid time format: {time_str}")

    number = int(match.group(1))
    unit = match.group(2)

    units = {"m": "minutes", "h": "hours", "d": "days", "w": "weeks"}
    return timedelta(**{units[unit]: number})


def matches_size(file_path: Path, size_op: str, size_bytes: int) -> bool:
    """Check if file matches size criteria."""
    try:
        file_size = file_path.stat().st_size
        if size_op == "+":
            return file_size > size_bytes
        elif size_op == "-":
            return file_size < size_bytes
        else:
            return file_size == size_bytes
    except OSError:
        return False


def matches_time(file_path: Path, time_delta: timedelta, modified: bool = True) -> bool:
    """Check if file was modified/created within time delta."""
    try:
        stat = file_path.stat()
        if modified:
            file_time = datetime.fromtimestamp(stat.st_mtime)
        else:
            file_time = datetime.fromtimestamp(stat.st_ctime)
        cutoff = datetime.now() - time_delta
        return file_time >= cutoff
    except OSError:
        return False


def find_files(
    root: Path,
    pattern: str = "*",
    size: str = None,
    modified_within: str = None,
    file_type: str = None,
    recursive: bool = True,
    follow_symlinks: bool = True
) -> list[dict]:
    """Find files matching criteria.

    Args:
        root: Starting directory
        pattern: Glob pattern for filename
        size: Size filter (e.g., '+1M', '-100K')
        modified_within: Time filter (e.g., '7d', '24h')
        file_type: 'f' for files, 'd' for directories
        recursive: Search recursively
        follow_symlinks: Follow symbolic links

    Returns:
        List of file info dictionaries
    """
    results = []

    # Parse filters
    size_filter = None
    if size:
        size_filter = parse_size(size)

    time_filter = None
    if modified_within:
        time_filter = parse_time(modified_within)

    # Walk directory
    if recursive:
        walker = root.rglob(pattern)
    else:
        walker = root.glob(pattern)

    for path in walker:
        try:
            if not follow_symlinks and path.is_symlink():
                continue

            # Type filter
            if file_type == "f" and not path.is_file():
                continue
            if file_type == "d" and not path.is_dir():
                continue

            # Size filter
            if size_filter and path.is_file():
                if not matches_size(path, *size_filter):
                    continue

            # Time filter
            if time_filter:
                if not matches_time(path, time_filter):
                    continue

            stat = path.stat()
            results.append({
                "path": str(path),
                "name": path.name,
                "size": stat.st_size if path.is_file() else None,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_file": path.is_file(),
                "is_dir": path.is_dir()
            })
        except (OSError, PermissionError):
            continue

    return results


def format_size(size: int) -> str:
    """Format size in human-readable format."""
    if size is None:
        return "-"
    for unit in ["B", "K", "M", "G"]:
        if size < 1024:
            return f"{size:>7.1f}{unit}"
        size /= 1024
    return f"{size:>7.1f}T"


def main():
    parser = argparse.ArgumentParser(
        description="Find files by pattern, size, or date.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Size format:
  +1M   larger than 1 MB
  -100K smaller than 100 KB
  Suffixes: B, K, M, G

Time format:
  7d    7 days
  24h   24 hours
  30m   30 minutes
  2w    2 weeks

Examples:
  %(prog)s . --pattern "*.py"
  %(prog)s /var/log --pattern "*.log" --size +1M
  %(prog)s . --modified-within 7d
  %(prog)s src --pattern "*.py" --type f
        """
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Starting directory (default: current)"
    )
    parser.add_argument(
        "-p", "--pattern",
        default="*",
        help="Filename pattern (glob syntax, default: *)"
    )
    parser.add_argument(
        "-s", "--size",
        help="Size filter (e.g., +1M, -100K)"
    )
    parser.add_argument(
        "-m", "--modified-within",
        help="Modified within time (e.g., 7d, 24h)"
    )
    parser.add_argument(
        "-t", "--type",
        choices=["f", "d"],
        help="Type: f=file, d=directory"
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Don't search subdirectories"
    )
    parser.add_argument(
        "--no-follow",
        action="store_true",
        help="Don't follow symbolic links"
    )
    parser.add_argument(
        "-l", "--long",
        action="store_true",
        help="Long format (show size and date)"
    )
    parser.add_argument(
        "-0", "--null",
        action="store_true",
        help="Separate output with null characters"
    )

    args = parser.parse_args()

    root = Path(args.path)
    if not root.exists():
        print(f"Error: Path not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    try:
        results = find_files(
            root=root,
            pattern=args.pattern,
            size=args.size,
            modified_within=args.modified_within,
            file_type=args.type,
            recursive=not args.no_recursive,
            follow_symlinks=not args.no_follow
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print("No files found matching criteria.", file=sys.stderr)
        sys.exit(0)

    if args.null:
        for r in results:
            print(r["path"], end="\0")
    elif args.long:
        for r in results:
            size_str = format_size(r["size"])
            mod_date = r["modified"][:10]
            ftype = "d" if r["is_dir"] else "-"
            print(f"{ftype} {size_str} {mod_date} {r['path']}")
    else:
        for r in results:
            print(r["path"])

    print(f"\nFound {len(results)} item(s)", file=sys.stderr)


if __name__ == "__main__":
    main()
