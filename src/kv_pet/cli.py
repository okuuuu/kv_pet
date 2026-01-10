"""Command-line interface for kv_pet."""

import argparse
import sys
from pathlib import Path

from .config import DEFAULT_CSV_PATH
from .criteria import SearchCriteria
from .csv_store import CsvStore
from .fetcher import KvFetcher, build_search_url
from .parser import KvParser, parse_pagination


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="KV.ee property listing parser and CSV updater",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  kv-pet search --deal-type sale --price-max 200000
  kv-pet search --rooms-min 2 --area-min 50 --keyword Tallinn
  kv-pet stats
  kv-pet inspect https://www.kv.ee/12345.html
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search listings and update CSV")
    search_parser.add_argument(
        "--deal-type",
        choices=["sale", "rent"],
        default="sale",
        help="Type of deal (default: sale)",
    )
    search_parser.add_argument("--county", help="County/region filter")
    search_parser.add_argument("--price-min", type=int, help="Minimum price")
    search_parser.add_argument("--price-max", type=int, help="Maximum price")
    search_parser.add_argument("--rooms-min", type=int, help="Minimum rooms")
    search_parser.add_argument("--rooms-max", type=int, help="Maximum rooms")
    search_parser.add_argument("--area-min", type=int, help="Minimum area (m²)")
    search_parser.add_argument("--area-max", type=int, help="Maximum area (m²)")
    search_parser.add_argument("--keyword", help="Keyword/address search")
    search_parser.add_argument(
        "--pages", type=int, default=1, help="Number of pages to fetch (default: 1)"
    )
    search_parser.add_argument(
        "--output", type=Path, default=DEFAULT_CSV_PATH, help="Output CSV path"
    )
    search_parser.add_argument(
        "--dry-run", action="store_true", help="Show URL without fetching"
    )

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show CSV statistics")
    stats_parser.add_argument(
        "--output", type=Path, default=DEFAULT_CSV_PATH, help="CSV path"
    )

    # Inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect a URL and show raw HTML")
    inspect_parser.add_argument("url", help="URL to inspect")
    inspect_parser.add_argument(
        "--save", type=Path, help="Save HTML to file"
    )

    args = parser.parse_args()

    if args.command == "search":
        return cmd_search(args)
    elif args.command == "stats":
        return cmd_stats(args)
    elif args.command == "inspect":
        return cmd_inspect(args)
    else:
        parser.print_help()
        return 0


def cmd_search(args) -> int:
    """Execute search command."""
    criteria = SearchCriteria(
        deal_type=args.deal_type,
        county=args.county,
        price_min=args.price_min,
        price_max=args.price_max,
        rooms_min=args.rooms_min,
        rooms_max=args.rooms_max,
        area_min=args.area_min,
        area_max=args.area_max,
        keyword=args.keyword,
    )

    errors = criteria.validate()
    if errors:
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        return 1

    if args.dry_run:
        for page in range(1, args.pages + 1):
            criteria.page = page
            print(build_search_url(criteria))
        return 0

    store = CsvStore(args.output)
    parser = KvParser(deal_type=args.deal_type)
    all_listings = []

    with KvFetcher() as fetcher:
        for page in range(1, args.pages + 1):
            criteria.page = page
            url = build_search_url(criteria)
            print(f"Fetching page {page}: {url}")

            try:
                response = fetcher.fetch_search_results(criteria)
                response.raise_for_status()
            except Exception as e:
                print(f"Error fetching page {page}: {e}", file=sys.stderr)
                if page == 1:
                    return 1
                break

            listings = parser.parse_search_results(response.text)
            print(f"  Found {len(listings)} listings")
            all_listings.extend(listings)

            if not listings:
                print("  No more results, stopping pagination")
                break

    if all_listings:
        added, updated, unchanged = store.merge_listings(all_listings)
        print(f"\nResults: {added} added, {updated} updated, {unchanged} unchanged")
        print(f"CSV saved to: {args.output}")
    else:
        print("\nNo listings found")

    return 0


def cmd_stats(args) -> int:
    """Show CSV statistics."""
    store = CsvStore(args.output)
    stats = store.get_stats()

    print(f"CSV: {args.output}")
    print(f"Total listings: {stats['total']}")
    print(f"Active: {stats['active']}")
    print(f"Inactive: {stats['inactive']}")

    return 0


def cmd_inspect(args) -> int:
    """Inspect a URL and show/save HTML."""
    with KvFetcher() as fetcher:
        try:
            response = fetcher.fetch_url(args.url)
            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"Content-Length: {len(response.text)} chars")

            if args.save:
                args.save.write_text(response.text, encoding="utf-8")
                print(f"Saved to: {args.save}")
            else:
                print("\n--- HTML Preview (first 2000 chars) ---")
                print(response.text[:2000])

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
