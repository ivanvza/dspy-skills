#!/usr/bin/env python3
"""Ping a host to check network reachability."""

import argparse
import platform
import subprocess
import sys


def ping_host(host: str, count: int = 4, timeout: int = 5) -> dict:
    """Ping a host and return results.

    Args:
        host: Hostname or IP address to ping
        count: Number of ping packets to send
        timeout: Timeout in seconds for each ping

    Returns:
        Dictionary with ping results
    """
    # Determine ping command based on OS
    system = platform.system().lower()

    if system == "windows":
        cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
    else:  # Linux, macOS
        cmd = ["ping", "-c", str(count), "-W", str(timeout), host]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout * count + 10
        )

        return {
            "success": result.returncode == 0,
            "host": host,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None,
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "host": host,
            "output": None,
            "error": "Ping command timed out",
            "return_code": -1
        }
    except FileNotFoundError:
        return {
            "success": False,
            "host": host,
            "output": None,
            "error": "Ping command not found on this system",
            "return_code": -1
        }
    except Exception as e:
        return {
            "success": False,
            "host": host,
            "output": None,
            "error": str(e),
            "return_code": -1
        }


def main():
    parser = argparse.ArgumentParser(
        description="Ping a host to check network reachability.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s google.com
  %(prog)s 8.8.8.8 --count 10
  %(prog)s example.com --timeout 2
        """
    )
    parser.add_argument("host", help="Hostname or IP address to ping")
    parser.add_argument(
        "-c", "--count",
        type=int,
        default=4,
        help="Number of ping packets to send (default: 4)"
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=5,
        help="Timeout in seconds for each ping (default: 5)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Only show success/failure, not full output"
    )

    args = parser.parse_args()

    result = ping_host(args.host, args.count, args.timeout)

    if args.quiet:
        if result["success"]:
            print(f"SUCCESS: {args.host} is reachable")
            sys.exit(0)
        else:
            print(f"FAILURE: {args.host} is not reachable")
            if result["error"]:
                print(f"Error: {result['error']}")
            sys.exit(1)
    else:
        print(f"Pinging {args.host}...")
        print("-" * 40)

        if result["success"]:
            print(result["output"])
            print("-" * 40)
            print(f"Result: {args.host} is REACHABLE")
            sys.exit(0)
        else:
            if result["output"]:
                print(result["output"])
            if result["error"]:
                print(f"Error: {result['error']}")
            print("-" * 40)
            print(f"Result: {args.host} is NOT REACHABLE")
            sys.exit(1)


if __name__ == "__main__":
    main()
