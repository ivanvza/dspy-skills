#!/usr/bin/env python3
"""Fetch HTML content from a URL."""

import argparse
import sys

try:
    import requests
except ImportError:
    print("Error: requests package is required. Install with: pip install requests")
    sys.exit(1)


def fetch_page(
    url: str,
    timeout: int = 30,
    user_agent: str = None,
    headers: dict = None
) -> dict:
    """Fetch HTML content from a URL.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        user_agent: Custom User-Agent string
        headers: Additional HTTP headers

    Returns:
        Dictionary with fetch results
    """
    default_headers = {
        "User-Agent": user_agent or "Mozilla/5.0 (compatible; WebScraper/1.0)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    if headers:
        default_headers.update(headers)

    try:
        response = requests.get(
            url,
            headers=default_headers,
            timeout=timeout,
            allow_redirects=True
        )

        return {
            "success": True,
            "url": url,
            "final_url": response.url,
            "status_code": response.status_code,
            "content": response.text,
            "encoding": response.encoding,
            "headers": dict(response.headers),
            "error": None
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "url": url,
            "status_code": None,
            "content": None,
            "error": f"Request timed out after {timeout} seconds"
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "success": False,
            "url": url,
            "status_code": None,
            "content": None,
            "error": f"Connection error: {e}"
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "url": url,
            "status_code": None,
            "content": None,
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(
        description="Fetch HTML content from a URL.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://example.com
  %(prog)s https://example.com --output page.html
  %(prog)s https://example.com --timeout 60
  %(prog)s https://example.com --user-agent "MyBot/1.0"
        """
    )
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument(
        "-o", "--output",
        help="Save content to file instead of stdout"
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)"
    )
    parser.add_argument(
        "-u", "--user-agent",
        help="Custom User-Agent string"
    )
    parser.add_argument(
        "--headers-only",
        action="store_true",
        help="Only show response headers, not content"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress status messages"
    )

    args = parser.parse_args()

    # Ensure URL has scheme
    url = args.url
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    result = fetch_page(url, args.timeout, args.user_agent)

    if not result["success"]:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    if not args.quiet:
        print(f"URL: {result['url']}", file=sys.stderr)
        if result["final_url"] != result["url"]:
            print(f"Redirected to: {result['final_url']}", file=sys.stderr)
        print(f"Status: {result['status_code']}", file=sys.stderr)
        print(f"Encoding: {result['encoding']}", file=sys.stderr)
        print(f"Content length: {len(result['content'])} chars", file=sys.stderr)
        print("-" * 40, file=sys.stderr)

    if args.headers_only:
        for key, value in result["headers"].items():
            print(f"{key}: {value}")
        sys.exit(0)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result["content"])
        if not args.quiet:
            print(f"Content saved to: {args.output}", file=sys.stderr)
    else:
        print(result["content"])


if __name__ == "__main__":
    main()
