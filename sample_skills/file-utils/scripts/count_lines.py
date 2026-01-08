#!/usr/bin/env python3
"""Count lines in files."""

import argparse
import os
import re
import sys
from pathlib import Path


def count_lines(
    file_path: Path,
    match_pattern: str = None,
    exclude_blank: bool = False,
    exclude_comments: str = None
) -> dict:
    """Count lines in a file.

    Args:
        file_path: Path to the file
        match_pattern: Only count lines matching this regex
        exclude_blank: Exclude blank lines
        exclude_comments: Comment prefix to exclude (e.g., '#', '//')

    Returns:
        Dictionary with count results
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        return {
            "success": False,
            "file": str(file_path),
            "error": str(e)
        }

    total = len(lines)
    counted = 0
    blank = 0
    comments = 0

    pattern = re.compile(match_pattern) if match_pattern else None

    for line in lines:
        stripped = line.strip()

        # Count blanks
        if not stripped:
            blank += 1
            if exclude_blank:
                continue

        # Count comments
        if exclude_comments and stripped.startswith(exclude_comments):
            comments += 1
            continue

        # Pattern matching
        if pattern:
            if pattern.search(line):
                counted += 1
        else:
            counted += 1

    return {
        "success": True,
        "file": str(file_path),
        "total": total,
        "counted": counted,
        "blank": blank,
        "comments": comments,
        "error": None
    }


def find_files_by_pattern(root: Path, pattern: str) -> list[Path]:
    """Find files matching glob pattern."""
    return list(root.rglob(pattern))


def main():
    parser = argparse.ArgumentParser(
        description="Count lines in files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s myfile.txt
  %(prog)s src/ --pattern "*.py"
  %(prog)s code.py --match "TODO"
  %(prog)s src/ --pattern "*.py" --no-blank --comments "#"
  %(prog)s . --pattern "*.py" --total
        """
    )
    parser.add_argument(
        "path",
        help="File or directory to count"
    )
    parser.add_argument(
        "-p", "--pattern",
        help="Glob pattern for files (when path is directory)"
    )
    parser.add_argument(
        "-m", "--match",
        help="Only count lines matching regex pattern"
    )
    parser.add_argument(
        "-b", "--no-blank",
        action="store_true",
        help="Exclude blank lines from count"
    )
    parser.add_argument(
        "-c", "--comments",
        help="Comment prefix to exclude (e.g., '#', '//')"
    )
    parser.add_argument(
        "-t", "--total",
        action="store_true",
        help="Show total only (for multiple files)"
    )
    parser.add_argument(
        "-s", "--sort",
        choices=["name", "lines", "none"],
        default="none",
        help="Sort output (default: none)"
    )

    args = parser.parse_args()

    path = Path(args.path)

    if not path.exists():
        print(f"Error: Path not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    # Get file list
    if path.is_file():
        files = [path]
    elif path.is_dir():
        if args.pattern:
            files = find_files_by_pattern(path, args.pattern)
        else:
            files = [f for f in path.iterdir() if f.is_file()]
    else:
        print(f"Error: Not a file or directory: {args.path}", file=sys.stderr)
        sys.exit(1)

    if not files:
        print("No files found.", file=sys.stderr)
        sys.exit(0)

    results = []
    grand_total = 0
    grand_blank = 0
    grand_comments = 0

    for file_path in files:
        result = count_lines(
            file_path,
            match_pattern=args.match,
            exclude_blank=args.no_blank,
            exclude_comments=args.comments
        )

        if result["success"]:
            results.append(result)
            grand_total += result["counted"]
            grand_blank += result["blank"]
            grand_comments += result["comments"]
        else:
            print(f"Warning: {result['file']}: {result['error']}", file=sys.stderr)

    if not results:
        print("No files could be processed.", file=sys.stderr)
        sys.exit(1)

    # Sort results
    if args.sort == "name":
        results.sort(key=lambda r: r["file"])
    elif args.sort == "lines":
        results.sort(key=lambda r: r["counted"], reverse=True)

    # Output
    if args.total and len(results) > 1:
        print(f"Total: {grand_total} lines in {len(results)} files")
        if args.no_blank:
            print(f"  (excluded {grand_blank} blank lines)")
        if args.comments:
            print(f"  (excluded {grand_comments} comment lines)")
    else:
        max_width = max(len(r["file"]) for r in results)

        for result in results:
            if len(results) == 1:
                print(f"File: {result['file']}")
                print(f"Lines: {result['counted']}")
                if result["blank"] > 0:
                    print(f"Blank: {result['blank']}")
                if result["comments"] > 0:
                    print(f"Comments: {result['comments']}")
            else:
                print(f"{result['counted']:>8}  {result['file']}")

        if len(results) > 1:
            print("-" * (max_width + 10))
            print(f"{grand_total:>8}  total")


if __name__ == "__main__":
    main()
