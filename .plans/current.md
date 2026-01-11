# Plan: Listing detail enrichment and CLI filters

## Context
- Git remote check found no configured remotes; fetch skipped per instruction.
- Listing parsing currently only extracts basic fields from search results, with detailed listing parsing TODO.
- CSV schema already includes county, city, district, build_year, and condition but they are not populated from parsing.
- CLI search parameters include county but omit parish/city and other requested filters.
- Encoding issues likely stem from response decoding when fetching HTML (e.g., Estonian diacritics).

## Files to Create/Modify
- `.plans/current.md` — record the updated plan and findings.
- `.plans/archive/2026-01-10.md` — archived copy of the prior plan (verbatim).
- `src/kv_pet/parser.py` — extend listing parsing to capture county/city/district, build year, condition, and energy certificate.
- `src/kv_pet/config.py` — extend CSV schema to include energy certificate (and any new listing fields if needed).
- `src/kv_pet/criteria.py` — add new search criteria fields and query parameter mapping.
- `src/kv_pet/cli.py` — add CLI arguments for parish/city and new filters.
- `src/kv_pet/fetcher.py` — ensure HTML decoding preserves Estonian characters.

## Implementation Steps
1. [x] Review kv.ee HTML for listing cards and/or listing detail pages to identify selectors for county, city, district, build year, condition, and energy certificate.
2. [x] Update `Listing` dataclass and `to_dict` mapping to include energy certificate (and any missing fields) while keeping CSV output stable.
3. [x] Implement parsing updates in `KvParser` to populate county/city/district, build year, condition, and energy certificate from search results or detail pages.
4. [x] Extend CSV schema in `config.CSV_COLUMNS` to include the new field(s) in output order.
5. [x] Add search filters to `SearchCriteria` and `to_query_params` for building material, energy certificate, condition, parish, and city.
6. [x] Add CLI flags for the new search parameters and wire them into `cmd_search` criteria creation.
7. [x] Fix UTF-8/encoding handling in fetcher responses to prevent mis-decoding Estonian characters.
8. [x] Run formatting/linting/tests if applicable. (36 tests passed)
✅ Verify by running: python -m pytest

## Technical Constraints
- Keep CSV column order consistent with existing schema, adding new fields only as needed.
- Avoid changing fetcher behavior in a way that breaks anti-bot detection or headless fallback.
- Maintain backward compatibility for existing CLI arguments.

## Dependencies
- No new dependencies

## Notes / Edge Cases
- kv.ee may provide location hierarchy and building metadata only on detail pages; if so, consider fetching each listing page when needed.
- Some listings may not have energy certificate or condition; keep fields optional and leave blank when missing.
- Ensure encoding fix handles both HTTP headers and HTML meta charset.

## Implementation Findings (2026-01-11)
- **Location parsing**: Location string from `.description h2 a` splits into: county, city/parish, district, sub-district, address
  - Tallinn format: "Harjumaa, Tallinn, Põhja-Tallinn, Kalamaja, Uus-Volta 7-49"
  - Rural format: "Harjumaa, Saku vald, Saku, Kirsiõue, Soo tee 5-20"
- **Excerpt data**: `p.object-excerpt` contains: floor, ownership type, building material, construction year, condition
  - Building materials found: "stone house", "panel house"
  - Conditions found: "all brand-new", "renovated", "good condition"
- **Energy certificate**: NOT available in search results - only on detail pages (deferred for future implementation)
- **Encoding fix**: Set `response.encoding = 'utf-8'` before accessing `response.text` to prevent chardet mis-detection
- **Bilingual support**: Parser handles both English and Estonian text (korrus/floor, kivimaja/stone house, ehitusaasta/construction year, uus/new, renoveeritud/renovated)

## API Parameter Discovery (2026-01-11)
Analyzed `tests/fixtures/kv_ee_advanced_search.html` to find correct kv.ee parameter names:
- **structure[]**: Building material codes (9=stone, 10=wood, 11=panel, 68=log)
- **c[]**: Condition codes (38=new, 104=good, 39=renovated, 41=satisfactory, 51=needs renovation)
- **energy_certs**: Comma-separated energy classes (A,B,C,D,E,F,G,H)
- **county**: Numeric county codes (1=Harjumaa, 12=Tartumaa, etc.)
- **city[]**, **parish**: Numeric location codes

Updated `criteria.py` to map user-friendly values (e.g., "stone", "renovated") to kv.ee codes. Filters now work correctly.

## Claude Code Handoff
- Save this plan to `.plans/current.md`.
- Claude Code command: `claude "Read .plans/current.md and implement the plan step by step"`
- While implementing:
  1. Read the full plan first
  2. Execute steps in order
  3. Check off completed items
  4. Record deviations/blockers directly in the plan file
