#!/usr/bin/env python3
"""Get detailed file information."""

import argparse
import hashlib
import mimetypes
import os
import stat
import sys
from datetime import datetime
from pathlib import Path


def detect_encoding(file_path: Path, sample_size: int = 8192) -> str:
    """Attempt to detect file encoding."""
    try:
        with open(file_path, "rb") as f:
            sample = f.read(sample_size)

        # Check for BOM
        if sample.startswith(b"\xef\xbb\xbf"):
            return "utf-8-sig"
        if sample.startswith(b"\xff\xfe"):
            return "utf-16-le"
        if sample.startswith(b"\xfe\xff"):
            return "utf-16-be"

        # Try UTF-8
        try:
            sample.decode("utf-8")
            return "utf-8"
        except UnicodeDecodeError:
            pass

        # Try Latin-1 (always succeeds, but may not be correct)
        return "latin-1"

    except Exception:
        return "unknown"


def is_binary(file_path: Path, sample_size: int = 8192) -> bool:
    """Check if file appears to be binary."""
    try:
        with open(file_path, "rb") as f:
            sample = f.read(sample_size)
        # Check for null bytes
        return b"\x00" in sample
    except Exception:
        return False


def calculate_checksum(file_path: Path, algorithm: str = "md5") -> str:
    """Calculate file checksum."""
    hash_func = getattr(hashlib, algorithm)()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def format_size(size: int) -> str:
    """Format size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def format_permissions(mode: int) -> str:
    """Format file permissions in rwx format."""
    perms = ""
    for who in ["USR", "GRP", "OTH"]:
        for what in ["R", "W", "X"]:
            perm = getattr(stat, f"S_I{what}{who}")
            perms += what.lower() if mode & perm else "-"
    return perms


def get_file_stats(file_path: Path, calculate_hash: bool = False) -> dict:
    """Get detailed file statistics.

    Args:
        file_path: Path to the file
        calculate_hash: Whether to calculate checksums

    Returns:
        Dictionary with file statistics
    """
    if not file_path.exists():
        return {"success": False, "error": "File not found"}

    try:
        file_stat = file_path.stat()
        is_file = file_path.is_file()
        is_dir = file_path.is_dir()
        is_link = file_path.is_symlink()

        result = {
            "success": True,
            "path": str(file_path.absolute()),
            "name": file_path.name,
            "type": "directory" if is_dir else ("symlink" if is_link else "file"),
            "size": file_stat.st_size,
            "size_human": format_size(file_stat.st_size),
            "permissions": format_permissions(file_stat.st_mode),
            "permissions_octal": oct(file_stat.st_mode)[-3:],
            "owner_uid": file_stat.st_uid,
            "group_gid": file_stat.st_gid,
            "created": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            "accessed": datetime.fromtimestamp(file_stat.st_atime).isoformat(),
        }

        if is_file:
            mime_type, _ = mimetypes.guess_type(str(file_path))
            result["mime_type"] = mime_type or "application/octet-stream"
            result["is_binary"] = is_binary(file_path)

            if not result["is_binary"]:
                result["encoding"] = detect_encoding(file_path)

                # Count lines for text files
                try:
                    with open(file_path, "r", encoding=result["encoding"], errors="replace") as f:
                        result["lines"] = sum(1 for _ in f)
                except Exception:
                    pass

            if calculate_hash:
                result["md5"] = calculate_checksum(file_path, "md5")
                result["sha256"] = calculate_checksum(file_path, "sha256")

        if is_link:
            result["link_target"] = str(file_path.resolve())

        return result

    except PermissionError:
        return {"success": False, "error": "Permission denied"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Get detailed file information.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.txt
  %(prog)s image.png --checksum
  %(prog)s /var/log/syslog
  %(prog)s mydir/
        """
    )
    parser.add_argument(
        "file",
        help="File or directory to analyze"
    )
    parser.add_argument(
        "-c", "--checksum",
        action="store_true",
        help="Calculate MD5 and SHA256 checksums"
    )
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    file_path = Path(args.file)

    if not file_path.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    result = get_file_stats(file_path, calculate_hash=args.checksum)

    if not result["success"]:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        print(f"File: {result['name']}")
        print(f"Path: {result['path']}")
        print(f"Type: {result['type']}")
        print(f"Size: {result['size_human']} ({result['size']} bytes)")
        print(f"Permissions: {result['permissions']} ({result['permissions_octal']})")
        print(f"Modified: {result['modified']}")
        print(f"Created: {result['created']}")

        if result["type"] == "file":
            print(f"MIME type: {result.get('mime_type', 'unknown')}")
            print(f"Binary: {'Yes' if result.get('is_binary') else 'No'}")

            if not result.get("is_binary"):
                print(f"Encoding: {result.get('encoding', 'unknown')}")
                if "lines" in result:
                    print(f"Lines: {result['lines']}")

            if "md5" in result:
                print(f"MD5: {result['md5']}")
                print(f"SHA256: {result['sha256']}")

        if result["type"] == "symlink":
            print(f"Target: {result.get('link_target', 'unknown')}")


if __name__ == "__main__":
    main()
