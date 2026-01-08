#!/usr/bin/env python3
"""Validate JSON syntax."""

import argparse
import json
import sys


def validate_json(content: str) -> dict:
    """Validate JSON content.

    Args:
        content: JSON string to validate

    Returns:
        Dictionary with validation results
    """
    try:
        data = json.loads(content)

        # Gather statistics
        stats = analyze_json(data)

        return {
            "valid": True,
            "data": data,
            "stats": stats,
            "error": None,
            "error_position": None
        }
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "data": None,
            "stats": None,
            "error": str(e),
            "error_position": {
                "line": e.lineno,
                "column": e.colno,
                "char": e.pos
            }
        }


def analyze_json(data, depth=0) -> dict:
    """Analyze JSON structure and return statistics."""
    stats = {
        "type": type(data).__name__,
        "depth": depth
    }

    if isinstance(data, dict):
        stats["keys"] = len(data)
        stats["max_depth"] = depth
        for value in data.values():
            child_stats = analyze_json(value, depth + 1)
            stats["max_depth"] = max(stats["max_depth"], child_stats.get("max_depth", depth))
    elif isinstance(data, list):
        stats["items"] = len(data)
        stats["max_depth"] = depth
        for item in data:
            child_stats = analyze_json(item, depth + 1)
            stats["max_depth"] = max(stats["max_depth"], child_stats.get("max_depth", depth))
    elif isinstance(data, str):
        stats["length"] = len(data)
    elif isinstance(data, (int, float)):
        stats["value"] = data
    elif data is None:
        stats["value"] = None
    elif isinstance(data, bool):
        stats["value"] = data

    return stats


def get_input(args) -> tuple[str, str]:
    """Get input content and source name."""
    if args.string:
        return args.string, "<string>"
    elif args.file == "-":
        return sys.stdin.read(), "<stdin>"
    else:
        with open(args.file, "r", encoding="utf-8") as f:
            return f.read(), args.file


def main():
    parser = argparse.ArgumentParser(
        description="Validate JSON syntax.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data.json
  %(prog)s data.json --stats
  echo '{"key": "value"}' | %(prog)s -
  %(prog)s --string '{"valid": true}'
        """
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="JSON file to validate (use '-' for stdin)"
    )
    parser.add_argument(
        "-s", "--string",
        help="Validate JSON from string instead of file"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics about the JSON structure"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Only exit with status code, no output"
    )

    args = parser.parse_args()

    try:
        content, source = get_input(args)
    except FileNotFoundError:
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(1)

    result = validate_json(content)

    if args.quiet:
        sys.exit(0 if result["valid"] else 1)

    if result["valid"]:
        print(f"✓ Valid JSON ({source})")

        if args.stats and result["stats"]:
            stats = result["stats"]
            print(f"\nStructure:")
            print(f"  Root type: {stats['type']}")
            if stats["type"] == "dict":
                print(f"  Keys: {stats.get('keys', 0)}")
            elif stats["type"] == "list":
                print(f"  Items: {stats.get('items', 0)}")
            print(f"  Max depth: {stats.get('max_depth', 0)}")
            print(f"  Size: {len(content)} chars")

        sys.exit(0)
    else:
        print(f"✗ Invalid JSON ({source})")
        print(f"\nError: {result['error']}")

        if result["error_position"]:
            pos = result["error_position"]
            print(f"Location: line {pos['line']}, column {pos['column']}")

            # Show context around error
            lines = content.split("\n")
            if 0 < pos["line"] <= len(lines):
                print(f"\nContext:")
                line_num = pos["line"]
                if line_num > 1:
                    print(f"  {line_num - 1}: {lines[line_num - 2]}")
                print(f"→ {line_num}: {lines[line_num - 1]}")
                print(f"  {' ' * (pos['column'] + 2)}^")
                if line_num < len(lines):
                    print(f"  {line_num + 1}: {lines[line_num]}")

        sys.exit(1)


if __name__ == "__main__":
    main()
