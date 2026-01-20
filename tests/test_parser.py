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


class TestListingPageParsing:
    """Tests for parsing individual listing pages."""

    @pytest.fixture
    def search_example_html(self):
        """Load kv_ee_search_example.html fixture."""
        fixture_file = FIXTURES_DIR / "kv_ee_search_example.html"
        return fixture_file.read_text()

    @pytest.fixture
    def inactive_html(self):
        """Load kv_ee_inactive.html fixture."""
        fixture_file = FIXTURES_DIR / "kv_ee_inactive.html"
        return fixture_file.read_text()

    def test_parse_condition_from_meta_table(self, search_example_html):
        """Test that condition is extracted from meta table."""
        parser = KvParser(deal_type="sale")
        listing = parser.parse_listing_page(search_example_html, "3759975")

        # Should extract "Heas korras" and normalize to "good"
        assert listing is not None
        assert listing.condition == "good"

    def test_parse_energy_certificate_from_meta_table(self, search_example_html):
        """Test that energy certificate is extracted from meta table."""
        parser = KvParser(deal_type="sale")
        listing = parser.parse_listing_page(search_example_html, "3759975")

        # Should extract "C" from Energiamärgis row
        assert listing is not None
        assert listing.energy_certificate == "C"

    def test_parse_reserved_status(self, inactive_html):
        """Test that reserved status is detected from Broneeritud header."""
        parser = KvParser(deal_type="sale")
        listing = parser.parse_listing_page(inactive_html, "3768144")

        # Should detect "(Broneeritud)" and set is_active=False, status="reserved"
        assert listing is not None
        assert listing.is_active is False
        assert listing.status == "reserved"

    def test_active_listing_has_active_status(self, search_example_html):
        """Test that non-reserved listings have active status."""
        parser = KvParser(deal_type="sale")
        listing = parser.parse_listing_page(search_example_html, "3759975")

        assert listing is not None
        assert listing.is_active is True
        assert listing.status == "active"

    def test_parse_rooms_from_meta_table(self, search_example_html):
        """Test that rooms are extracted from meta table."""
        parser = KvParser(deal_type="sale")
        listing = parser.parse_listing_page(search_example_html, "3759975")

        # Should extract "3" from Tube row
        assert listing is not None
        assert listing.rooms == 3

    def test_parse_area_from_meta_table(self, search_example_html):
        """Test that area is extracted from meta table."""
        parser = KvParser(deal_type="sale")
        listing = parser.parse_listing_page(search_example_html, "3759975")

        # Should extract "87.3 m²" from Üldpind row
        assert listing is not None
        assert listing.area_m2 == 87.3

    def test_parse_floor_from_meta_table(self, search_example_html):
        """Test that floor info is extracted from meta table."""
        parser = KvParser(deal_type="sale")
        listing = parser.parse_listing_page(search_example_html, "3759975")

        # Should extract "4/6" from Korrus/Korruseid row
        assert listing is not None
        assert listing.floor == 4
        assert listing.total_floors == 6

    def test_parse_build_year_from_meta_table(self, search_example_html):
        """Test that build year is extracted from meta table."""
        parser = KvParser(deal_type="sale")
        listing = parser.parse_listing_page(search_example_html, "3759975")

        # Should extract "2008" from Ehitusaasta row
        assert listing is not None
        assert listing.build_year == 2008


class TestConditionNormalization:
    """Tests for condition normalization."""

    def test_normalize_heas_korras(self):
        """Test Estonian 'Heas korras' normalizes to 'good'."""
        parser = KvParser()
        assert parser._normalize_condition("Heas korras") == "good"
        assert parser._normalize_condition("heas korras") == "good"

    def test_normalize_good_condition(self):
        """Test English 'good condition' normalizes to 'good'."""
        parser = KvParser()
        assert parser._normalize_condition("good condition") == "good"

    def test_normalize_uus(self):
        """Test Estonian 'uus' normalizes to 'new'."""
        parser = KvParser()
        assert parser._normalize_condition("uus") == "new"

    def test_normalize_renoveeritud(self):
        """Test Estonian 'renoveeritud' normalizes to 'renovated'."""
        parser = KvParser()
        assert parser._normalize_condition("renoveeritud") == "renovated"

    def test_normalize_vajab_remonti(self):
        """Test Estonian 'vajab remonti' normalizes to 'needs renovation'."""
        parser = KvParser()
        assert parser._normalize_condition("vajab remonti") == "needs renovation"

    def test_unknown_condition_preserved(self):
        """Test that unknown conditions are preserved as-is."""
        parser = KvParser()
        assert parser._normalize_condition("custom condition") == "custom condition"


class TestReservedDetection:
    """Tests for reserved status detection."""

    def test_detect_broneeritud_in_parentheses(self):
        """Test detection of '(Broneeritud)' in HTML."""
        parser = KvParser()
        from bs4 import BeautifulSoup

        html = '<th colspan="2">Müüa korter (Broneeritud)</th>'
        soup = BeautifulSoup(html, "html.parser")
        assert parser._detect_reserved_status(soup, html) is True

    def test_detect_reserved_in_parentheses(self):
        """Test detection of '(Reserved)' in HTML."""
        parser = KvParser()
        from bs4 import BeautifulSoup

        html = '<th colspan="2">Sell apartment (Reserved)</th>'
        soup = BeautifulSoup(html, "html.parser")
        assert parser._detect_reserved_status(soup, html) is True

    def test_no_reserved_marker(self):
        """Test that normal listings are not marked as reserved."""
        parser = KvParser()
        from bs4 import BeautifulSoup

        html = '<th colspan="2">Müüa korter</th>'
        soup = BeautifulSoup(html, "html.parser")
        assert parser._detect_reserved_status(soup, html) is False


class TestRecommendedListingsExclusion:
    """Tests for excluding recommended/suggested listings from results."""

    @pytest.fixture
    def html_with_recommended(self):
        """Load HTML fixture with recommended section."""
        fixture_file = FIXTURES_DIR / "search_with_recommended.html"
        return fixture_file.read_text()

    def test_excludes_recommended_listings(self, html_with_recommended):
        """Test that listings after 'huvi pakkuda' heading are excluded."""
        parser = KvParser(deal_type="sale")
        listings = parser.parse_search_results(html_with_recommended)

        # Should only get the 2 main listings, not the 2 recommended ones
        assert len(listings) == 2

        # Verify we got the main listings (IDs 1111111 and 2222222)
        listing_ids = {l.id for l in listings}
        assert "1111111" in listing_ids
        assert "2222222" in listing_ids

        # Verify we excluded the recommended listings (IDs 9999991 and 9999992)
        assert "9999991" not in listing_ids
        assert "9999992" not in listing_ids

    def test_no_recommended_section_parses_all(self):
        """Test that when no recommended section exists, all listings are parsed."""
        # HTML without recommended section
        html = """
        <div class="results">
            <article data-object-id="1111111" data-object-url="/test-1.html">
                <div class="description">
                    <h2><a href="/test-1.html">Test 1</a></h2>
                </div>
                <div class="rooms">2</div>
                <div class="area">50 m²</div>
                <div class="price">100 000 €</div>
            </article>
            <article data-object-id="2222222" data-object-url="/test-2.html">
                <div class="description">
                    <h2><a href="/test-2.html">Test 2</a></h2>
                </div>
                <div class="rooms">3</div>
                <div class="area">75 m²</div>
                <div class="price">150 000 €</div>
            </article>
        </div>
        """
        parser = KvParser(deal_type="sale")
        listings = parser.parse_search_results(html)

        assert len(listings) == 2

    def test_english_recommended_heading(self):
        """Test that English recommended heading is also detected."""
        html = """
        <div class="results">
            <article data-object-id="1111111" data-object-url="/main.html">
                <div class="description"><h2><a href="/main.html">Main</a></h2></div>
            </article>
        </div>
        <h3>Listings that might interest you</h3>
        <div class="results">
            <article data-object-id="9999999" data-object-url="/rec.html">
                <div class="description"><h2><a href="/rec.html">Recommended</a></h2></div>
            </article>
        </div>
        """
        parser = KvParser(deal_type="sale")
        listings = parser.parse_search_results(html)

        assert len(listings) == 1
        assert listings[0].id == "1111111"
