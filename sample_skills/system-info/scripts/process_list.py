#!/usr/bin/env python3
"""List running processes."""

import argparse
import json
import os
import sys
from datetime import datetime

# Try to import psutil for better information
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def format_bytes(bytes_val: int) -> str:
    """Format bytes in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f}TB"


def get_processes_psutil(sort_by: str = "pid", top_n: int = None) -> list:
    """Get process list using psutil."""
    processes = []

    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent',
                                      'memory_percent', 'memory_info', 'status',
                                      'create_time', 'cmdline']):
        try:
            info = proc.info
            processes.append({
                "pid": info["pid"],
                "name": info["name"],
                "user": info["username"],
                "cpu_percent": info["cpu_percent"] or 0.0,
                "memory_percent": round(info["memory_percent"] or 0.0, 1),
                "memory_bytes": info["memory_info"].rss if info["memory_info"] else 0,
                "status": info["status"],
                "started": datetime.fromtimestamp(info["create_time"]).isoformat() if info["create_time"] else None,
                "cmdline": " ".join(info["cmdline"] or [])[:100]
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Sort
    sort_keys = {
        "pid": lambda p: p["pid"],
        "name": lambda p: p["name"].lower(),
        "cpu": lambda p: p["cpu_percent"],
        "memory": lambda p: p["memory_percent"],
        "user": lambda p: p["user"] or ""
    }

    reverse = sort_by in ["cpu", "memory"]
    processes.sort(key=sort_keys.get(sort_by, sort_keys["pid"]), reverse=reverse)

    if top_n:
        processes = processes[:top_n]

    return processes


def get_processes_proc(sort_by: str = "pid", top_n: int = None) -> list:
    """Get process list from /proc (Linux fallback)."""
    processes = []

    try:
        for pid_str in os.listdir("/proc"):
            if not pid_str.isdigit():
                continue

            pid = int(pid_str)
            proc_dir = f"/proc/{pid}"

            try:
                # Get command name
                with open(f"{proc_dir}/comm", "r") as f:
                    name = f.read().strip()

                # Get status info
                with open(f"{proc_dir}/status", "r") as f:
                    status_info = {}
                    for line in f:
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            status_info[parts[0].strip()] = parts[1].strip()

                # Get memory info
                mem_rss = 0
                if "VmRSS" in status_info:
                    mem_rss = int(status_info["VmRSS"].split()[0]) * 1024

                # Get user
                uid = int(status_info.get("Uid", "0").split()[0])
                try:
                    import pwd
                    user = pwd.getpwuid(uid).pw_name
                except Exception:
                    user = str(uid)

                processes.append({
                    "pid": pid,
                    "name": name,
                    "user": user,
                    "cpu_percent": 0.0,  # Can't easily calculate without multiple samples
                    "memory_percent": 0.0,
                    "memory_bytes": mem_rss,
                    "status": status_info.get("State", "?").split()[0],
                    "started": None,
                    "cmdline": ""
                })

            except (IOError, PermissionError):
                continue

    except Exception as e:
        return [{"error": str(e)}]

    # Sort
    sort_keys = {
        "pid": lambda p: p["pid"],
        "name": lambda p: p["name"].lower(),
        "memory": lambda p: p["memory_bytes"],
        "user": lambda p: p["user"]
    }

    reverse = sort_by == "memory"
    processes.sort(key=sort_keys.get(sort_by, sort_keys["pid"]), reverse=reverse)

    if top_n:
        processes = processes[:top_n]

    return processes


def get_processes(sort_by: str = "pid", top_n: int = None) -> list:
    """Get process list."""
    if HAS_PSUTIL:
        return get_processes_psutil(sort_by, top_n)
    else:
        return get_processes_proc(sort_by, top_n)


def main():
    parser = argparse.ArgumentParser(
        description="List running processes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --sort cpu --top 10
  %(prog)s --filter python
  %(prog)s --user root
  %(prog)s --json
        """
    )
    parser.add_argument(
        "-s", "--sort",
        choices=["pid", "name", "cpu", "memory", "user"],
        default="pid",
        help="Sort by field (default: pid)"
    )
    parser.add_argument(
        "-n", "--top",
        type=int,
        metavar="N",
        help="Show only top N processes"
    )
    parser.add_argument(
        "-f", "--filter",
        metavar="PATTERN",
        help="Filter by process name (case-insensitive)"
    )
    parser.add_argument(
        "-u", "--user",
        help="Filter by username"
    )
    parser.add_argument(
        "-p", "--pid",
        type=int,
        help="Show specific PID only"
    )
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "-l", "--long",
        action="store_true",
        help="Show more details"
    )

    args = parser.parse_args()

    processes = get_processes(sort_by=args.sort, top_n=None)

    # Check for errors
    if processes and "error" in processes[0]:
        print(f"Error: {processes[0]['error']}", file=sys.stderr)
        sys.exit(1)

    # Apply filters
    if args.filter:
        pattern = args.filter.lower()
        processes = [p for p in processes if pattern in p["name"].lower()]

    if args.user:
        processes = [p for p in processes if p["user"] == args.user]

    if args.pid:
        processes = [p for p in processes if p["pid"] == args.pid]

    # Apply top N after filtering
    if args.top:
        processes = processes[:args.top]

    if not processes:
        print("No processes found matching criteria.", file=sys.stderr)
        sys.exit(0)

    if args.json:
        print(json.dumps(processes, indent=2))
        sys.exit(0)

    # Print header
    print(f"{'PID':>7} {'USER':<10} {'CPU%':>6} {'MEM%':>6} {'MEM':>9} {'STATUS':<8} {'NAME'}")
    print("-" * 70)

    for proc in processes:
        pid = proc["pid"]
        user = (proc["user"] or "?")[:9]
        cpu = f"{proc['cpu_percent']:.1f}"
        mem_pct = f"{proc['memory_percent']:.1f}"
        mem = format_bytes(proc["memory_bytes"])
        status = proc["status"][:7]
        name = proc["name"]

        print(f"{pid:>7} {user:<10} {cpu:>6} {mem_pct:>6} {mem:>9} {status:<8} {name}")

        if args.long and proc["cmdline"]:
            print(f"        └─ {proc['cmdline'][:60]}")

    print(f"\nTotal: {len(processes)} processes")

    if not HAS_PSUTIL:
        print("\nNote: Install psutil for CPU usage and more details")


if __name__ == "__main__":
    main()
