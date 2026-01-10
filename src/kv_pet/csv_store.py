"""CSV storage with schema enforcement and merge logic."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import CSV_COLUMNS, DEFAULT_CSV_PATH, OUTPUT_DIR
from .parser import Listing


class CsvStore:
    """CSV store for listing data with merge and deduplication."""

    def __init__(self, csv_path: Optional[Path] = None):
        self.csv_path = csv_path or DEFAULT_CSV_PATH
        self._ensure_output_dir()

    def _ensure_output_dir(self) -> None:
        """Create output directory if it doesn't exist."""
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)

    def read_all(self) -> dict[str, dict]:
        """Read all listings from CSV, keyed by ID."""
        if not self.csv_path.exists():
            return {}

        listings = {}
        with open(self.csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                listing_id = row.get("id")
                if listing_id:
                    listings[listing_id] = row

        return listings

    def merge_listings(
        self, new_listings: list[Listing], mark_missing_inactive: bool = False
    ) -> tuple[int, int, int]:
        """Merge new listings with existing data.

        Returns (added, updated, unchanged) counts.
        """
        existing = self.read_all()
        now = datetime.utcnow().isoformat()

        added = 0
        updated = 0
        unchanged = 0
        seen_ids = set()

        for listing in new_listings:
            seen_ids.add(listing.id)
            new_data = listing.to_dict()

            if listing.id in existing:
                old_data = existing[listing.id]
                merged = self._merge_row(old_data, new_data, now)
                if merged != old_data:
                    existing[listing.id] = merged
                    updated += 1
                else:
                    unchanged += 1
            else:
                new_data["first_seen"] = now
                new_data["last_seen"] = now
                existing[listing.id] = new_data
                added += 1

        if mark_missing_inactive:
            for listing_id, data in existing.items():
                if listing_id not in seen_ids and data.get("is_active") == "true":
                    data["is_active"] = "false"
                    data["last_seen"] = now

        self._write_all(existing)
        return added, updated, unchanged

    def _merge_row(self, old: dict, new: dict, now: str) -> dict:
        """Merge old and new row data, preserving first_seen."""
        merged = old.copy()

        for key, new_value in new.items():
            if key == "first_seen":
                continue
            if key == "last_seen":
                merged[key] = now
                continue
            if new_value is not None and new_value != "" and new_value != "None":
                merged[key] = new_value

        return merged

    def _write_all(self, listings: dict[str, dict]) -> None:
        """Write all listings to CSV in schema order."""
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
            writer.writeheader()

            for listing_id in sorted(listings.keys()):
                row = listings[listing_id]
                cleaned = {k: (v if v is not None else "") for k, v in row.items()}
                writer.writerow(cleaned)

    def get_stats(self) -> dict:
        """Get statistics about stored listings."""
        listings = self.read_all()
        active = sum(1 for l in listings.values() if l.get("is_active") == "true")
        return {
            "total": len(listings),
            "active": active,
            "inactive": len(listings) - active,
        }

    def clear(self) -> None:
        """Remove CSV file."""
        if self.csv_path.exists():
            self.csv_path.unlink()
