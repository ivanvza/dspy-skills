#!/usr/bin/env python3
"""Compare two files and show differences."""

import argparse
import difflib
import hashlib
import sys
from pathlib import Path


def files_identical(file1: Path, file2: Path) -> bool:
    """Check if two files are byte-for-byte identical."""
    if file1.stat().st_size != file2.stat().st_size:
        return False

    with open(file1, "rb") as f1, open(file2, "rb") as f2:
        while True:
            chunk1 = f1.read(8192)
            chunk2 = f2.read(8192)
            if chunk1 != chunk2:
                return False
            if not chunk1:
                return True


def compare_binary(file1: Path, file2: Path) -> dict:
    """Compare two binary files."""
    size1 = file1.stat().st_size
    size2 = file2.stat().st_size

    # Calculate checksums
    def get_hash(path):
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    hash1 = get_hash(file1)
    hash2 = get_hash(file2)

    identical = hash1 == hash2

    return {
        "identical": identical,
        "file1": {
            "path": str(file1),
            "size": size1,
            "md5": hash1
        },
        "file2": {
            "path": str(file2),
            "size": size2,
            "md5": hash2
        },
        "size_diff": size2 - size1
    }


def compare_text(
    file1: Path,
    file2: Path,
    context: int = 3,
    unified: bool = False
) -> dict:
    """Compare two text files."""
    try:
        with open(file1, "r", encoding="utf-8", errors="replace") as f:
            lines1 = f.readlines()
        with open(file2, "r", encoding="utf-8", errors="replace") as f:
            lines2 = f.readlines()
    except Exception as e:
        return {"success": False, "error": str(e)}

    if unified:
        diff = list(difflib.unified_diff(
            lines1, lines2,
            fromfile=str(file1),
            tofile=str(file2),
            n=context
        ))
    else:
        diff = list(difflib.context_diff(
            lines1, lines2,
            fromfile=str(file1),
            tofile=str(file2),
            n=context
        ))

    # Count changes
    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

    return {
        "success": True,
        "identical": len(diff) == 0,
        "file1": {
            "path": str(file1),
            "lines": len(lines1)
        },
        "file2": {
            "path": str(file2),
            "lines": len(lines2)
        },
        "diff": diff,
        "added": added,
        "removed": removed,
        "changed": (added + removed) // 2 if added == removed else max(added, removed)
    }


def main():
    parser = argparse.ArgumentParser(
        description="Compare two files and show differences.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s old.txt new.txt
  %(prog)s file1.bin file2.bin --binary
  %(prog)s config1.yaml config2.yaml --unified
  %(prog)s before.py after.py --context 5
        """
    )
    parser.add_argument("file1", help="First file")
    parser.add_argument("file2", help="Second file")
    parser.add_argument(
        "-b", "--binary",
        action="store_true",
        help="Compare as binary files"
    )
    parser.add_argument(
        "-u", "--unified",
        action="store_true",
        help="Use unified diff format"
    )
    parser.add_argument(
        "-c", "--context",
        type=int,
        default=3,
        help="Lines of context (default: 3)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Only report if files differ"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )

    args = parser.parse_args()

    file1 = Path(args.file1)
    file2 = Path(args.file2)

    if not file1.exists():
        print(f"Error: File not found: {args.file1}", file=sys.stderr)
        sys.exit(1)
    if not file2.exists():
        print(f"Error: File not found: {args.file2}", file=sys.stderr)
        sys.exit(1)

    # Colors for terminal output
    if args.no_color or not sys.stdout.isatty():
        RED = GREEN = RESET = CYAN = ""
    else:
        RED = "\033[91m"
        GREEN = "\033[92m"
        CYAN = "\033[96m"
        RESET = "\033[0m"

    if args.binary:
        result = compare_binary(file1, file2)

        if args.quiet:
            sys.exit(0 if result["identical"] else 1)

        if result["identical"]:
            print(f"Files are identical (MD5: {result['file1']['md5']})")
            sys.exit(0)
        else:
            print(f"Files differ:")
            print(f"  {result['file1']['path']}:")
            print(f"    Size: {result['file1']['size']} bytes")
            print(f"    MD5:  {result['file1']['md5']}")
            print(f"  {result['file2']['path']}:")
            print(f"    Size: {result['file2']['size']} bytes")
            print(f"    MD5:  {result['file2']['md5']}")
            if result["size_diff"] != 0:
                sign = "+" if result["size_diff"] > 0 else ""
                print(f"  Size difference: {sign}{result['size_diff']} bytes")
            sys.exit(1)

    else:
        result = compare_text(file1, file2, context=args.context, unified=args.unified)

        if not result["success"]:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(2)

        if args.quiet:
            sys.exit(0 if result["identical"] else 1)

        if result["identical"]:
            print(f"Files are identical ({result['file1']['lines']} lines)")
            sys.exit(0)

        print(f"Files differ:")
        print(f"  {result['file1']['path']}: {result['file1']['lines']} lines")
        print(f"  {result['file2']['path']}: {result['file2']['lines']} lines")
        print(f"  Changes: +{result['added']} -{result['removed']}")
        print()

        for line in result["diff"]:
            if line.startswith("+"):
                print(f"{GREEN}{line}{RESET}", end="")
            elif line.startswith("-"):
                print(f"{RED}{line}{RESET}", end="")
            elif line.startswith("@") or line.startswith("*"):
                print(f"{CYAN}{line}{RESET}", end="")
            else:
                print(line, end="")

        sys.exit(1)


if __name__ == "__main__":
    main()
