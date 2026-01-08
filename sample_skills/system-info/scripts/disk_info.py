#!/usr/bin/env python3
"""Get disk usage and partition information."""

import argparse
import json
import os
import sys

# Try to import psutil for better information
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def format_bytes(bytes_val: int, human: bool = True) -> str:
    """Format bytes in human-readable format."""
    if not human:
        return str(bytes_val)

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"


def get_disk_usage(path: str = "/") -> dict:
    """Get disk usage for a specific path."""
    try:
        stat = os.statvfs(path)
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bfree * stat.f_frsize
        available = stat.f_bavail * stat.f_frsize
        used = total - free

        return {
            "path": path,
            "total": total,
            "used": used,
            "free": free,
            "available": available,
            "percent": round((used / total) * 100, 1) if total > 0 else 0
        }
    except Exception as e:
        return {
            "path": path,
            "error": str(e)
        }


def get_partitions_psutil(include_all: bool = False) -> list:
    """Get partition information using psutil."""
    partitions = []

    for part in psutil.disk_partitions(all=include_all):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "opts": part.opts,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent
            })
        except (PermissionError, OSError):
            partitions.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "opts": part.opts,
                "error": "Permission denied or inaccessible"
            })

    return partitions


def get_partitions_proc(include_all: bool = False) -> list:
    """Get partition information from /proc/mounts (Linux fallback)."""
    partitions = []

    try:
        with open("/proc/mounts", "r") as f:
            for line in f:
                parts = line.split()
                device = parts[0]
                mountpoint = parts[1]
                fstype = parts[2]
                opts = parts[3]

                # Skip virtual filesystems unless include_all
                if not include_all:
                    if fstype in ["proc", "sysfs", "devtmpfs", "devpts", "tmpfs",
                                   "securityfs", "cgroup", "cgroup2", "pstore",
                                   "debugfs", "tracefs", "hugetlbfs", "mqueue",
                                   "fusectl", "configfs", "fuse.gvfsd-fuse"]:
                        continue
                    if device.startswith("/dev/loop"):
                        continue

                usage = get_disk_usage(mountpoint)
                partitions.append({
                    "device": device,
                    "mountpoint": mountpoint,
                    "fstype": fstype,
                    "opts": opts,
                    **{k: v for k, v in usage.items() if k != "path"}
                })

    except Exception as e:
        return [{"error": str(e)}]

    return partitions


def get_partitions(include_all: bool = False) -> list:
    """Get partition information."""
    if HAS_PSUTIL:
        return get_partitions_psutil(include_all)
    else:
        return get_partitions_proc(include_all)


def main():
    parser = argparse.ArgumentParser(
        description="Get disk usage and partition information.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --all
  %(prog)s --path /home
  %(prog)s --json
        """
    )
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="Include all filesystems (including virtual)"
    )
    parser.add_argument(
        "-p", "--path",
        help="Show usage for specific path only"
    )
    parser.add_argument(
        "-H", "--human",
        action="store_true",
        default=True,
        help="Show sizes in human-readable format (default)"
    )
    parser.add_argument(
        "-b", "--bytes",
        action="store_true",
        help="Show all values in bytes"
    )
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    human = not args.bytes

    if args.path:
        data = get_disk_usage(args.path)

        if "error" in data:
            print(f"Error: {data['error']}", file=sys.stderr)
            sys.exit(1)

        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print(f"Disk Usage for {data['path']}")
            print("=" * 40)
            print(f"Total:     {format_bytes(data['total'], human):>12}")
            print(f"Used:      {format_bytes(data['used'], human):>12} ({data['percent']:.1f}%)")
            print(f"Available: {format_bytes(data['available'], human):>12}")

    else:
        partitions = get_partitions(include_all=args.all)

        if args.json:
            print(json.dumps(partitions, indent=2))
            sys.exit(0)

        print("Disk Partitions")
        print("=" * 80)

        # Header
        if human:
            print(f"{'Filesystem':<20} {'Size':>10} {'Used':>10} {'Avail':>10} {'Use%':>6} {'Mounted on'}")
        else:
            print(f"{'Filesystem':<20} {'Type':<10} {'Total':>15} {'Used':>15} {'Mounted on'}")

        print("-" * 80)

        for part in partitions:
            if "error" in part and "device" not in part:
                print(f"Error: {part['error']}")
                continue

            device = part["device"][:19] if len(part["device"]) > 19 else part["device"]

            if "error" in part:
                print(f"{device:<20} {'error':>10} {'':>10} {'':>10} {'':>6} {part['mountpoint']}")
                continue

            if human:
                total = format_bytes(part["total"], True)
                used = format_bytes(part["used"], True)
                avail = format_bytes(part.get("free", part.get("available", 0)), True)
                percent = f"{part['percent']:.0f}%"
                print(f"{device:<20} {total:>10} {used:>10} {avail:>10} {percent:>6} {part['mountpoint']}")
            else:
                print(f"{device:<20} {part['fstype']:<10} {part['total']:>15} {part['used']:>15} {part['mountpoint']}")

        # Visual summary for main partitions
        print("\n" + "=" * 80)
        bar_width = 30

        for part in partitions:
            if "error" in part or "percent" not in part:
                continue
            # Only show bars for significant partitions
            if part.get("total", 0) > 1024 * 1024 * 1024:  # > 1GB
                percent = part["percent"]
                filled = int(bar_width * percent / 100)
                bar = "█" * filled + "░" * (bar_width - filled)
                total = format_bytes(part["total"], True)
                name = part["mountpoint"][:15] if len(part["mountpoint"]) > 15 else part["mountpoint"]
                print(f"{name:<15} [{bar}] {percent:>5.1f}% of {total}")

        if not HAS_PSUTIL:
            print("\nNote: Install psutil for more detailed information")


if __name__ == "__main__":
    main()
