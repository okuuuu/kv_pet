# Plan: KV Listing Detail Field Parsing

## Context
- Git remote check found no configured remotes, so fetching `master` was skipped per instruction.
- Condition and energy certificate values are present in the listing detail fixture as meta table rows (e.g., “Seisukord” and “Energiamärgis”) but are not currently parsed into CSV fields.
- The current condition extraction only inspects search result excerpts, which yields mostly “new” values and misses the detailed condition value.
- On-hold listings (“Broneeritud”) appear in the inactive fixture via overlay/status text and meta table labels, but `is_active` does not reflect this.
- New parsing should use the provided fixtures `kv_ee_search_example.html` and `kv_ee_inactive.html` to drive correct extraction and status handling.

## Files to Create/Modify
- `src/kv_pet/parser.py` — parse condition and energy certificate from listing detail meta table; detect “Broneeritud” status and map to RESERVED.
- `tests/test_parser.py` — add tests for listing detail parsing (condition, energy certificate) and reserved status detection.
- `tests/fixtures/kv_ee_search_example.html` — fixture used to validate condition/energy certificate parsing (no changes expected unless missing markup).
- `tests/fixtures/kv_ee_inactive.html` — fixture used to validate reserved detection (no changes expected unless missing markup).

## Implementation Steps
1. [ ] Inspect `kv_ee_search_example.html` to identify the meta table selectors/labels used for condition and energy certificate (e.g., “Seisukord”, “Energiamärgis”) and note any English equivalents.
2. [ ] Implement or extend `parse_listing_page` (and any helper) to extract condition and energy certificate from the meta table, preferring explicit table values over excerpt heuristics.
3. [ ] Implement reserved detection in `parse_listing_page` using indicators in `kv_ee_inactive.html` (e.g., “BRONEERITUD” overlay text or “(Broneeritud)” in meta table headers) and map `is_active` to a RESERVED status per CSV expectations.
4. [ ] Update `Listing`/CSV mapping if needed to represent RESERVED cleanly without breaking existing `is_active` consumers.
5. [ ] Add tests to `tests/test_parser.py` that parse the fixtures and assert condition, energy certificate, and reserved status values.
✅ Verify by running: python -m pytest

## Technical Constraints
- Avoid brittle selectors; prefer semantic table labels and normalize for Estonian/English variants.
- Keep existing search-results parsing intact; detailed fields should come from listing detail pages when available.
- Preserve CSV schema expectations while adding RESERVED status handling.

## Dependencies
- No new dependencies

## Notes / Edge Cases
- Listings may omit energy certificate; ensure parser returns `None` rather than incorrect defaults.
- Condition text may include synonyms (e.g., “Heas korras”, “good condition”); normalize consistently.
- Reserved status may appear in multiple places; treat any clear “Broneeritud” indicator as reserved even if other fields are present.

## Claude Code Handoff
- Save this plan to `.plans/current.md`.
- Claude Code command: `claude "Read .plans/current.md and implement the plan step by step"`
- While implementing:
  1. Read the full plan first
  2. Execute steps in order
  3. Check off completed items
  4. Record deviations/blockers directly in the plan file
