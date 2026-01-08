#!/usr/bin/env python3
"""Perform DNS lookups for domain names."""

import argparse
import socket
import sys


def dns_lookup(domain: str, record_type: str = "A") -> dict:
    """Perform a DNS lookup for a domain.

    Args:
        domain: Domain name to look up
        record_type: Type of DNS record (A, AAAA, etc.)

    Returns:
        Dictionary with lookup results
    """
    record_type = record_type.upper()

    try:
        if record_type == "A":
            # IPv4 address lookup
            try:
                results = socket.getaddrinfo(domain, None, socket.AF_INET)
                addresses = list(set(r[4][0] for r in results))
                return {
                    "success": True,
                    "domain": domain,
                    "type": "A",
                    "records": addresses,
                    "error": None
                }
            except socket.gaierror as e:
                return {
                    "success": False,
                    "domain": domain,
                    "type": "A",
                    "records": [],
                    "error": f"No A records found: {e}"
                }

        elif record_type == "AAAA":
            # IPv6 address lookup
            try:
                results = socket.getaddrinfo(domain, None, socket.AF_INET6)
                addresses = list(set(r[4][0] for r in results))
                return {
                    "success": True,
                    "domain": domain,
                    "type": "AAAA",
                    "records": addresses,
                    "error": None
                }
            except socket.gaierror as e:
                return {
                    "success": False,
                    "domain": domain,
                    "type": "AAAA",
                    "records": [],
                    "error": f"No AAAA records found: {e}"
                }

        elif record_type in ("MX", "TXT", "NS", "CNAME", "SOA"):
            # For these record types, we need to use nslookup or dig
            import subprocess

            try:
                # Try using nslookup (available on most systems)
                result = subprocess.run(
                    ["nslookup", f"-type={record_type}", domain],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    return {
                        "success": True,
                        "domain": domain,
                        "type": record_type,
                        "records": [result.stdout],
                        "error": None
                    }
                else:
                    return {
                        "success": False,
                        "domain": domain,
                        "type": record_type,
                        "records": [],
                        "error": result.stderr or "Lookup failed"
                    }
            except FileNotFoundError:
                return {
                    "success": False,
                    "domain": domain,
                    "type": record_type,
                    "records": [],
                    "error": f"nslookup not found. {record_type} lookups require nslookup or dig command."
                }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "domain": domain,
                    "type": record_type,
                    "records": [],
                    "error": "DNS lookup timed out"
                }
        else:
            return {
                "success": False,
                "domain": domain,
                "type": record_type,
                "records": [],
                "error": f"Unsupported record type: {record_type}. Use A, AAAA, MX, TXT, NS, CNAME, or SOA."
            }

    except Exception as e:
        return {
            "success": False,
            "domain": domain,
            "type": record_type,
            "records": [],
            "error": str(e)
        }


def reverse_lookup(ip: str) -> dict:
    """Perform a reverse DNS lookup for an IP address.

    Args:
        ip: IP address to look up

    Returns:
        Dictionary with lookup results
    """
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return {
            "success": True,
            "ip": ip,
            "hostname": hostname,
            "error": None
        }
    except socket.herror as e:
        return {
            "success": False,
            "ip": ip,
            "hostname": None,
            "error": f"Reverse lookup failed: {e}"
        }
    except Exception as e:
        return {
            "success": False,
            "ip": ip,
            "hostname": None,
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(
        description="Perform DNS lookups for domain names.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s example.com
  %(prog)s example.com --type MX
  %(prog)s example.com --type AAAA
  %(prog)s 8.8.8.8 --reverse

Record types:
  A     - IPv4 address (default)
  AAAA  - IPv6 address
  MX    - Mail exchange records
  TXT   - Text records
  NS    - Name server records
  CNAME - Canonical name records
        """
    )
    parser.add_argument("domain", help="Domain name or IP address to look up")
    parser.add_argument(
        "-t", "--type",
        default="A",
        help="DNS record type: A, AAAA, MX, TXT, NS, CNAME (default: A)"
    )
    parser.add_argument(
        "-r", "--reverse",
        action="store_true",
        help="Perform reverse DNS lookup (domain should be an IP address)"
    )
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="Show both A and AAAA records"
    )

    args = parser.parse_args()

    print(f"DNS Lookup for: {args.domain}")
    print("-" * 40)

    if args.reverse:
        result = reverse_lookup(args.domain)
        if result["success"]:
            print(f"Reverse lookup: {result['ip']} -> {result['hostname']}")
            sys.exit(0)
        else:
            print(f"Error: {result['error']}")
            sys.exit(1)

    if args.all:
        # Show both A and AAAA records
        for rtype in ["A", "AAAA"]:
            result = dns_lookup(args.domain, rtype)
            print(f"\n{rtype} Records:")
            if result["success"] and result["records"]:
                for record in result["records"]:
                    print(f"  {record}")
            else:
                print(f"  None found")
        sys.exit(0)

    result = dns_lookup(args.domain, args.type)

    if result["success"]:
        print(f"Record type: {result['type']}")
        print(f"Results:")
        for record in result["records"]:
            # Handle multi-line output from nslookup
            if "\n" in record:
                for line in record.strip().split("\n"):
                    if line.strip():
                        print(f"  {line}")
            else:
                print(f"  {record}")
        sys.exit(0)
    else:
        print(f"Error: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
