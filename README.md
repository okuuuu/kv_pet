# kv-pet

KV.ee property listing parser and CSV updater.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Usage

### Search and save listings

```bash
# Search for apartments for sale
kv-pet search --deal-type sale --price-max 200000

# Search with multiple criteria
kv-pet search --rooms-min 2 --area-min 50 --keyword Tallinn --pages 3

# Dry run (show URLs only)
kv-pet search --deal-type rent --dry-run
```

### View statistics

```bash
kv-pet stats
```

### Inspect a URL

```bash
# Preview HTML
kv-pet inspect https://www.kv.ee/search

# Save HTML to file for analysis
kv-pet inspect https://www.kv.ee/search --save tests/fixtures/search_page.html
```

## CLI Options

```
kv-pet search [OPTIONS]

Options:
  --deal-type {sale,rent}  Type of deal (default: sale)
  --county TEXT            County/region filter
  --price-min INT          Minimum price
  --price-max INT          Maximum price
  --rooms-min INT          Minimum rooms
  --rooms-max INT          Maximum rooms
  --area-min INT           Minimum area (m²)
  --area-max INT           Maximum area (m²)
  --keyword TEXT           Keyword/address search
  --pages INT              Number of pages to fetch (default: 1)
  --output PATH            Output CSV path
  --dry-run                Show URL without fetching
```

## Output

Results are saved to `output/listings.csv` with these columns:

- `id` - Unique listing ID
- `url` - Full listing URL
- `title` - Listing title
- `deal_type` - "sale" or "rent"
- `price` - Price in EUR
- `price_per_m2` - Price per square meter
- `area_m2` - Area in m²
- `rooms` - Number of rooms
- `floor` / `total_floors` - Floor info
- `location` - Full address
- `first_seen` / `last_seen` - Timestamps
- `is_active` - Whether listing is still active

## Development

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=kv_pet
```

## Anti-Bot Protection

KV.ee uses **Cloudflare** protection that blocks automated HTTP requests with a JavaScript challenge.

### Symptoms
- HTTP 403 responses
- "Just a moment..." challenge page
- `cf-mitigated: challenge` header

### Solutions

**Option 1: Headless Browser with Stealth (Recommended)**
```bash
# Install playwright with stealth support
pip install playwright playwright-stealth
playwright install chromium
sudo playwright install-deps chromium  # Install system dependencies

# Now searches will automatically use headless browser with stealth mode
kv-pet search --deal-type sale
```

**Option 2: Manual HTML Capture**
1. Open the search page in your browser
2. Right-click → "Save as" → "Webpage, HTML Only"
3. Save to `tests/fixtures/kv_ee_search_results.html`
4. Use the fixture for testing/development

**Option 3: Disable Headless Fallback**
```bash
# Skip headless browser attempt (useful for debugging)
kv-pet inspect https://www.kv.ee/en/search --no-headless
```

### Fixture Provenance

Test fixtures should be captured from real kv.ee pages. Document the capture:
- URL: `https://www.kv.ee/en/search?deal_type=1`
- Timestamp: (when captured)
- Notes: Any redactions of personal data

## Constraints

- Respect kv.ee rate limits (2-5 second delay between requests)
- The site blocks automated requests; headless browser fallback available
- Parser selectors may need updating if site structure changes
- Always test with real HTML fixtures when possible

## License

Apache License 2.0
