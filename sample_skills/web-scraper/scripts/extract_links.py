#!/usr/bin/env python3
"""Extract all links from a web page."""

import argparse
import re
import sys
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: Required packages missing. Install with:")
    print("  pip install requests beautifulsoup4")
    sys.exit(1)


def extract_links(
    url: str,
    absolute: bool = True,
    timeout: int = 30,
    filter_pattern: str = None,
    include_images: bool = False,
    include_scripts: bool = False
) -> dict:
    """Extract all links from a web page.

    Args:
        url: URL to extract links from
        absolute: Convert relative URLs to absolute
        timeout: Request timeout in seconds
        filter_pattern: Regex pattern to filter links
        include_images: Include image sources
        include_scripts: Include script sources

    Returns:
        Dictionary with extraction results
    """
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; LinkExtractor/1.0)"},
            timeout=timeout
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        links = []

        # Extract anchor links
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)[:100]  # Limit text length

            if absolute:
                href = urljoin(url, href)

            links.append({
                "url": href,
                "text": text,
                "type": "link"
            })

        # Extract image sources if requested
        if include_images:
            for img in soup.find_all("img", src=True):
                src = img["src"]
                alt = img.get("alt", "")[:100]

                if absolute:
                    src = urljoin(url, src)

                links.append({
                    "url": src,
                    "text": alt,
                    "type": "image"
                })

        # Extract script sources if requested
        if include_scripts:
            for script in soup.find_all("script", src=True):
                src = script["src"]

                if absolute:
                    src = urljoin(url, src)

                links.append({
                    "url": src,
                    "text": "",
                    "type": "script"
                })

        # Apply filter if provided
        if filter_pattern:
            pattern = re.compile(filter_pattern)
            links = [l for l in links if pattern.search(l["url"])]

        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in links:
            if link["url"] not in seen:
                seen.add(link["url"])
                unique_links.append(link)

        return {
            "success": True,
            "url": url,
            "count": len(unique_links),
            "links": unique_links,
            "error": None
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "url": url,
            "count": 0,
            "links": [],
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "count": 0,
            "links": [],
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(
        description="Extract all links from a web page.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://example.com
  %(prog)s https://example.com --absolute
  %(prog)s https://example.com --filter "\\.pdf$"
  %(prog)s https://example.com --images --scripts
  %(prog)s https://example.com --internal-only
        """
    )
    parser.add_argument("url", help="URL to extract links from")
    parser.add_argument(
        "-a", "--absolute",
        action="store_true",
        default=True,
        help="Convert relative URLs to absolute (default: True)"
    )
    parser.add_argument(
        "--relative",
        action="store_true",
        help="Keep URLs as they appear in HTML"
    )
    parser.add_argument(
        "-f", "--filter",
        help="Regex pattern to filter links (e.g., '\\.pdf$' for PDFs)"
    )
    parser.add_argument(
        "-i", "--images",
        action="store_true",
        help="Include image sources"
    )
    parser.add_argument(
        "-s", "--scripts",
        action="store_true",
        help="Include script sources"
    )
    parser.add_argument(
        "--internal-only",
        action="store_true",
        help="Only show links to the same domain"
    )
    parser.add_argument(
        "--external-only",
        action="store_true",
        help="Only show links to external domains"
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)"
    )
    parser.add_argument(
        "--urls-only",
        action="store_true",
        help="Only output URLs, one per line"
    )

    args = parser.parse_args()

    # Ensure URL has scheme
    url = args.url
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    absolute = not args.relative

    result = extract_links(
        url,
        absolute=absolute,
        timeout=args.timeout,
        filter_pattern=args.filter,
        include_images=args.images,
        include_scripts=args.scripts
    )

    if not result["success"]:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    # Filter by domain if requested
    links = result["links"]
    base_domain = urlparse(url).netloc

    if args.internal_only:
        links = [l for l in links if urlparse(l["url"]).netloc == base_domain]
    elif args.external_only:
        links = [l for l in links if urlparse(l["url"]).netloc != base_domain]

    if args.urls_only:
        for link in links:
            print(link["url"])
    else:
        print(f"Found {len(links)} links on {url}")
        print("-" * 60)

        for link in links:
            link_type = f"[{link['type']}]" if link["type"] != "link" else ""
            text = f" - {link['text']}" if link["text"] else ""
            print(f"{link_type} {link['url']}{text}")


if __name__ == "__main__":
    main()
