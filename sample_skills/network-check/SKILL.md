---
name: network-check
description: Network connectivity testing toolkit for checking host reachability, port availability, and DNS resolution. Use when diagnosing network issues, verifying service availability, testing connectivity to servers, or troubleshooting DNS problems.
license: MIT
metadata:
  author: dspy-skills
  version: "1.0"
---

# Network Connectivity Check

A toolkit for diagnosing network connectivity issues and verifying host/service availability.

## When to Use This Skill

Activate this skill when the user needs to:
- Check if a host is reachable (ping)
- Verify if a specific port is open on a host
- Perform DNS lookups to resolve domain names
- Diagnose network connectivity problems
- Test if a service is available

## Available Scripts

**Always run scripts with `--help` first** to see all available options.

| Script | Purpose |
|--------|---------|
| `ping_host.py` | Ping a host to check reachability |
| `check_port.py` | Check if a TCP port is open |
| `dns_lookup.py` | Perform DNS lookups |

## Decision Tree

```
Task → What do you need to check?
    │
    ├─ Is the host reachable at all?
    │   └─ Use: ping_host.py <hostname>
    │
    ├─ Is a specific service/port available?
    │   └─ Use: check_port.py <hostname> <port>
    │
    └─ Need to resolve a domain name?
        └─ Use: dns_lookup.py <domain>
```

## Quick Examples

**Check if a host is reachable:**
```bash
python scripts/ping_host.py google.com
python scripts/ping_host.py 8.8.8.8 --count 5
```

**Check if a port is open:**
```bash
python scripts/check_port.py example.com 443
python scripts/check_port.py localhost 8080 --timeout 5
```

**DNS lookup:**
```bash
python scripts/dns_lookup.py example.com
python scripts/dns_lookup.py example.com --type MX
```

## Common Use Cases

1. **Verify web server is running**: `check_port.py myserver.com 80`
2. **Test SSH access**: `check_port.py server.local 22`
3. **Check database connectivity**: `check_port.py db.example.com 5432`
4. **Diagnose DNS issues**: `dns_lookup.py problematic-domain.com`

## Notes

- Scripts use Python standard library only (no external dependencies)
- Ping may require appropriate permissions on some systems
- Port checks use TCP connections (not UDP)
- DNS lookups support A, AAAA, MX, TXT, NS, and CNAME record types
