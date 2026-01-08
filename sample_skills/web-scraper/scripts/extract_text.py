#!/usr/bin/env python3
"""Extract readable text content from a web page."""

import argparse
import sys

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: Required packages missing. Install with:")
    print("  pip install requests beautifulsoup4")
    sys.exit(1)


def extract_text(
    url: str,
    timeout: int = 30,
    include_title: bool = True,
    paragraphs_only: bool = False,
    min_length: int = 0
) -> dict:
    """Extract readable text from a web page.

    Args:
        url: URL to extract text from
        timeout: Request timeout in seconds
        include_title: Include page title
        paragraphs_only: Only extract paragraph text
        min_length: Minimum text block length to include

    Returns:
        Dictionary with extraction results
    """
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TextExtractor/1.0)"},
            timeout=timeout
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        result_parts = []

        # Extract title
        title = None
        if include_title:
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)
                result_parts.append(f"# {title}\n")

        # Extract meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            result_parts.append(f"*{meta_desc['content']}*\n")

        # Extract headings and paragraphs
        if paragraphs_only:
            elements = soup.find_all("p")
        else:
            elements = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "td", "th"])

        for element in elements:
            text = element.get_text(strip=True)

            if len(text) < min_length:
                continue

            if element.name.startswith("h"):
                level = int(element.name[1])
                prefix = "#" * level
                result_parts.append(f"\n{prefix} {text}\n")
            elif element.name == "li":
                result_parts.append(f"  - {text}")
            else:
                result_parts.append(text)

        # Join and clean up
        full_text = "\n".join(result_parts)

        # Remove excessive whitespace
        import re
        full_text = re.sub(r"\n{3,}", "\n\n", full_text)
        full_text = full_text.strip()

        return {
            "success": True,
            "url": url,
            "title": title,
            "text": full_text,
            "word_count": len(full_text.split()),
            "char_count": len(full_text),
            "error": None
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "url": url,
            "text": None,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "text": None,
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(
        description="Extract readable text content from a web page.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://example.com
  %(prog)s https://example.com --paragraphs
  %(prog)s https://example.com --min-length 50
  %(prog)s https://example.com --output article.txt
        """
    )
    parser.add_argument("url", help="URL to extract text from")
    parser.add_argument(
        "-o", "--output",
        help="Save text to file instead of stdout"
    )
    parser.add_argument(
        "-p", "--paragraphs",
        action="store_true",
        help="Only extract paragraph text (skip headings, lists)"
    )
    parser.add_argument(
        "--no-title",
        action="store_true",
        help="Don't include page title"
    )
    parser.add_argument(
        "-m", "--min-length",
        type=int,
        default=0,
        help="Minimum text block length to include (default: 0)"
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics (word count, char count)"
    )

    args = parser.parse_args()

    # Ensure URL has scheme
    url = args.url
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    result = extract_text(
        url,
        timeout=args.timeout,
        include_title=not args.no_title,
        paragraphs_only=args.paragraphs,
        min_length=args.min_length
    )

    if not result["success"]:
        print(f"Error: {result['error']}", file=sys.stderr)
        sys.exit(1)

    if args.stats:
        print(f"URL: {result['url']}", file=sys.stderr)
        print(f"Words: {result['word_count']}", file=sys.stderr)
        print(f"Characters: {result['char_count']}", file=sys.stderr)
        print("-" * 40, file=sys.stderr)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result["text"])
        print(f"Text saved to: {args.output}", file=sys.stderr)
    else:
        print(result["text"])


if __name__ == "__main__":
    main()
