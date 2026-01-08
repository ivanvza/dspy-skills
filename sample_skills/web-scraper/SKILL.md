---
name: web-scraper
description: Web scraping toolkit for extracting content from web pages. Fetch HTML, extract links, parse text content, and download page resources. Use when the user needs to scrape websites, extract data from web pages, gather links, or harvest text content.
license: MIT
compatibility: Requires requests and beautifulsoup4 packages
metadata:
  author: dspy-skills
  version: "1.0"
---

# Web Scraper

A toolkit for extracting content from web pages using Python.

## When to Use This Skill

Activate this skill when the user needs to:
- Fetch the HTML content of a web page
- Extract all links from a page
- Get readable text content from HTML
- Scrape data from websites
- Download and analyze web content

## Requirements

This skill requires external packages:
```bash
pip install requests beautifulsoup4
```

## Available Scripts

**Always run scripts with `--help` first** to see all available options.

| Script | Purpose |
|--------|---------|
| `fetch_page.py` | Download HTML content from a URL |
| `extract_links.py` | Extract all links from a page |
| `extract_text.py` | Extract readable text from HTML |

## Decision Tree

```
Task → What do you need?
    │
    ├─ Raw HTML content?
    │   └─ Use: fetch_page.py <url>
    │
    ├─ List of links on a page?
    │   └─ Use: extract_links.py <url>
    │
    └─ Text content (no HTML tags)?
        └─ Use: extract_text.py <url>
```

## Quick Examples

**Fetch page HTML:**
```bash
python scripts/fetch_page.py https://example.com
python scripts/fetch_page.py https://example.com --output page.html
```

**Extract all links:**
```bash
python scripts/extract_links.py https://example.com
python scripts/extract_links.py https://example.com --absolute --filter "\.pdf$"
```

**Extract text content:**
```bash
python scripts/extract_text.py https://example.com
python scripts/extract_text.py https://example.com --paragraphs
```

## Best Practices

1. **Respect robots.txt** - Check if scraping is allowed
2. **Add delays** - Don't overwhelm servers with rapid requests
3. **Use appropriate User-Agent** - Identify your scraper properly
4. **Handle errors gracefully** - Websites may block or timeout
5. **Cache responses** - Don't re-fetch unchanged pages

## Common Issues

- **403 Forbidden**: Site may be blocking scrapers. Try with `--user-agent` flag.
- **Timeout**: Site may be slow. Increase `--timeout` value.
- **Empty content**: Page may require JavaScript. These scripts handle static HTML only.
- **Encoding issues**: Use `--encoding` flag if text appears garbled.

## Reference Files

See [references/selectors.md](references/selectors.md) for CSS selector syntax reference.

## Ethical Considerations

- Only scrape public data
- Respect rate limits and robots.txt
- Don't scrape personal/private information
- Check website terms of service
- Consider using official APIs when available
