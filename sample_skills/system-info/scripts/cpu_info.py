#!/usr/bin/env python3
"""Get CPU usage and information."""

import argparse
import json
import os
import platform
import sys
import time

# Try to import psutil for better accuracy
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def get_cpu_count() -> dict:
    """Get CPU count information."""
    logical = os.cpu_count() or 1

    if HAS_PSUTIL:
        physical = psutil.cpu_count(logical=False) or logical
    else:
        physical = logical  # Can't determine without psutil

    return {
        "logical": logical,
        "physical": physical
    }


def get_cpu_usage() -> dict:
    """Get current CPU usage."""
    if HAS_PSUTIL:
        # Get overall CPU usage
        overall = psutil.cpu_percent(interval=0.1)

        # Get per-CPU usage
        per_cpu = psutil.cpu_percent(interval=0.1, percpu=True)

        return {
            "overall": overall,
            "per_cpu": per_cpu
        }
    else:
        # Fallback: read from /proc/stat on Linux
        try:
            with open("/proc/stat", "r") as f:
                line = f.readline()
            parts = line.split()
            total = sum(int(p) for p in parts[1:])
            idle = int(parts[4])

            # Need two readings to calculate usage
            time.sleep(0.1)

            with open("/proc/stat", "r") as f:
                line = f.readline()
            parts = line.split()
            total2 = sum(int(p) for p in parts[1:])
            idle2 = int(parts[4])

            total_diff = total2 - total
            idle_diff = idle2 - idle

            usage = ((total_diff - idle_diff) / total_diff) * 100 if total_diff > 0 else 0

            return {
                "overall": round(usage, 1),
                "per_cpu": None
            }
        except Exception:
            return {
                "overall": None,
                "per_cpu": None
            }


def get_cpu_info() -> dict:
    """Get CPU information."""
    info = {
        "processor": platform.processor() or "Unknown",
        "architecture": platform.machine(),
        "platform": platform.system()
    }

    if HAS_PSUTIL:
        try:
            freq = psutil.cpu_freq()
            if freq:
                info["frequency"] = {
                    "current": round(freq.current, 0),
                    "min": round(freq.min, 0) if freq.min else None,
                    "max": round(freq.max, 0) if freq.max else None
                }
        except Exception:
            pass

    # Try to get more info from /proc/cpuinfo on Linux
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("model name"):
                    info["model"] = line.split(":")[1].strip()
                    break
    except Exception:
        pass

    return info


def get_load_average() -> dict:
    """Get system load average."""
    try:
        load = os.getloadavg()
        return {
            "1min": round(load[0], 2),
            "5min": round(load[1], 2),
            "15min": round(load[2], 2)
        }
    except (AttributeError, OSError):
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Get CPU usage and information.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --watch 2
  %(prog)s --json
        """
    )
    parser.add_argument(
        "-w", "--watch",
        type=float,
        metavar="SECONDS",
        help="Continuously update every N seconds"
    )
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--no-usage",
        action="store_true",
        help="Skip usage measurement (faster)"
    )

    args = parser.parse_args()

    def get_all_info():
        result = {
            "count": get_cpu_count(),
            "info": get_cpu_info(),
            "load_average": get_load_average()
        }
        if not args.no_usage:
            result["usage"] = get_cpu_usage()
        return result

    if args.watch:
        try:
            while True:
                data = get_all_info()
                if args.json:
                    print(json.dumps(data))
                else:
                    # Clear screen
                    print("\033[2J\033[H", end="")
                    print("CPU Information (Ctrl+C to stop)")
                    print("=" * 40)

                    if data["usage"]:
                        print(f"Overall Usage: {data['usage']['overall']:.1f}%")
                        if data["usage"]["per_cpu"]:
                            print("Per-CPU:", " ".join(f"{u:.0f}%" for u in data["usage"]["per_cpu"]))

                    if data["load_average"]:
                        la = data["load_average"]
                        print(f"Load Average: {la['1min']} {la['5min']} {la['15min']}")

                    print(f"CPUs: {data['count']['logical']} logical, {data['count']['physical']} physical")

                time.sleep(args.watch)
        except KeyboardInterrupt:
            print("\nStopped.")
            sys.exit(0)
    else:
        data = get_all_info()

        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print("CPU Information")
            print("=" * 40)

            info = data["info"]
            print(f"Processor: {info.get('model', info['processor'])}")
            print(f"Architecture: {info['architecture']}")

            if "frequency" in info and info["frequency"]["current"]:
                freq = info["frequency"]
                print(f"Frequency: {freq['current']:.0f} MHz", end="")
                if freq["max"]:
                    print(f" (max: {freq['max']:.0f} MHz)", end="")
                print()

            count = data["count"]
            print(f"CPU Cores: {count['physical']} physical, {count['logical']} logical")

            if data.get("usage"):
                usage = data["usage"]
                print(f"\nUsage: {usage['overall']:.1f}%")
                if usage["per_cpu"]:
                    print("Per-CPU:", " ".join(f"{u:.0f}%" for u in usage["per_cpu"]))

            if data["load_average"]:
                la = data["load_average"]
                print(f"\nLoad Average: {la['1min']} (1m) {la['5min']} (5m) {la['15min']} (15m)")

            if not HAS_PSUTIL:
                print("\nNote: Install psutil for more detailed information")


if __name__ == "__main__":
    main()
