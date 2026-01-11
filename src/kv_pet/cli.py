"""Command-line interface for kv_pet."""

import argparse
import sys
from pathlib import Path

from .config import DEFAULT_CSV_PATH
from .criteria import SearchCriteria
from .csv_store import CsvStore
from .fetcher import KvFetcher, build_search_url
from .parser import KvParser


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
    search_parser.add_argument("--parish", help="Parish/municipality filter")
    search_parser.add_argument("--city", help="City filter")
    search_parser.add_argument("--price-min", type=int, help="Minimum price")
    search_parser.add_argument("--price-max", type=int, help="Maximum price")
    search_parser.add_argument("--rooms-min", type=int, help="Minimum rooms")
    search_parser.add_argument("--rooms-max", type=int, help="Maximum rooms")
    search_parser.add_argument("--area-min", type=int, help="Minimum area (m²)")
    search_parser.add_argument("--area-max", type=int, help="Maximum area (m²)")
    search_parser.add_argument("--build-year-min", type=int, help="Minimum construction year")
    search_parser.add_argument("--build-year-max", type=int, help="Maximum construction year")
    search_parser.add_argument("--condition", help="Property condition (new, renovated, good)")
    search_parser.add_argument("--building-material", help="Building material (stone, panel, wood)")
    search_parser.add_argument("--energy-certificate", help="Energy certificate class (A, B, C, etc.)")
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
    search_parser.add_argument(
        "--no-headless", action="store_true", help="Disable headless browser fallback"
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
    inspect_parser.add_argument(
        "--no-headless", action="store_true", help="Disable headless browser fallback"
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
        parish=args.parish,
        city=args.city,
        price_min=args.price_min,
        price_max=args.price_max,
        rooms_min=args.rooms_min,
        rooms_max=args.rooms_max,
        area_min=args.area_min,
        area_max=args.area_max,
        build_year_min=args.build_year_min,
        build_year_max=args.build_year_max,
        condition=args.condition,
        building_material=args.building_material,
        energy_certificate=args.energy_certificate,
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

    use_headless = not getattr(args, "no_headless", False)
    store = CsvStore(args.output)
    html_parser = KvParser(deal_type=args.deal_type)
    all_listings = []

    with KvFetcher(use_headless_fallback=use_headless) as fetcher:
        for page in range(1, args.pages + 1):
            criteria.page = page
            url = build_search_url(criteria)
            print(f"Fetching page {page}: {url}")

            result = fetcher.fetch_search_results(criteria)

            if result.is_blocked:
                print(f"  BLOCKED: {result.block_reason}", file=sys.stderr)
                if page == 1:
                    print(
                        "\nTip: The site uses Cloudflare protection. Options:\n"
                        "  1. Install playwright: pip install playwright && playwright install chromium\n"
                        "  2. Manually capture HTML and use as fixture\n"
                        "  3. Try again later (rate limiting)",
                        file=sys.stderr,
                    )
                    return 1
                break

            if result.status_code != 200:
                print(f"  Error: HTTP {result.status_code}", file=sys.stderr)
                if page == 1:
                    return 1
                break

            listings = html_parser.parse_search_results(result.html)
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
    use_headless = not getattr(args, "no_headless", False)

    with KvFetcher(use_headless_fallback=use_headless) as fetcher:
        result = fetcher.fetch_url(args.url)

        print(f"URL: {result.url}")
        print(f"Status: {result.status_code}")
        print(f"Blocked: {result.is_blocked}")
        if result.block_reason:
            print(f"Block reason: {result.block_reason}")
        print(f"Content-Length: {len(result.html)} chars")

        if result.is_blocked:
            print(
                "\nThe site blocked this request. Options:\n"
                "  1. Install playwright: pip install playwright && playwright install chromium\n"
                "  2. Manually save the page from your browser\n",
                file=sys.stderr,
            )

        if args.save:
            args.save.parent.mkdir(parents=True, exist_ok=True)
            args.save.write_text(result.html, encoding="utf-8")
            print(f"Saved to: {args.save}")
        else:
            print("\n--- HTML Preview (first 2000 chars) ---")
            print(result.html[:2000])

    return 0 if not result.is_blocked else 1


if __name__ == "__main__":
    sys.exit(main())
