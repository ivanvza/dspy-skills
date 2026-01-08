---
name: network-recon
description: Perform network reconnaissance including host discovery, port scanning, and service enumeration. Use when asked to "scan a network", "find hosts", "discover devices", "enumerate services", "recon a subnet", or "what's on my network".
metadata:
  author: dspy-skills
  version: "1.0"
allowed-tools: Bash(nmap:*) Bash(curl:*)
---

# Network Reconnaissance Playbook

A systematic approach to network discovery and enumeration. You must complete all phases when doing recon.

## When to Use This Skill

Activate this skill when the user needs to:
- Discover live hosts on a network
- Find open ports on a target
- Identify running services and versions
- Enumerate web services
- Perform a full network assessment

## Decision Tree

```
Task → What does the user need?
    │
    ├─ Find live hosts on a network?
    │   └─ Phase 1: Host Discovery
    │
    ├─ Find open ports on a known host?
    │   └─ Phase 2: Port Scanning
    │
    ├─ Identify what services are running?
    │   └─ Phase 3: Service Detection
    │
    ├─ Explore web services in detail?
    │   └─ Phase 4: Web Enumeration
    │
    └─ Full network assessment?
        └─ Run all phases in sequence
```

## Phase 1: Host Discovery

**Goal:** Find live hosts on the target network.

```bash
# Ping sweep - fastest method
nmap -sn 192.168.1.0/24

# ARP scan - more reliable on local networks (requires root)
nmap -sn -PR 192.168.1.0/24

# Skip ping, assume hosts are up (for filtered networks)
nmap -Pn 192.168.1.0/24
```

**Output parsing:** Look for lines containing "Nmap scan report for" - these are your live hosts.

**Next step:** Record all discovered IPs, then proceed to Phase 2 for each host.

## Phase 2: Port Scanning

**Goal:** Find open ports on discovered hosts.

| Scan Type | Command | Use When |
|-----------|---------|----------|
| Quick (top 100) | `nmap -Pn -F <ips>` | Initial fast scan |
| Standard (top 1000) | `nmap -Pn <ips>` | Default reconnaissance |
| Full (all 65535) | `nmap -Pn -p- <ips>` | Thorough assessment |
| Specific ports | `nmap -Pn -p 22,80,443 <ips>` | Known services |
| UDP scan | `nmap -sU --top-ports 20 <ips>` | Check UDP services |

**Speed options:**
```bash
# Faster scanning (less accurate)
nmap -T4 -F 192.168.1.1

# Aggressive timing
nmap -T5 192.168.1.1
```

**Output parsing:** Note all ports showing "open" state.

**Next step:** For each host with open ports, proceed to Phase 3.

## Phase 3: Service Detection

**Goal:** Identify services and versions running on open ports.

```bash
# Version detection on all open ports
nmap -sV 192.168.1.1

# Version detection on specific ports (faster)
nmap -sV -p 22,80,443,3306 192.168.1.1

# Aggressive version detection
nmap -sV --version-intensity 5 192.168.1.1

# Include OS detection
nmap -sV -O 192.168.1.1
```

**Combined scan (recommended for full assessment):**
```bash
# Version + default scripts + OS detection
nmap -A 192.168.1.1

# Same but on specific ports
nmap -A -p 22,80,443 192.168.1.1
```

**Output parsing:** Record service names, versions, and any additional info from scripts.

**Next step:** For hosts with web ports (80, 443, 8080, 8443), proceed to Phase 4.

## Phase 4: Web Enumeration

**Goal:** Gather details about web services.

**Check HTTP headers:**
```bash
# HTTP
curl -I http://192.168.1.1
curl -I http://192.168.1.1:8080

# HTTPS (ignore cert errors)
curl -Ik https://192.168.1.1

# Follow redirects
curl -ILk http://192.168.1.1
```

**Grab page title and content:**
```bash
# Get page content
curl -s http://192.168.1.1 | head -50

# Just the title
curl -s http://192.168.1.1 | grep -i '<title>'
```

**Check common paths:**
```bash
# Robots.txt
curl -s http://192.168.1.1/robots.txt

# Common admin paths
curl -I http://192.168.1.1/admin
curl -I http://192.168.1.1/login
curl -I http://192.168.1.1/wp-admin
```

**Nmap HTTP scripts:**
```bash
# HTTP enumeration
nmap --script http-enum -p 80 192.168.1.1

# HTTP headers
nmap --script http-headers -p 80 192.168.1.1

# HTTP methods
nmap --script http-methods -p 80 192.168.1.1

# All HTTP scripts
nmap --script "http-*" -p 80,443 192.168.1.1
```

## Phase 5: Vulnerability Scanning (Optional)

**Goal:** Check for known vulnerabilities.

```bash
# Run vulnerability scripts
nmap --script vuln 192.168.1.1

# Check specific vulnerabilities
nmap --script smb-vuln-* -p 445 192.168.1.1
nmap --script ssl-heartbleed -p 443 192.168.1.1
```

## Quick Reference Commands

| Task | Command |
|------|---------|
| Discover hosts | `nmap -sn 192.168.1.0/24` |
| Quick port scan | `nmap -Pn -F <ips>` |
| Full port scan | `nmap -Pn -p- <ips>` |
| Service versions | `nmap -Pn -sV <ips>` |
| Full assessment | `nmap -Pn -A <ips>` |
| Web headers | `curl -Ik https://192.168.1.1` |
| Vuln scan | `nmap --script vuln <ips>` |

## Output Format

After completing reconnaissance, summarize findings:

```
## Network Recon Summary

### Target: 192.168.1.0/24
### Hosts Discovered: 5

### Host: 192.168.1.1 (Gateway)
- Open Ports: 22, 80, 443
- Services:
  - 22/tcp: OpenSSH 8.2
  - 80/tcp: nginx 1.18.0
  - 443/tcp: nginx 1.18.0 (SSL)
- Web: Router admin panel, requires auth
- Notes: Default credentials may apply

### Host: 192.168.1.10 (Web Server)
- Open Ports: 22, 80, 3306
- Services:
  - 22/tcp: OpenSSH 8.4
  - 80/tcp: Apache 2.4.41
  - 3306/tcp: MySQL 8.0.27
- Web: WordPress site detected
- Notes: /wp-admin accessible, MySQL exposed
```

## Constraints

- Confirm target scope with user before scanning
- Large network scans may take significant time
- UDP scans are slower than TCP
- Some scans require root/sudo privileges
- Always note authorization status
