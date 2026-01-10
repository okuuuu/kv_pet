"""Tests for CSV store."""

import csv
from pathlib import Path

import pytest

from kv_pet.csv_store import CsvStore
from kv_pet.config import CSV_COLUMNS
from kv_pet.parser import Listing


@pytest.fixture
def temp_csv(tmp_path):
    """Create a temporary CSV path."""
    return tmp_path / "test_listings.csv"


@pytest.fixture
def store(temp_csv):
    """Create a CsvStore with temp path."""
    return CsvStore(temp_csv)


@pytest.fixture
def sample_listing():
    """Create a sample listing."""
    return Listing(
        id="12345",
        url="https://www.kv.ee/12345.html",
        title="Test apartment",
        deal_type="sale",
        price=100000,
        area_m2=50.0,
        rooms=2,
        location="Tallinn",
    )


class TestCsvStore:
    """Tests for CsvStore."""

    def test_read_empty(self, store):
        """Reading non-existent CSV returns empty dict."""
        result = store.read_all()
        assert result == {}

    def test_merge_new_listing(self, store, sample_listing):
        """New listing is added to empty store."""
        added, updated, unchanged = store.merge_listings([sample_listing])

        assert added == 1
        assert updated == 0
        assert unchanged == 0

        listings = store.read_all()
        assert "12345" in listings
        assert listings["12345"]["title"] == "Test apartment"

    def test_merge_updates_existing(self, store, sample_listing):
        """Existing listing is updated with new data."""
        store.merge_listings([sample_listing])

        updated_listing = Listing(
            id="12345",
            url="https://www.kv.ee/12345.html",
            title="Updated apartment",
            deal_type="sale",
            price=110000,
            area_m2=50.0,
            rooms=2,
            location="Tallinn",
        )

        added, updated, unchanged = store.merge_listings([updated_listing])

        assert added == 0
        assert updated == 1
        assert unchanged == 0

        listings = store.read_all()
        assert listings["12345"]["title"] == "Updated apartment"
        assert listings["12345"]["price"] == "110000"

    def test_merge_preserves_first_seen(self, store, sample_listing):
        """first_seen is preserved on update."""
        store.merge_listings([sample_listing])
        listings = store.read_all()
        original_first_seen = listings["12345"]["first_seen"]

        updated_listing = Listing(
            id="12345",
            url="https://www.kv.ee/12345.html",
            title="Updated apartment",
            deal_type="sale",
            price=110000,
        )

        store.merge_listings([updated_listing])

        listings = store.read_all()
        assert listings["12345"]["first_seen"] == original_first_seen

    def test_csv_column_order(self, store, sample_listing, temp_csv):
        """CSV columns are in schema order."""
        store.merge_listings([sample_listing])

        with open(temp_csv, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)

        assert headers == CSV_COLUMNS

    def test_stats(self, store, sample_listing):
        """Stats returns correct counts."""
        store.merge_listings([sample_listing])

        stats = store.get_stats()

        assert stats["total"] == 1
        assert stats["active"] == 1
        assert stats["inactive"] == 0

    def test_multiple_listings(self, store):
        """Multiple listings are handled correctly."""
        listings = [
            Listing(
                id="1",
                url="https://www.kv.ee/1.html",
                title="Apt 1",
                deal_type="sale",
            ),
            Listing(
                id="2",
                url="https://www.kv.ee/2.html",
                title="Apt 2",
                deal_type="sale",
            ),
            Listing(
                id="3",
                url="https://www.kv.ee/3.html",
                title="Apt 3",
                deal_type="rent",
            ),
        ]

        added, updated, unchanged = store.merge_listings(listings)

        assert added == 3
        assert store.get_stats()["total"] == 3

    def test_clear(self, store, sample_listing, temp_csv):
        """Clear removes CSV file."""
        store.merge_listings([sample_listing])
        assert temp_csv.exists()

        store.clear()
        assert not temp_csv.exists()
