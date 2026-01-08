#!/usr/bin/env python3
"""Get memory usage statistics."""

import argparse
import json
import sys

# Try to import psutil for better accuracy
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


def get_memory_info_psutil() -> dict:
    """Get memory info using psutil."""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "virtual": {
            "total": mem.total,
            "available": mem.available,
            "used": mem.used,
            "free": mem.free,
            "percent": mem.percent,
            "cached": getattr(mem, "cached", None),
            "buffers": getattr(mem, "buffers", None)
        },
        "swap": {
            "total": swap.total,
            "used": swap.used,
            "free": swap.free,
            "percent": swap.percent
        }
    }


def get_memory_info_proc() -> dict:
    """Get memory info from /proc/meminfo (Linux fallback)."""
    mem_info = {}

    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split()
                key = parts[0].rstrip(":")
                value = int(parts[1]) * 1024  # Convert KB to bytes
                mem_info[key] = value

        total = mem_info.get("MemTotal", 0)
        free = mem_info.get("MemFree", 0)
        buffers = mem_info.get("Buffers", 0)
        cached = mem_info.get("Cached", 0)
        available = mem_info.get("MemAvailable", free + buffers + cached)
        used = total - available

        swap_total = mem_info.get("SwapTotal", 0)
        swap_free = mem_info.get("SwapFree", 0)
        swap_used = swap_total - swap_free

        return {
            "virtual": {
                "total": total,
                "available": available,
                "used": used,
                "free": free,
                "percent": round((used / total) * 100, 1) if total > 0 else 0,
                "cached": cached,
                "buffers": buffers
            },
            "swap": {
                "total": swap_total,
                "used": swap_used,
                "free": swap_free,
                "percent": round((swap_used / swap_total) * 100, 1) if swap_total > 0 else 0
            }
        }
    except Exception as e:
        return {
            "error": str(e),
            "virtual": None,
            "swap": None
        }


def get_memory_info() -> dict:
    """Get memory information."""
    if HAS_PSUTIL:
        return get_memory_info_psutil()
    else:
        return get_memory_info_proc()


def main():
    parser = argparse.ArgumentParser(
        description="Get memory usage statistics.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --human
  %(prog)s --json
        """
    )
    parser.add_argument(
        "-H", "--human",
        action="store_true",
        help="Show sizes in human-readable format"
    )
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "-b", "--bytes",
        action="store_true",
        help="Show all values in bytes"
    )

    args = parser.parse_args()

    data = get_memory_info()

    if "error" in data:
        print(f"Error: {data['error']}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(data, indent=2))
        sys.exit(0)

    human = args.human or not args.bytes
    vm = data["virtual"]
    swap = data["swap"]

    print("Memory Usage")
    print("=" * 50)

    print("\nVirtual Memory:")
    print(f"  Total:     {format_bytes(vm['total'], human):>12}")
    print(f"  Used:      {format_bytes(vm['used'], human):>12} ({vm['percent']:.1f}%)")
    print(f"  Available: {format_bytes(vm['available'], human):>12}")
    print(f"  Free:      {format_bytes(vm['free'], human):>12}")

    if vm.get("cached"):
        print(f"  Cached:    {format_bytes(vm['cached'], human):>12}")
    if vm.get("buffers"):
        print(f"  Buffers:   {format_bytes(vm['buffers'], human):>12}")

    if swap["total"] > 0:
        print("\nSwap:")
        print(f"  Total:     {format_bytes(swap['total'], human):>12}")
        print(f"  Used:      {format_bytes(swap['used'], human):>12} ({swap['percent']:.1f}%)")
        print(f"  Free:      {format_bytes(swap['free'], human):>12}")
    else:
        print("\nSwap: Not configured")

    # Visual bar
    print("\n" + "=" * 50)
    bar_width = 40

    def draw_bar(percent, label):
        filled = int(bar_width * percent / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"{label}: [{bar}] {percent:.1f}%")

    draw_bar(vm["percent"], "Memory")
    if swap["total"] > 0:
        draw_bar(swap["percent"], "Swap  ")

    if not HAS_PSUTIL:
        print("\nNote: Install psutil for more accurate information")


if __name__ == "__main__":
    main()
