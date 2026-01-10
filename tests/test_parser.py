"""Tests for HTML parser."""

from pathlib import Path

import pytest

from kv_pet.parser import (
    KvParser,
    Listing,
    extract_listing_id,
    normalize_area,
    normalize_int,
    normalize_price,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestNormalization:
    """Tests for data normalization functions."""

    def test_normalize_price_with_spaces(self):
        assert normalize_price("150 000 €") == 150000

    def test_normalize_price_with_comma(self):
        assert normalize_price("150,000€") == 150000

    def test_normalize_price_plain(self):
        assert normalize_price("150000") == 150000

    def test_normalize_price_with_nbsp(self):
        # Non-breaking space (common in Estonian formatting)
        assert normalize_price("165\xa0990\xa0€") == 165990

    def test_normalize_price_empty(self):
        assert normalize_price("") is None

    def test_normalize_price_none(self):
        assert normalize_price(None) is None

    def test_normalize_area_with_m2(self):
        assert normalize_area("60.5 m²") == 60.5

    def test_normalize_area_with_m2_no_space(self):
        assert normalize_area("60.5m²") == 60.5

    def test_normalize_area_with_comma(self):
        assert normalize_area("60,5 m²") == 60.5

    def test_normalize_area_plain(self):
        assert normalize_area("60.5") == 60.5

    def test_normalize_area_with_nbsp(self):
        assert normalize_area("43.6\xa0m²") == 43.6

    def test_normalize_area_empty(self):
        assert normalize_area("") is None

    def test_normalize_int_plain(self):
        assert normalize_int("5") == 5

    def test_normalize_int_with_text(self):
        assert normalize_int("3 rooms") == 3

    def test_normalize_int_empty(self):
        assert normalize_int("") is None


class TestExtractListingId:
    """Tests for listing ID extraction."""

    def test_extract_from_slug_url(self):
        # kv.ee uses slugs with ID at end: /en/some-title-3447874.html
        assert extract_listing_id("/en/kirsioue-kaasaegne-ja-hubane-kodupaik-sakuskirsiou-3447874.html") == "3447874"

    def test_extract_from_html_url(self):
        assert extract_listing_id("https://www.kv.ee/12345.html") == "12345"

    def test_extract_from_relative_url(self):
        assert extract_listing_id("/12345.html") == "12345"

    def test_extract_from_query_param(self):
        assert extract_listing_id("https://www.kv.ee/?id=12345") == "12345"

    def test_extract_no_id(self):
        assert extract_listing_id("https://www.kv.ee/search") is None


class TestKvParser:
    """Tests for the main parser."""

    @pytest.fixture
    def real_html(self):
        """Load real kv.ee HTML fixture."""
        sample_file = FIXTURES_DIR / "kv_ee_search_results.html"
        if sample_file.exists():
            return sample_file.read_text()
        return ""

    @pytest.fixture
    def sample_html(self):
        """Load sample HTML fixture (for backwards compatibility)."""
        sample_file = FIXTURES_DIR / "sample_listing.html"
        if sample_file.exists():
            return sample_file.read_text()
        return ""

    def test_parse_real_search_results(self, real_html):
        """Test parsing real kv.ee search results."""
        if not real_html:
            pytest.skip("Real HTML fixture not available")

        parser = KvParser(deal_type="sale")
        listings = parser.parse_search_results(real_html)

        # Should find multiple listings
        assert len(listings) >= 10

        # Check first listing has required fields
        listing = listings[0]
        assert listing.id
        assert listing.url
        assert listing.deal_type == "sale"

    def test_parse_listing_fields(self, real_html):
        """Test that listing fields are correctly extracted."""
        if not real_html:
            pytest.skip("Real HTML fixture not available")

        parser = KvParser(deal_type="sale")
        listings = parser.parse_search_results(real_html)

        # Find a listing with complete data
        complete_listings = [l for l in listings if l.price and l.area_m2 and l.rooms]
        assert len(complete_listings) > 0, "Should have listings with price, area, and rooms"

        listing = complete_listings[0]
        assert listing.price > 0
        assert listing.area_m2 > 0
        assert listing.rooms > 0
        assert listing.price_per_m2 > 0

    def test_parse_location(self, real_html):
        """Test that location is extracted."""
        if not real_html:
            pytest.skip("Real HTML fixture not available")

        parser = KvParser(deal_type="sale")
        listings = parser.parse_search_results(real_html)

        # Check that locations are extracted
        with_location = [l for l in listings if l.location]
        assert len(with_location) > 0, "Should have listings with location"

        # Location should contain address info (Estonian addresses often have commas)
        listing = with_location[0]
        assert len(listing.location) > 5

    def test_parse_floor_info(self, real_html):
        """Test that floor info is extracted from excerpts."""
        if not real_html:
            pytest.skip("Real HTML fixture not available")

        parser = KvParser(deal_type="sale")
        listings = parser.parse_search_results(real_html)

        # Some listings should have floor info
        with_floor = [l for l in listings if l.floor is not None]
        assert len(with_floor) > 0, "Should have listings with floor info"

        listing = with_floor[0]
        assert listing.floor >= 1
        assert listing.total_floors is None or listing.total_floors >= listing.floor

    def test_parse_property_type(self, real_html):
        """Test that property type is extracted from article classes."""
        if not real_html:
            pytest.skip("Real HTML fixture not available")

        parser = KvParser(deal_type="sale")
        listings = parser.parse_search_results(real_html)

        with_type = [l for l in listings if l.property_type]
        assert len(with_type) > 0, "Should have listings with property type"

        # Property type should be something like "apartment", "house", etc.
        listing = with_type[0]
        assert listing.property_type in ["apartment", "house", "land", "commercial", "room"]

    def test_parser_sets_timestamps(self, real_html):
        """Test that parser sets first_seen and last_seen."""
        if not real_html:
            pytest.skip("Real HTML fixture not available")

        parser = KvParser(deal_type="sale")
        listings = parser.parse_search_results(real_html)

        assert len(listings) > 0
        listing = listings[0]
        assert listing.first_seen is not None
        assert listing.last_seen is not None
        assert listing.is_active is True


class TestListing:
    """Tests for Listing dataclass."""

    def test_to_dict(self):
        listing = Listing(
            id="12345",
            url="https://www.kv.ee/12345.html",
            title="Test apartment",
            deal_type="sale",
            price=100000,
            area_m2=50.0,
            rooms=2,
        )

        data = listing.to_dict()

        assert data["id"] == "12345"
        assert data["price"] == 100000
        assert data["is_active"] == "true"

    def test_to_dict_with_none_values(self):
        listing = Listing(
            id="12345",
            url="https://www.kv.ee/12345.html",
            title="Test",
            deal_type="sale",
        )

        data = listing.to_dict()

        assert data["price"] is None
        assert data["rooms"] is None
