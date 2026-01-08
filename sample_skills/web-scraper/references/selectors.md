# CSS Selector Reference

A quick reference for CSS selectors used in web scraping.

## Basic Selectors

| Selector | Description | Example |
|----------|-------------|---------|
| `tag` | Select by tag name | `p`, `div`, `a` |
| `.class` | Select by class | `.article`, `.nav-link` |
| `#id` | Select by ID | `#main`, `#header` |
| `*` | Select all elements | `*` |

## Combinators

| Selector | Description | Example |
|----------|-------------|---------|
| `A B` | Descendant (B inside A) | `div p` |
| `A > B` | Direct child | `ul > li` |
| `A + B` | Adjacent sibling | `h2 + p` |
| `A ~ B` | General sibling | `h2 ~ p` |

## Attribute Selectors

| Selector | Description | Example |
|----------|-------------|---------|
| `[attr]` | Has attribute | `[href]` |
| `[attr=val]` | Exact match | `[type="text"]` |
| `[attr^=val]` | Starts with | `[href^="https"]` |
| `[attr$=val]` | Ends with | `[href$=".pdf"]` |
| `[attr*=val]` | Contains | `[class*="btn"]` |

## Pseudo-classes

| Selector | Description |
|----------|-------------|
| `:first-child` | First child element |
| `:last-child` | Last child element |
| `:nth-child(n)` | Nth child (1-indexed) |
| `:not(sel)` | Negation |

## Common Patterns

### Extract all links
```python
soup.select("a[href]")
```

### Extract navigation links
```python
soup.select("nav a")
soup.select(".nav-menu a")
```

### Extract article content
```python
soup.select("article p")
soup.select(".content p")
soup.select("#main-content p")
```

### Extract images with alt text
```python
soup.select("img[alt]")
```

### Extract external links
```python
soup.select("a[href^='http']")
```

### Extract PDF links
```python
soup.select("a[href$='.pdf']")
```

### Extract data tables
```python
soup.select("table.data-table tr")
soup.select("table tbody tr td")
```

## BeautifulSoup Usage

```python
from bs4 import BeautifulSoup

# Parse HTML
soup = BeautifulSoup(html, "html.parser")

# Find single element
element = soup.select_one("h1.title")

# Find all matching elements
elements = soup.select("div.article p")

# Get text content
text = element.get_text(strip=True)

# Get attribute
href = element.get("href")
href = element["href"]  # Raises KeyError if missing
```

## Tips

1. **Be specific**: `div.content p` is better than just `p`
2. **Use IDs when available**: `#article-content` is most specific
3. **Test selectors**: Use browser DevTools to test selectors first
4. **Handle missing elements**: Always check if element exists before accessing
