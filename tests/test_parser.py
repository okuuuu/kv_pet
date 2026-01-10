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
    def sample_html(self):
        sample_file = FIXTURES_DIR / "sample_listing.html"
        if sample_file.exists():
            return sample_file.read_text()
        return ""

    def test_parse_search_results(self, sample_html):
        if not sample_html:
            pytest.skip("Sample HTML fixture not available")

        parser = KvParser(deal_type="sale")
        listings = parser.parse_search_results(sample_html)

        assert len(listings) == 3

        # Check first listing
        listing = listings[0]
        assert listing.id == "12345"
        assert listing.title == "3-room apartment in Mustamäe"
        assert listing.price == 150000
        assert listing.area_m2 == 60.5
        assert listing.rooms == 3
        assert listing.floor == 5
        assert listing.total_floors == 9
        assert listing.deal_type == "sale"

    def test_parser_calculates_price_per_m2(self, sample_html):
        if not sample_html:
            pytest.skip("Sample HTML fixture not available")

        parser = KvParser(deal_type="sale")
        listings = parser.parse_search_results(sample_html)

        listing = listings[0]
        expected = round(150000 / 60.5, 2)
        assert listing.price_per_m2 == expected


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
