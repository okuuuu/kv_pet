# Plan: KV.ee Listing Parser & CSV Updater

## Context
- Build a parser for kv.ee property listings that can search by user-specified criteria and update a local CSV in the required format.

- The site has no public API, so the first implementation work must focus on inspecting page structure, request patterns, and access constraints.

- Assume we must respect robots/terms, rate limits, and handle potential anti-bot measures before implementing full crawling.

- Output is a local CSV file in a defined schema (to be documented early).

## Files to Create/Modify
- `plans/current.md` — store this plan for Claude Code execution.

- `docs/kv_ee_research.md` — capture findings about page structure, request parameters, and accessibility constraints.

- `docs/csv_schema.md` — define the required CSV columns, ordering, and data types.

- `src/kv_pet/config.py` — configuration defaults (base URL, search params, output path).

- `src/kv_pet/fetcher.py` — HTTP access layer (requests/session, throttling, headers).

- `src/kv_pet/parser.py` — HTML parsing of listing pages/search results.

- `src/kv_pet/criteria.py` — criteria normalization/validation for search inputs.

- `src/kv_pet/csv_store.py` — CSV read/update/write logic with schema enforcement.

- `src/kv_pet/cli.py` — command-line entry point for running searches and updating CSV.

- `tests/test_parser.py` — parsing tests using saved HTML fixtures.

- `tests/test_csv_store.py` — CSV update/merge tests with sample files.

- `tests/fixtures/` — captured HTML pages and sample CSVs for repeatable tests.

- `README.md` — usage and setup instructions (if absent or minimal today).

## Implementation Steps
<!-- Atomic tasks, one per line, in order -->
1. [x] Read CLAUDE.md and .plans/current.md to confirm workflow requirements and update this plan file with the final approved steps.

2. [x] Create docs/kv_ee_research.md and document initial manual inspection targets: search page URL patterns, query parameters, pagination, listing URLs, and any robots/terms constraints.

3. [x] Identify CSV requirements (columns, required fields, data types, deduping key) and record in docs/csv_schema.md.

4. [x] Define the high-level package layout under src/kv_pet/ and add a minimal package initializer (no implementation yet).

5. [x] Add config.py scaffolding for base URLs, default headers, throttling settings, and CSV output path.

6. [x] Implement criteria.py to normalize/validate search criteria and convert to query parameters.

7. [x] Implement fetcher.py for HTTP GET with session reuse, basic backoff, and rate limiting knobs.

8. [x] Implement parser.py to extract listing attributes (id/url/title/price/area/location/etc.) from HTML search results.

9. [x] Implement csv_store.py to read existing CSV, merge new rows with stable deduping key, and write in schema order.

10. [x] Implement cli.py to accept criteria flags, run fetch+parse, and update CSV.

11. [x] Capture representative HTML pages into tests/fixtures/ and add parser tests for core fields.

12. [x] Add CSV store tests covering schema ordering and merge behavior.

13. [x] Update README.md with setup, usage examples, and constraints (rate limits, allowed usage).

## Technical Constraints
- Use plain HTTP requests and HTML parsing first; only introduce a headless browser if the site renders results via JS.

- Respect robots/terms; include conservative delays and avoid excessive concurrency.

- Keep the CSV schema stable and explicit; do not infer columns dynamically.

- Do not implement a full crawler; scope is “search by criteria → update CSV”.

- Avoid large refactors to repository structure; keep to src/kv_pet/ layout.

## Dependencies
- If needed: requests (HTTP), beautifulsoup4 or lxml (HTML parsing), pandas (CSV manipulation) — add only if a clear parsing or schema need arises.

## Notes
- kv.ee may use anti-bot protections or require JS rendering; plan for fallback to browser automation if needed.

- Pagination and sorting parameters must be captured to ensure complete result sets.

- Listings can change or disappear; CSV updates should handle removed listings without deleting old rows unless explicitly requested.

- Locale-specific number formats (spaces, commas, “€” symbol) must be normalized.
