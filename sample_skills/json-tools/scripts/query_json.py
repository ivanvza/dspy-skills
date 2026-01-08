#!/usr/bin/env python3
"""Query JSON data using path expressions."""

import argparse
import json
import sys


def query_json(data: any, path: str) -> dict:
    """Query JSON data using a dot-notation path.

    Args:
        data: Parsed JSON data
        path: Dot-notation path (e.g., "users.0.name")

    Returns:
        Dictionary with query results
    """
    if not path or path == ".":
        return {
            "success": True,
            "path": path,
            "value": data,
            "type": type(data).__name__,
            "error": None
        }

    parts = path.split(".")
    current = data

    for i, part in enumerate(parts):
        current_path = ".".join(parts[:i + 1])

        if isinstance(current, dict):
            if part in current:
                current = current[part]
            else:
                return {
                    "success": False,
                    "path": path,
                    "value": None,
                    "type": None,
                    "error": f"Key '{part}' not found at '{current_path}'"
                }

        elif isinstance(current, list):
            try:
                index = int(part)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return {
                        "success": False,
                        "path": path,
                        "value": None,
                        "type": None,
                        "error": f"Index {index} out of range at '{current_path}' (list has {len(current)} items)"
                    }
            except ValueError:
                return {
                    "success": False,
                    "path": path,
                    "value": None,
                    "type": None,
                    "error": f"Expected integer index but got '{part}' at '{current_path}'"
                }
        else:
            return {
                "success": False,
                "path": path,
                "value": None,
                "type": None,
                "error": f"Cannot access '{part}' on {type(current).__name__} at '{'.'.join(parts[:i])}'"
            }

    return {
        "success": True,
        "path": path,
        "value": current,
        "type": type(current).__name__,
        "error": None
    }


def list_keys(data: any, path: str = "") -> list:
    """List available keys/indices at a path."""
    if path and path != ".":
        result = query_json(data, path)
        if not result["success"]:
            return []
        data = result["value"]

    if isinstance(data, dict):
        return list(data.keys())
    elif isinstance(data, list):
        return [str(i) for i in range(len(data))]
    else:
        return []


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
        description="Query JSON data using path expressions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Path syntax:
  key           - Access object key
  0, 1, 2       - Access array index
  key.subkey    - Nested access
  items.0.name  - Mixed access
  . (or empty)  - Root element

Examples:
  %(prog)s data.json "users"
  %(prog)s data.json "users.0.name"
  %(prog)s data.json "config.database.host"
  %(prog)s data.json --keys
  %(prog)s data.json "users" --keys
  echo '{"a":1}' | %(prog)s - "a"
        """
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="JSON file to query (use '-' for stdin)"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path expression (default: root)"
    )
    parser.add_argument(
        "-s", "--string",
        help="Query JSON from string instead of file"
    )
    parser.add_argument(
        "-k", "--keys",
        action="store_true",
        help="List available keys/indices at path"
    )
    parser.add_argument(
        "-r", "--raw",
        action="store_true",
        help="Output raw value (no JSON formatting for strings)"
    )
    parser.add_argument(
        "-c", "--compact",
        action="store_true",
        help="Output compact JSON"
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

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON - {e}", file=sys.stderr)
        sys.exit(1)

    if args.keys:
        keys = list_keys(data, args.path)
        if keys:
            for key in keys:
                print(key)
        else:
            print("(no keys available)", file=sys.stderr)
        sys.exit(0)

    result = query_json(data, args.path)

    if not result["success"]:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    value = result["value"]

    if args.raw and isinstance(value, str):
        print(value)
    elif args.compact:
        print(json.dumps(value, separators=(",", ":")))
    else:
        if isinstance(value, (dict, list)):
            print(json.dumps(value, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(value))


if __name__ == "__main__":
    main()
