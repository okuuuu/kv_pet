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

# Search by location (Tallinn, Kristiine district)
kv-pet search --county Harjumaa --parish Tallinn --city Kristiine

# Filter by property characteristics
kv-pet search --county Harjumaa --condition renovated --building-material stone

# Filter with energy certificate
kv-pet search --county Harjumaa --energy-certificate B,C,D

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
  --county TEXT            County/region filter (e.g., Harjumaa)
  --parish TEXT            Parish/municipality filter (e.g., Saku vald)
  --city TEXT              City filter (e.g., Tallinn)
  --price-min INT          Minimum price
  --price-max INT          Maximum price
  --rooms-min INT          Minimum rooms
  --rooms-max INT          Maximum rooms
  --area-min INT           Minimum area (m²)
  --area-max INT           Maximum area (m²)
  --build-year-min INT     Minimum construction year
  --build-year-max INT     Maximum construction year
  --condition TEXT         Property condition (new, renovated, good)
  --building-material TEXT Building material (stone, panel, wood)
  --energy-certificate TEXT Energy certificate class (A, B, C, etc.)
  --keyword TEXT           Keyword/address search
  --pages INT              Number of pages to fetch (default: 1)
  --output PATH            Output CSV path
  --dry-run                Show URL without fetching
  --no-headless            Disable headless browser fallback
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
- `location` - Full address (e.g., "Harjumaa, Tallinn, Põhja-Tallinn, Kalamaja, Street 1-2")
- `county` - County/region (e.g., "Harjumaa")
- `city` - City or parish (e.g., "Tallinn", "Saku vald")
- `district` - District (e.g., "Põhja-Tallinn", "Saku")
- `property_type` - Type (apartment, house, etc.)
- `build_year` - Construction year
- `condition` - Property condition (all brand-new, renovated, good condition)
- `building_material` - Building material (stone house, panel house, etc.)
- `energy_certificate` - Energy class (requires detail page fetch)
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

### Filter Values

The advanced filters use kv.ee's internal codes. Accepted values:

**`--condition`**: `new`, `good`, `renovated`, `satisfactory`, `needs renovation`

**`--building-material`**: `stone`, `wood`, `panel`, `log`

**`--energy-certificate`**: Comma-separated, e.g., `B,C,D` or single value `A`

**`--county`**: County name (e.g., `Harjumaa`, `Tartumaa`) or major city (`Tallinn`, `Tartu`, `Pärnu`)

**`--parish`**: Parish name (e.g., `Tallinn`, `Saku vald`, `Viimsi vald`, `Maardu`)

**`--city`**: Tallinn district (e.g., `Kristiine`, `Kesklinn`, `Mustamäe`, `Lasnamäe`, `Põhja-Tallinn`, `Nõmme`, `Pirita`, `Haabersti`)

### Language Support

The parser handles both English and Estonian listing text:
- Floor: "Floor 3/4" / "Korrus 3/4"
- Build year: "construction year 2024" / "ehitusaasta 2024"
- Condition: "renovated" / "renoveeritud", "all brand-new" / "uus"
- Material: "stone house" / "kivimaja", "panel house" / "paneelmaja"

## License

Apache License 2.0
