---
name: web-fingerprint
description: Find and fingerprint web servers on a target. Use when asked to "find web servers", "fingerprint a website", "what's running on this web server", "identify web technologies", or "scan for web services".
metadata:
  author: dspy-skills
  version: "1.0"
allowed-tools: Bash(nmap:*)
---

# Web Server Fingerprinting Playbook

Systematically discover and identify web servers and their technologies. **You must complete all steps in sequence.**

## When to Use This Skill

Activate this skill when the user needs to:
- Find web servers on a target or network
- Identify what web technologies are running
- Fingerprint a website or web application
- Discover CMS, frameworks, or server software

## Available Scripts

| Script | Purpose |
|--------|---------|
| `fetch_page.py` | Fetch a web page and extract fingerprinting info |

**Script usage:**
```bash
python scripts/fetch_page.py <url>
python scripts/fetch_page.py 192.168.1.1 --port 8080
python scripts/fetch_page.py 192.168.1.1 --https
python scripts/fetch_page.py example.com --json
```

---

## Step 1: Port Discovery

**Goal:** Find open web server ports on the target.

**Run this scan:**
```bash
nmap -Pn -p 80,443,8080,8443,8000,8888,3000,5000 <target>
```

**Parse output:** Look for ports showing `open` state. Common web ports:
- 80 (HTTP)
- 443 (HTTPS)
- 8080, 8000, 8888 (Alt HTTP)
- 8443 (Alt HTTPS)
- 3000, 5000 (Dev servers)

**Next:** For EACH open port found, proceed to Step 2.

---

## Step 2: Service Detection

**Goal:** Identify what web server software is running.

**Run this scan:**
```bash
nmap -Pn -sV -p <open_ports> <target>
```

**Example:** If Step 1 found ports 80 and 443 open:
```bash
nmap -Pn -sV -p 80,443 192.168.1.1
```

**Parse output:** Note the SERVICE and VERSION columns. Look for:
- Apache, nginx, IIS, lighttpd
- Version numbers
- Any additional info

**Next:** Proceed to Step 3 for each web port.

---

## Step 3: Web Page Fingerprinting

**Goal:** Fetch the page and identify technologies.

**Run the fetch_page.py script for each web port:**

For HTTP (port 80):
```bash
python scripts/fetch_page.py <target>
```

For HTTPS (port 443):
```bash
python scripts/fetch_page.py <target> --https
```

For alternate ports:
```bash
python scripts/fetch_page.py <target> --port 8080
python scripts/fetch_page.py <target> --port 8443 --https
```

**The script returns:**
- HTTP status code
- Page title
- Server headers
- Detected technologies (CMS, frameworks, libraries)
- Page content preview

**Next:** Proceed to Step 4 to compile findings.

---

## Step 4: Compile Report

**Goal:** Summarize all findings in a structured report.

**Report format:**

```
## Web Fingerprint Report

### Target: <target>
### Scan Date: <date>

### Open Web Ports
- Port 80: HTTP (open)
- Port 443: HTTPS (open)

### Server Software
- Port 80: Apache/2.4.41 (Ubuntu)
- Port 443: Apache/2.4.41 (Ubuntu)

### Web Technologies Detected
- CMS: WordPress 6.0
- Framework: PHP
- Libraries: jQuery 3.6
- CDN: Cloudflare

### Page Information
- Title: "Welcome to Example Site"
- Generator: WordPress 6.0

### Headers of Interest
- Server: Apache/2.4.41 (Ubuntu)
- X-Powered-By: PHP/8.1

### Observations
- WordPress admin panel at /wp-admin
- Login page detected
- Self-signed SSL certificate
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Find web ports | `nmap -Pn -p 80,443,8080,8443 <target>` |
| Service versions | `nmap -Pn -sV -p <ports> <target>` |
| Fetch HTTP page | `python scripts/fetch_page.py <target>` |
| Fetch HTTPS page | `python scripts/fetch_page.py <target> --https` |
| Fetch alt port | `python scripts/fetch_page.py <target> -p 8080` |

## Example Workflow

**User asks:** "What web servers are running on 192.168.1.1?"

**Step 1:** Scan for web ports
```bash
nmap -Pn -p 80,443,8080,8443,8000,8888,3000,5000 192.168.1.1
```
Output shows: 80/tcp open, 443/tcp open

**Step 2:** Get service versions
```bash
nmap -Pn -sV -p 80,443 192.168.1.1
```
Output shows: Apache httpd 2.4.41

**Step 3:** Fingerprint each port
```bash
python scripts/fetch_page.py 192.168.1.1
python scripts/fetch_page.py 192.168.1.1 --https
```
Output shows: WordPress detected, jQuery, PHP

**Step 4:** Report findings to user

## Constraints

- Always complete all 4 steps
- Scan each open web port individually in Step 3
- Some servers may not respond to fingerprinting
- Self-signed certificates are handled automatically
