"""HTML parser for kv.ee listing pages."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup

from .config import BASE_URL


@dataclass
class Listing:
    """Parsed listing data."""

    id: str
    url: str
    title: str
    deal_type: str
    price: Optional[int] = None
    price_per_m2: Optional[float] = None
    area_m2: Optional[float] = None
    rooms: Optional[int] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    location: Optional[str] = None
    county: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    property_type: Optional[str] = None
    build_year: Optional[int] = None
    condition: Optional[str] = None
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    is_active: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary for CSV export."""
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "deal_type": self.deal_type,
            "price": self.price,
            "price_per_m2": self.price_per_m2,
            "area_m2": self.area_m2,
            "rooms": self.rooms,
            "floor": self.floor,
            "total_floors": self.total_floors,
            "location": self.location,
            "county": self.county,
            "city": self.city,
            "district": self.district,
            "property_type": self.property_type,
            "build_year": self.build_year,
            "condition": self.condition,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "is_active": str(self.is_active).lower(),
        }


def normalize_price(price_str: str) -> Optional[int]:
    """Extract numeric price from string like '150 000 €' or '150,000€'."""
    if not price_str:
        return None
    cleaned = re.sub(r"[^\d]", "", price_str)
    return int(cleaned) if cleaned else None


def normalize_area(area_str: str) -> Optional[float]:
    """Extract area from string like '60.5 m²' or '60,5m2'."""
    if not area_str:
        return None
    cleaned = area_str.replace(",", ".").replace("m²", "").replace("m2", "").strip()
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_int(value_str: str) -> Optional[int]:
    """Extract integer from string."""
    if not value_str:
        return None
    cleaned = re.sub(r"[^\d]", "", value_str)
    return int(cleaned) if cleaned else None


def extract_listing_id(url: str) -> Optional[str]:
    """Extract listing ID from URL like 'https://www.kv.ee/12345.html'."""
    match = re.search(r"/(\d+)\.html", url)
    if match:
        return match.group(1)
    match = re.search(r"[?&]id=(\d+)", url)
    if match:
        return match.group(1)
    return None


class KvParser:
    """Parser for kv.ee HTML pages.

    NOTE: Selectors are placeholders and need to be updated based on
    actual HTML structure once sample pages are captured.
    """

    # CSS selectors - UPDATE THESE based on actual HTML structure
    LISTING_CONTAINER = ".listing-item, .object-item, article.result"
    LISTING_LINK = "a[href*='.html']"
    LISTING_TITLE = ".title, h2, h3"
    LISTING_PRICE = ".price, .object-price"
    LISTING_AREA = ".area, .size, [class*='area']"
    LISTING_ROOMS = ".rooms, [class*='room']"
    LISTING_LOCATION = ".location, .address, [class*='location']"
    LISTING_FLOOR = ".floor, [class*='floor']"

    def __init__(self, deal_type: str = "sale"):
        self.deal_type = deal_type
        self.now = datetime.utcnow().isoformat()

    def parse_search_results(self, html: str) -> list[Listing]:
        """Parse search results page and return list of listings."""
        soup = BeautifulSoup(html, "html.parser")
        listings = []

        containers = soup.select(self.LISTING_CONTAINER)

        for container in containers:
            listing = self._parse_listing_card(container)
            if listing:
                listings.append(listing)

        return listings

    def _parse_listing_card(self, container) -> Optional[Listing]:
        """Parse a single listing card from search results."""
        link_elem = container.select_one(self.LISTING_LINK)
        if not link_elem:
            return None

        href = link_elem.get("href", "")
        if not href.startswith("http"):
            href = f"{BASE_URL}{href}" if href.startswith("/") else f"{BASE_URL}/{href}"

        listing_id = extract_listing_id(href)
        if not listing_id:
            return None

        title_elem = container.select_one(self.LISTING_TITLE)
        title = title_elem.get_text(strip=True) if title_elem else ""

        price_elem = container.select_one(self.LISTING_PRICE)
        price = normalize_price(price_elem.get_text()) if price_elem else None

        area_elem = container.select_one(self.LISTING_AREA)
        area = normalize_area(area_elem.get_text()) if area_elem else None

        rooms_elem = container.select_one(self.LISTING_ROOMS)
        rooms = normalize_int(rooms_elem.get_text()) if rooms_elem else None

        location_elem = container.select_one(self.LISTING_LOCATION)
        location = location_elem.get_text(strip=True) if location_elem else None

        floor_elem = container.select_one(self.LISTING_FLOOR)
        floor_text = floor_elem.get_text() if floor_elem else ""
        floor, total_floors = self._parse_floor(floor_text)

        price_per_m2 = None
        if price and area and area > 0:
            price_per_m2 = round(price / area, 2)

        return Listing(
            id=listing_id,
            url=href,
            title=title,
            deal_type=self.deal_type,
            price=price,
            price_per_m2=price_per_m2,
            area_m2=area,
            rooms=rooms,
            floor=floor,
            total_floors=total_floors,
            location=location,
            first_seen=self.now,
            last_seen=self.now,
            is_active=True,
        )

    def _parse_floor(self, floor_text: str) -> tuple[Optional[int], Optional[int]]:
        """Parse floor string like '5/9' into (floor, total_floors)."""
        if not floor_text:
            return None, None
        match = re.search(r"(\d+)\s*/\s*(\d+)", floor_text)
        if match:
            return int(match.group(1)), int(match.group(2))
        single = normalize_int(floor_text)
        return single, None

    def parse_listing_page(self, html: str, listing_id: str) -> Optional[Listing]:
        """Parse individual listing page for detailed info."""
        soup = BeautifulSoup(html, "html.parser")

        # TODO: Implement detailed parsing once HTML structure is known
        # This would extract additional fields like build_year, condition, etc.

        return None


def parse_pagination(html: str) -> tuple[int, int]:
    """Parse pagination info from search results.

    Returns (current_page, total_pages).
    """
    soup = BeautifulSoup(html, "html.parser")

    # Look for pagination elements
    # TODO: Update selectors based on actual HTML
    pagination = soup.select(".pagination a, .pager a, [class*='page'] a")

    current_page = 1
    total_pages = 1

    for elem in pagination:
        if "active" in elem.get("class", []) or "current" in elem.get("class", []):
            current_page = normalize_int(elem.get_text()) or 1
        page_num = normalize_int(elem.get_text())
        if page_num and page_num > total_pages:
            total_pages = page_num

    return current_page, total_pages
