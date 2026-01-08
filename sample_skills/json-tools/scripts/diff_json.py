#!/usr/bin/env python3
"""Compare two JSON files and show differences."""

import argparse
import json
import sys


def diff_json(data1: any, data2: any, path: str = "") -> list:
    """Compare two JSON structures and return differences.

    Args:
        data1: First JSON data
        data2: Second JSON data
        path: Current path (for nested comparisons)

    Returns:
        List of difference dictionaries
    """
    differences = []

    if type(data1) != type(data2):
        differences.append({
            "path": path or "(root)",
            "type": "type_change",
            "old": {"type": type(data1).__name__, "value": data1},
            "new": {"type": type(data2).__name__, "value": data2}
        })
        return differences

    if isinstance(data1, dict):
        all_keys = set(data1.keys()) | set(data2.keys())

        for key in sorted(all_keys):
            key_path = f"{path}.{key}" if path else key

            if key not in data1:
                differences.append({
                    "path": key_path,
                    "type": "added",
                    "value": data2[key]
                })
            elif key not in data2:
                differences.append({
                    "path": key_path,
                    "type": "removed",
                    "value": data1[key]
                })
            else:
                differences.extend(diff_json(data1[key], data2[key], key_path))

    elif isinstance(data1, list):
        max_len = max(len(data1), len(data2))

        for i in range(max_len):
            item_path = f"{path}.{i}" if path else str(i)

            if i >= len(data1):
                differences.append({
                    "path": item_path,
                    "type": "added",
                    "value": data2[i]
                })
            elif i >= len(data2):
                differences.append({
                    "path": item_path,
                    "type": "removed",
                    "value": data1[i]
                })
            else:
                differences.extend(diff_json(data1[i], data2[i], item_path))

    else:
        if data1 != data2:
            differences.append({
                "path": path or "(root)",
                "type": "changed",
                "old": data1,
                "new": data2
            })

    return differences


def format_value(value: any, max_length: int = 50) -> str:
    """Format a value for display."""
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, str):
        if len(value) > max_length:
            return f'"{value[:max_length]}..."'
        return f'"{value}"'
    elif isinstance(value, (dict, list)):
        s = json.dumps(value)
        if len(s) > max_length:
            return f"{s[:max_length]}..."
        return s
    else:
        return str(value)


def main():
    parser = argparse.ArgumentParser(
        description="Compare two JSON files and show differences.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s old.json new.json
  %(prog)s config1.json config2.json --keys-only
  %(prog)s file1.json file2.json --json
  %(prog)s file1.json file2.json --quiet
        """
    )
    parser.add_argument("file1", help="First JSON file")
    parser.add_argument("file2", help="Second JSON file")
    parser.add_argument(
        "-k", "--keys-only",
        action="store_true",
        help="Only show paths that differ, not values"
    )
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output differences as JSON"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Only exit with status code"
    )
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="Ignore paths matching pattern (can be repeated)"
    )

    args = parser.parse_args()

    # Load files
    try:
        with open(args.file1, "r", encoding="utf-8") as f:
            data1 = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {args.file1}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.file1}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.file2, "r", encoding="utf-8") as f:
            data2 = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {args.file2}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {args.file2}: {e}", file=sys.stderr)
        sys.exit(1)

    # Compare
    differences = diff_json(data1, data2)

    # Filter ignored paths
    if args.ignore:
        import re
        patterns = [re.compile(p) for p in args.ignore]
        differences = [
            d for d in differences
            if not any(p.search(d["path"]) for p in patterns)
        ]

    # Output
    if args.quiet:
        sys.exit(0 if not differences else 2)

    if not differences:
        print(f"No differences found between {args.file1} and {args.file2}")
        sys.exit(0)

    if args.json:
        print(json.dumps(differences, indent=2))
        sys.exit(2)

    print(f"Found {len(differences)} difference(s):")
    print(f"  {args.file1} (old)")
    print(f"  {args.file2} (new)")
    print("-" * 60)

    for diff in differences:
        path = diff["path"]
        diff_type = diff["type"]

        if diff_type == "added":
            symbol = "+"
            if args.keys_only:
                print(f"{symbol} {path}")
            else:
                print(f"{symbol} {path}: {format_value(diff['value'])}")

        elif diff_type == "removed":
            symbol = "-"
            if args.keys_only:
                print(f"{symbol} {path}")
            else:
                print(f"{symbol} {path}: {format_value(diff['value'])}")

        elif diff_type == "changed":
            symbol = "~"
            if args.keys_only:
                print(f"{symbol} {path}")
            else:
                print(f"{symbol} {path}:")
                print(f"    old: {format_value(diff['old'])}")
                print(f"    new: {format_value(diff['new'])}")

        elif diff_type == "type_change":
            symbol = "!"
            if args.keys_only:
                print(f"{symbol} {path}")
            else:
                print(f"{symbol} {path}: type changed")
                print(f"    old ({diff['old']['type']}): {format_value(diff['old']['value'])}")
                print(f"    new ({diff['new']['type']}): {format_value(diff['new']['value'])}")

    sys.exit(2)


if __name__ == "__main__":
    main()
