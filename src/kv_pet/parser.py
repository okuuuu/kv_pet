"""HTML parser for kv.ee listing pages."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from bs4 import BeautifulSoup, NavigableString

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
    building_material: Optional[str] = None
    energy_certificate: Optional[str] = None
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
            "building_material": self.building_material,
            "energy_certificate": self.energy_certificate,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "is_active": str(self.is_active).lower(),
        }


def normalize_price(price_str: str) -> Optional[int]:
    """Extract numeric price from string like '150 000 €' or '150,000€'."""
    if not price_str:
        return None
    # Remove non-breaking spaces and regular spaces
    cleaned = re.sub(r"[^\d]", "", price_str.replace("\xa0", ""))
    return int(cleaned) if cleaned else None


def normalize_area(area_str: str) -> Optional[float]:
    """Extract area from string like '60.5 m²' or '60,5m2'."""
    if not area_str:
        return None
    # Handle non-breaking spaces
    cleaned = area_str.replace("\xa0", " ").replace(",", ".").replace("m²", "").replace("m2", "").strip()
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
    """Extract listing ID from URL like '/en/some-title-3447874.html'."""
    # Match ID at the end of URL before .html
    match = re.search(r"-(\d+)\.html", url)
    if match:
        return match.group(1)
    # Fallback: any numeric ID before .html
    match = re.search(r"/(\d+)\.html", url)
    if match:
        return match.group(1)
    match = re.search(r"[?&]id=(\d+)", url)
    if match:
        return match.group(1)
    return None


class KvParser:
    """Parser for kv.ee HTML pages.

    Selectors based on kv.ee HTML structure as of 2026-01.

    Structure:
        article[data-object-id][data-object-url]
        ├── div.media (images)
        ├── div.actions (favorite, gallery)
        ├── div.description
        │   └── h2 > a (location/title link)
        │   └── p.object-excerpt (description with floor info)
        ├── div.rooms
        ├── div.area
        ├── div.add-time
        └── div.price
            └── small (price per m²)
    """

    def __init__(self, deal_type: str = "sale"):
        self.deal_type = deal_type
        self.now = datetime.utcnow().isoformat()

    def parse_search_results(self, html: str) -> list[Listing]:
        """Parse search results page and return list of listings."""
        soup = BeautifulSoup(html, "html.parser")
        listings = []

        # Find all article elements with data-object-id
        containers = soup.select("article[data-object-id]")

        for container in containers:
            listing = self._parse_listing_card(container)
            if listing:
                listings.append(listing)

        return listings

    def _parse_listing_card(self, container) -> Optional[Listing]:
        """Parse a single listing card from search results."""
        # Get ID from data attribute
        listing_id = container.get("data-object-id")
        if not listing_id:
            return None

        # Get URL from data attribute or link
        url = container.get("data-object-url", "")
        if not url:
            link = container.select_one(".description h2 a[href]")
            url = link.get("href", "") if link else ""

        if url and not url.startswith("http"):
            url = f"{BASE_URL}{url}" if url.startswith("/") else f"{BASE_URL}/{url}"

        # Get title/location from description h2 a
        title = ""
        location = None
        title_link = container.select_one(".description h2 a[href*='.html']")
        if title_link:
            location = title_link.get_text(strip=True)
            title = location  # Use location as title

        # Get rooms
        rooms_elem = container.select_one("div.rooms")
        rooms = normalize_int(rooms_elem.get_text()) if rooms_elem else None

        # Get area
        area_elem = container.select_one("div.area")
        area = normalize_area(area_elem.get_text()) if area_elem else None

        # Get price (first text node only, not the small element)
        price = None
        price_per_m2 = None
        price_elem = container.select_one("div.price")
        if price_elem:
            # Get first text content (main price)
            for child in price_elem.children:
                if isinstance(child, NavigableString):
                    price_text = str(child).strip()
                    if price_text and "€" in price_text:
                        price = normalize_price(price_text)
                        break

            # Get price per m² from small element
            small = price_elem.select_one("small")
            if small:
                price_per_m2 = normalize_area(small.get_text())

        # If no price_per_m2 from HTML, calculate it
        if price_per_m2 is None and price and area and area > 0:
            price_per_m2 = round(price / area, 2)

        # Get floor info from object-excerpt
        floor = None
        total_floors = None
        excerpt = container.select_one("p.object-excerpt")
        if excerpt:
            excerpt_text = excerpt.get_text()
            floor, total_floors = self._parse_floor(excerpt_text)

        # Get property type from article class
        property_type = None
        classes = container.get("class", [])
        for cls in classes:
            if cls.startswith("object-type-"):
                property_type = cls.replace("object-type-", "")
                break

        # Get build year from excerpt (English: "construction year", Estonian: "ehitusaasta")
        build_year = None
        condition = None
        building_material = None
        if excerpt:
            excerpt_text = excerpt.get_text()
            # Try English pattern first
            year_match = re.search(r"construction year (\d{4})", excerpt_text, re.IGNORECASE)
            if not year_match:
                # Try Estonian pattern
                year_match = re.search(r"ehitusaasta\s*(\d{4})", excerpt_text, re.IGNORECASE)
            if year_match:
                build_year = int(year_match.group(1))
            # Parse condition and building material
            condition, building_material = self._parse_excerpt(excerpt_text)

        # Parse location into county, city, district
        county, city, district = self._parse_location(location)

        return Listing(
            id=str(listing_id),
            url=url,
            title=title,
            deal_type=self.deal_type,
            price=price,
            price_per_m2=price_per_m2,
            area_m2=area,
            rooms=rooms,
            floor=floor,
            total_floors=total_floors,
            location=location,
            county=county,
            city=city,
            district=district,
            property_type=property_type,
            build_year=build_year,
            condition=condition,
            building_material=building_material,
            first_seen=self.now,
            last_seen=self.now,
            is_active=True,
        )

    def _parse_floor(self, text: str) -> tuple[Optional[int], Optional[int]]:
        """Parse floor string like 'Floor 3/4' or 'Korrus 3/4' into (floor, total_floors)."""
        if not text:
            return None, None
        # Match "Floor X/Y" or "Korrus X/Y" pattern (English/Estonian)
        match = re.search(r"(?:[Ff]loor|[Kk]orrus)\s*(\d+)\s*/\s*(\d+)", text)
        if match:
            return int(match.group(1)), int(match.group(2))
        # Match standalone "X/Y" pattern at start of text
        match = re.search(r"^(\d+)\s*/\s*(\d+)", text.strip())
        if match:
            return int(match.group(1)), int(match.group(2))
        return None, None

    def _parse_location(
        self, location: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse location string into (county, city, district).

        Location formats:
        - Tallinn: "Harjumaa, Tallinn, Põhja-Tallinn, Kalamaja, Uus-Volta 7-49"
        - Rural: "Harjumaa, Saku vald, Saku, Kirsiõue, Soo tee 5-20"

        Returns (county, city, district) where:
        - county: First part (e.g. "Harjumaa")
        - city: Second part - either city name or parish (e.g. "Tallinn" or "Saku vald")
        - district: Third part if available (e.g. "Põhja-Tallinn" or "Saku")
        """
        if not location:
            return None, None, None

        parts = [p.strip() for p in location.split(",")]
        if not parts:
            return None, None, None

        county = parts[0] if len(parts) > 0 else None
        city = parts[1] if len(parts) > 1 else None
        district = parts[2] if len(parts) > 2 else None

        return county, city, district

    def _parse_excerpt(
        self, excerpt_text: str
    ) -> tuple[Optional[str], Optional[str]]:
        """Parse excerpt text for condition and building material.

        Excerpt format: "Floor X/Y, ownership, building_material, construction year YYYY, condition, ..."

        Handles both English and Estonian text.
        """
        if not excerpt_text:
            return None, None

        condition = None
        building_material = None
        text_lower = excerpt_text.lower()

        # Known building materials (English -> Estonian mappings)
        # Format: (search_term, normalized_value)
        materials = [
            ("stone house", "stone"),
            ("kivimaja", "stone"),
            ("panel house", "panel"),
            ("paneelmaja", "panel"),
            ("paneel", "panel"),
            ("wooden house", "wood"),
            ("puitkarkass", "wood"),
            ("puit", "wood"),
            ("brick house", "brick"),
            ("tellismaja", "brick"),
            ("log house", "log"),
            ("palkmaja", "log"),
        ]
        for search_term, normalized in materials:
            if search_term in text_lower:
                building_material = normalized
                break

        # Known conditions (English and Estonian)
        # Format: (search_term, normalized_value)
        conditions = [
            ("all brand-new", "new"),
            ("brand-new", "new"),
            ("uus,", "new"),  # Estonian "new" - comma to avoid partial matches
            (", uus", "new"),
            ("renoveeritud", "renovated"),
            ("renovated", "renovated"),
            ("good condition", "good"),
            ("heas seisukorras", "good"),
            ("hea seisukord", "good"),
            ("satisfactory condition", "satisfactory"),
            ("rahuldav", "satisfactory"),
            ("needs renovation", "needs renovation"),
            ("vajab remonti", "needs renovation"),
        ]
        for search_term, normalized in conditions:
            if search_term in text_lower:
                condition = normalized
                break

        return condition, building_material

    def parse_listing_page(self, html: str, listing_id: str) -> Optional[Listing]:
        """Parse individual listing page for detailed info."""
        soup = BeautifulSoup(html, "html.parser")

        # TODO: Implement detailed parsing for individual listing pages
        # This would extract additional fields like condition, detailed address, etc.

        return None


def parse_pagination(html: str) -> tuple[int, int]:
    """Parse pagination info from search results.

    Returns (current_page, total_pages).
    """
    soup = BeautifulSoup(html, "html.parser")

    # Look for pagination elements
    pagination = soup.select(".pagination a, .pager a, .paging a")

    current_page = 1
    total_pages = 1

    for elem in pagination:
        classes = elem.get("class", [])
        if "active" in classes or "current" in classes:
            current_page = normalize_int(elem.get_text()) or 1
        page_num = normalize_int(elem.get_text())
        if page_num and page_num > total_pages:
            total_pages = page_num

    return current_page, total_pages
