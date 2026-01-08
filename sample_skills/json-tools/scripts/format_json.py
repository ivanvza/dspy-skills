#!/usr/bin/env python3
"""Format (pretty-print or minify) JSON."""

import argparse
import json
import sys


def format_json(
    content: str,
    indent: int = 2,
    minify: bool = False,
    sort_keys: bool = False
) -> dict:
    """Format JSON content.

    Args:
        content: JSON string to format
        indent: Indentation level (ignored if minify=True)
        minify: If True, output compact JSON
        sort_keys: If True, sort object keys alphabetically

    Returns:
        Dictionary with formatting results
    """
    try:
        data = json.loads(content)

        if minify:
            formatted = json.dumps(data, separators=(",", ":"), sort_keys=sort_keys)
        else:
            formatted = json.dumps(
                data,
                indent=indent,
                sort_keys=sort_keys,
                ensure_ascii=False
            )

        return {
            "success": True,
            "formatted": formatted,
            "original_size": len(content),
            "formatted_size": len(formatted),
            "error": None
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "formatted": None,
            "error": str(e)
        }


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
        description="Format (pretty-print or minify) JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s data.json
  %(prog)s data.json --indent 4
  %(prog)s data.json --minify
  %(prog)s data.json --sort-keys
  %(prog)s data.json --output formatted.json
  echo '{"b":2,"a":1}' | %(prog)s - --sort-keys
        """
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="JSON file to format (use '-' for stdin)"
    )
    parser.add_argument(
        "-s", "--string",
        help="Format JSON from string instead of file"
    )
    parser.add_argument(
        "-i", "--indent",
        type=int,
        default=2,
        help="Indentation spaces (default: 2)"
    )
    parser.add_argument(
        "-m", "--minify",
        action="store_true",
        help="Output compact JSON (no whitespace)"
    )
    parser.add_argument(
        "--sort-keys",
        action="store_true",
        help="Sort object keys alphabetically"
    )
    parser.add_argument(
        "-o", "--output",
        help="Write output to file instead of stdout"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show size comparison"
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

    result = format_json(
        content,
        indent=args.indent,
        minify=args.minify,
        sort_keys=args.sort_keys
    )

    if not result["success"]:
        print(f"Error: Invalid JSON - {result['error']}", file=sys.stderr)
        sys.exit(1)

    if args.stats:
        orig = result["original_size"]
        fmt = result["formatted_size"]
        diff = fmt - orig
        pct = (diff / orig * 100) if orig > 0 else 0
        sign = "+" if diff > 0 else ""
        print(f"Original: {orig} chars", file=sys.stderr)
        print(f"Formatted: {fmt} chars ({sign}{diff}, {sign}{pct:.1f}%)", file=sys.stderr)
        print("-" * 40, file=sys.stderr)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result["formatted"])
        print(f"Output written to: {args.output}", file=sys.stderr)
    else:
        print(result["formatted"])


if __name__ == "__main__":
    main()
