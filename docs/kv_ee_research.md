# KV.ee Research Notes

## Overview
KV.ee is Estonia's leading real estate portal (since 1999). No public API available.

## Access Constraints

### Cloudflare Protection (Confirmed 2026-01-10)
- **Protection type**: Cloudflare JS Challenge
- **Response**: HTTP 403 with challenge page
- **Key headers**:
  - `cf-mitigated: challenge`
  - `server: cloudflare`
  - `cf-ray: <ray-id>`
- **Challenge page content**: "Just a moment..." with JS that must execute

### What Doesn't Work
- Plain HTTP requests (even with browser-like headers)
- Adding Sec-Fetch-* headers
- Adding Sec-CH-UA-* client hints
- Cookie-based session persistence
- Standard headless Playwright/Chromium (detected as bot)

### What Works
1. **playwright-stealth** - Successfully bypasses Cloudflare (tested 2026-01-10)
   - Uses `playwright-stealth` library to mask automation signals
   - Requires: `pip install playwright playwright-stealth && playwright install chromium`
   - Also needs system deps: `sudo playwright install-deps chromium`
2. **Manual browser capture** - for test fixtures

### Stealth Configuration That Works
```python
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

browser = playwright.chromium.launch(
    headless=True,
    args=[
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
    ],
)
context = browser.new_context(
    viewport={"width": 1920, "height": 1080},
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    locale="en-US",
    timezone_id="Europe/Tallinn",
)
page = context.new_page()
stealth_sync(page)  # Apply stealth patches
```

## URL Patterns

### Search URL Structure
```
https://www.kv.ee/?act=search.simple&<parameters>
```

Or the newer format:
```
https://www.kv.ee/en/search?<parameters>
```

### Known Query Parameters

| Parameter | Description | Example Values |
|-----------|-------------|----------------|
| `act` | Action type | `search.simple` |
| `deal_type` | Transaction type | `1` (sale), `2` (rent) |
| `county` | County/region code | `0` (all), numeric codes |
| `parish` | Municipality | string |
| `price_min` | Minimum price | integer |
| `price_max` | Maximum price | integer |
| `rooms_min` | Min rooms | integer |
| `rooms_max` | Max rooms | integer |
| `area_min` | Min area (m²) | integer |
| `area_max` | Max area (m²) | integer |
| `floor_min` | Min floor | integer |
| `floor_max` | Max floor | integer |
| `page` | Pagination | integer |
| `page_size` | Results per page | integer |
| `orderby` | Sort order | `ob` (default) |
| `keyword` | Address/keyword search | string |

### Advanced Filter Parameters (discovered 2026-01-11)

| Parameter | Description | Values |
|-----------|-------------|--------|
| `structure[]` | Building material (array) | `9` (stone), `10` (wooden), `11` (panel), `68` (log) |
| `c[]` | Condition (array) | `38` (all brand-new), `104` (good), `39` (renovated), `40` (sanitary done), `41` (satisfactory), `42` (sanitary needed), `51` (needs renovating) |
| `energy_certs` | Energy certificate | Comma-separated: `A,B,C,D,E,F,G,H` |
| `city[]` | City/district code (array) | Numeric codes (e.g., `1004` for Kristiine) |
| `parish` | Parish code | Numeric codes (e.g., `1061` for Tallinn) |

**Example URL:**
```
https://www.kv.ee/en/search?deal_type=1&county=1&parish=1061&city[0]=1004&energy_certs=B,C,D&structure[0]=9&c[0]=104
```
This searches for: sale in Harjumaa, Tallinn/Kristiine, stone house, good condition, energy class B/C/D

### Listing URL Pattern
Individual listings follow slug format with ID at end:
```
https://www.kv.ee/en/<slug>-<listing-id>.html
```
Example: `/en/kirsioue-kaasaegne-ja-hubane-kodupaik-sakuskirsiou-3447874.html`

## HTML Structure (Confirmed 2026-01-10)

### Search Results Page
```
article[data-object-id][data-object-url]
├── div.media (images carousel)
├── div.actions (favorite, gallery buttons)
├── div.description
│   └── h2
│       └── a[href*=".html"] (location/title)
│   └── p.object-excerpt (description with floor info)
├── div.rooms (number of rooms)
├── div.area (area in m²)
├── div.add-time (posted time)
└── div.price
    ├── (text) main price "165 990 €"
    └── small (price per m²)
```

### Key Selectors
- Listing container: `article[data-object-id]`
- Listing ID: `data-object-id` attribute
- Listing URL: `data-object-url` attribute
- Title/Location: `.description h2 a[href*=".html"]`
- Rooms: `div.rooms`
- Area: `div.area`
- Price: `div.price` (first text node)
- Price/m²: `div.price small`
- Floor info: `p.object-excerpt` (parse "Floor X/Y" pattern)
- Property type: article class `object-type-apartment`, `object-type-house`, etc.
- Build year: `p.object-excerpt` (parse "construction year YYYY")

### Data Formats
- Prices: "165 990 €" or "165\xa0990\xa0€" (non-breaking spaces)
- Areas: "43.6 m²" or "43.6\xa0m²"
- Floor: "Floor 3/4" in excerpt text

### Location Hierarchy (from .description h2 a)
Location string format varies by area:
- Tallinn: `County, City, District, Sub-district, Street address`
  - Example: "Harjumaa, Tallinn, Põhja-Tallinn, Kalamaja, Uus-Volta 7-49"
- Rural: `County, Parish, Village/Town, Area, Street address`
  - Example: "Harjumaa, Saku vald, Saku, Kirsiõue, Soo tee 5-20"

### Object Excerpt Fields (from p.object-excerpt)
Excerpt contains comma-separated attributes:
- Floor: "Floor X/Y" or "2 floor"
- Ownership: "apartment ownership"
- Building material: "stone house", "panel house", "wooden house", "brick house"
- Construction year: "construction year YYYY"
- Condition: "all brand-new", "renovated", "good condition", "satisfactory condition"
- Additional: heating type, balcony, amenities

### Energy Certificate
- NOT visible in search results
- Available only on individual listing detail pages
- Would require fetching each listing page separately

## Rate Limiting Strategy
- Minimum 2-3 second delay between requests
- Session reuse with cookies
- Realistic User-Agent
- Respect any Retry-After headers

## Implementation Notes
1. HTTP requests fail with 403 (Cloudflare)
2. Standard headless browser detected as bot
3. **playwright-stealth successfully bypasses protection**
4. Parse HTML with BeautifulSoup4
5. Extract listing data from `article[data-object-id]` elements
