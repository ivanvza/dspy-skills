#!/usr/bin/env python3
"""Fetch a web page and extract fingerprinting information."""

import argparse
import html
import re
import ssl
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse


def fetch_page(url: str, timeout: int = 10) -> dict:
    """Fetch a web page and extract useful information.

    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Dictionary with page information
    """
    result = {
        "url": url,
        "status": None,
        "headers": {},
        "title": None,
        "meta_generator": None,
        "technologies": [],
        "body_preview": None,
        "error": None,
    }

    # Ensure URL has scheme
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"
        result["url"] = url

    # Create SSL context that doesn't verify (for self-signed certs)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
            result["status"] = response.status

            # Capture headers
            for header, value in response.getheaders():
                result["headers"][header.lower()] = value

            # Read body
            body = response.read()

            # Try to decode
            charset = "utf-8"
            content_type = result["headers"].get("content-type", "")
            if "charset=" in content_type:
                charset = content_type.split("charset=")[-1].split(";")[0].strip()

            try:
                body_text = body.decode(charset, errors="replace")
            except Exception:
                body_text = body.decode("utf-8", errors="replace")

            # Extract title
            title_match = re.search(r"<title[^>]*>(.*?)</title>", body_text, re.IGNORECASE | re.DOTALL)
            if title_match:
                result["title"] = html.unescape(title_match.group(1).strip())[:200]

            # Extract meta generator
            gen_match = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)["\']', body_text, re.IGNORECASE)
            if not gen_match:
                gen_match = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']generator["\']', body_text, re.IGNORECASE)
            if gen_match:
                result["meta_generator"] = gen_match.group(1).strip()

            # Detect technologies from headers and body
            technologies = []

            # Server header
            if "server" in result["headers"]:
                technologies.append(f"Server: {result['headers']['server']}")

            # X-Powered-By
            if "x-powered-by" in result["headers"]:
                technologies.append(f"Powered by: {result['headers']['x-powered-by']}")

            # Common frameworks/CMS detection
            detections = [
                (r"wp-content|wp-includes|wordpress", "WordPress"),
                (r"Drupal|drupal\.settings", "Drupal"),
                (r"Joomla", "Joomla"),
                (r"/sites/default/files|drupal", "Drupal"),
                (r"laravel|Laravel", "Laravel"),
                (r"django|csrfmiddlewaretoken", "Django"),
                (r"express|X-Powered-By: Express", "Express.js"),
                (r"next\.js|_next/static|__NEXT_DATA__", "Next.js"),
                (r"react|reactroot|__REACT", "React"),
                (r"vue\.js|v-app|vue-router", "Vue.js"),
                (r"angular|ng-version|ng-app", "Angular"),
                (r"jquery|jQuery", "jQuery"),
                (r"bootstrap", "Bootstrap"),
                (r"phpmyadmin|phpMyAdmin", "phpMyAdmin"),
                (r"tomcat|Apache Tomcat", "Apache Tomcat"),
                (r"nginx", "nginx"),
                (r"apache", "Apache"),
                (r"IIS|Microsoft-IIS", "Microsoft IIS"),
                (r"cloudflare", "Cloudflare"),
            ]

            check_text = body_text + " " + str(result["headers"])
            for pattern, name in detections:
                if re.search(pattern, check_text, re.IGNORECASE):
                    if name not in technologies:
                        technologies.append(name)

            result["technologies"] = technologies

            # Body preview (first 500 chars of visible text)
            # Remove script and style tags
            clean = re.sub(r"<script[^>]*>.*?</script>", "", body_text, flags=re.DOTALL | re.IGNORECASE)
            clean = re.sub(r"<style[^>]*>.*?</style>", "", clean, flags=re.DOTALL | re.IGNORECASE)
            clean = re.sub(r"<[^>]+>", " ", clean)
            clean = re.sub(r"\s+", " ", clean).strip()
            result["body_preview"] = clean[:500] if clean else None

    except urllib.error.HTTPError as e:
        result["status"] = e.code
        result["error"] = f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        result["error"] = f"URL Error: {e.reason}"
    except Exception as e:
        result["error"] = f"Error: {str(e)}"

    return result


def format_output(result: dict) -> str:
    """Format the result for display."""
    lines = []
    lines.append(f"URL: {result['url']}")
    lines.append(f"Status: {result['status']}")

    if result["error"]:
        lines.append(f"Error: {result['error']}")
        return "\n".join(lines)

    if result["title"]:
        lines.append(f"Title: {result['title']}")

    if result["meta_generator"]:
        lines.append(f"Generator: {result['meta_generator']}")

    if result["technologies"]:
        lines.append(f"Technologies: {', '.join(result['technologies'])}")

    # Key headers
    important_headers = ["server", "x-powered-by", "x-aspnet-version", "x-generator"]
    for h in important_headers:
        if h in result["headers"]:
            lines.append(f"Header {h}: {result['headers'][h]}")

    if result["body_preview"]:
        lines.append(f"\nPage Preview:\n{result['body_preview'][:300]}...")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Fetch and fingerprint a web page")
    parser.add_argument("url", help="URL or IP address to fetch")
    parser.add_argument("--port", "-p", type=int, help="Port number (appended to URL if provided)")
    parser.add_argument("--https", "-s", action="store_true", help="Use HTTPS instead of HTTP")
    parser.add_argument("--timeout", "-t", type=int, default=10, help="Timeout in seconds")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    url = args.url

    # Handle port
    if args.port:
        parsed = urlparse(url if "://" in url else f"http://{url}")
        scheme = "https" if args.https else (parsed.scheme or "http")
        host = parsed.hostname or url
        url = f"{scheme}://{host}:{args.port}"
    elif args.https and not url.startswith("https://"):
        url = url.replace("http://", "https://") if url.startswith("http://") else f"https://{url}"

    result = fetch_page(url, timeout=args.timeout)

    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        print(format_output(result))


if __name__ == "__main__":
    main()
