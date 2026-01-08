#!/usr/bin/env python3
"""Check if a TCP port is open on a host."""

import argparse
import socket
import sys


def check_port(host: str, port: int, timeout: float = 5.0) -> dict:
    """Check if a TCP port is open on a host.

    Args:
        host: Hostname or IP address
        port: Port number to check
        timeout: Connection timeout in seconds

    Returns:
        Dictionary with check results
    """
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        # Attempt connection
        result = sock.connect_ex((host, port))
        sock.close()

        if result == 0:
            return {
                "success": True,
                "host": host,
                "port": port,
                "status": "open",
                "error": None
            }
        else:
            return {
                "success": False,
                "host": host,
                "port": port,
                "status": "closed",
                "error": f"Connection refused or port closed (error code: {result})"
            }

    except socket.gaierror as e:
        return {
            "success": False,
            "host": host,
            "port": port,
            "status": "error",
            "error": f"Could not resolve hostname: {e}"
        }
    except socket.timeout:
        return {
            "success": False,
            "host": host,
            "port": port,
            "status": "timeout",
            "error": f"Connection timed out after {timeout} seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "host": host,
            "port": port,
            "status": "error",
            "error": str(e)
        }


def get_common_service(port: int) -> str:
    """Get common service name for a port."""
    common_ports = {
        20: "FTP Data",
        21: "FTP Control",
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        110: "POP3",
        143: "IMAP",
        443: "HTTPS",
        465: "SMTPS",
        587: "SMTP Submission",
        993: "IMAPS",
        995: "POP3S",
        3306: "MySQL",
        3389: "RDP",
        5432: "PostgreSQL",
        5900: "VNC",
        6379: "Redis",
        8080: "HTTP Proxy",
        8443: "HTTPS Alt",
        27017: "MongoDB",
    }
    return common_ports.get(port, "Unknown")


def main():
    parser = argparse.ArgumentParser(
        description="Check if a TCP port is open on a host.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s google.com 443
  %(prog)s localhost 8080 --timeout 2
  %(prog)s 192.168.1.1 22

Common ports:
  22 - SSH         80 - HTTP       443 - HTTPS
  21 - FTP         25 - SMTP       3306 - MySQL
  5432 - PostgreSQL                6379 - Redis
        """
    )
    parser.add_argument("host", help="Hostname or IP address")
    parser.add_argument("port", type=int, help="Port number to check (1-65535)")
    parser.add_argument(
        "-t", "--timeout",
        type=float,
        default=5.0,
        help="Connection timeout in seconds (default: 5.0)"
    )

    args = parser.parse_args()

    # Validate port
    if not 1 <= args.port <= 65535:
        print(f"Error: Port must be between 1 and 65535, got {args.port}")
        sys.exit(2)

    result = check_port(args.host, args.port, args.timeout)
    service = get_common_service(args.port)

    print(f"Checking {args.host}:{args.port} ({service})...")
    print("-" * 40)

    if result["success"]:
        print(f"Status: OPEN")
        print(f"Port {args.port} is accepting connections")
        sys.exit(0)
    else:
        print(f"Status: {result['status'].upper()}")
        if result["error"]:
            print(f"Details: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
