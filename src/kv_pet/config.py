"""Configuration defaults for kv_pet."""

from pathlib import Path

# Base URLs
BASE_URL = "https://www.kv.ee"
SEARCH_URL = f"{BASE_URL}/en/search"
LEGACY_SEARCH_URL = f"{BASE_URL}/?act=search.simple"

# Request settings - browser-like headers to avoid anti-bot detection
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,et;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Sec-CH-UA": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Cache-Control": "max-age=0",
}

# Fallback configuration for headless browser
HEADLESS_FALLBACK_ENABLED = True  # Try headless browser if HTTP requests fail
HEADLESS_BROWSER = "playwright"  # "playwright" or "selenium"

# Throttling
REQUEST_DELAY_MIN = 2.0  # seconds
REQUEST_DELAY_MAX = 5.0  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # multiplier

# Timeouts
REQUEST_TIMEOUT = 30  # seconds

# Output paths
OUTPUT_DIR = Path("output")
DEFAULT_CSV_PATH = OUTPUT_DIR / "listings.csv"

# Deal types
DEAL_TYPE_SALE = "1"
DEAL_TYPE_RENT = "2"

DEAL_TYPE_MAP = {
    "sale": DEAL_TYPE_SALE,
    "rent": DEAL_TYPE_RENT,
}

# CSV schema column order
CSV_COLUMNS = [
    "id",
    "url",
    "title",
    "deal_type",
    "price",
    "price_per_m2",
    "area_m2",
    "rooms",
    "floor",
    "total_floors",
    "location",
    "county",
    "city",
    "district",
    "property_type",
    "build_year",
    "condition",
    "first_seen",
    "last_seen",
    "is_active",
]
