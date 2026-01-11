# Plan: Exclude Recommended Listings From CSV

## Context
- Git remote check found no configured remotes, so fetching `master` was skipped per instruction.
- Search results parsing currently collects all `article[data-object-id]` entries without differentiating recommended sections.
- Recommended listings appear under the h3 heading “Kuulutused, mis võiksid sulle huvi pakkuda” and should be excluded from CSV output.
- CSV output is built directly from parsed listings, so filtering needs to happen during parsing or before merging into storage.

## Files to Create/Modify
- `src/kv_pet/parser.py` — exclude recommended listings by limiting the parsed containers to the main results section or by skipping listings after the recommended heading.
- `tests/fixtures/kv_ee_search_results.html` — add or update a fixture segment that includes the recommended section heading and listings for regression coverage.
- `tests/test_parser.py` — add a test ensuring recommended listings are excluded from `parse_search_results` output.

## Implementation Steps
1. [ ] Inspect the search results HTML (fixture and/or live capture) to locate the DOM structure around the recommended listings heading and identify a reliable boundary or wrapper selector.
2. [ ] Update `KvParser.parse_search_results` to only collect listing containers that belong to the primary results section, or to stop/skip listing cards that appear after the “Kuulutused, mis võiksid sulle huvi pakkuda” heading.
3. [ ] Update/add fixture content to include a recommended section so the parser behavior can be validated.
4. [ ] Add a parser test that loads the fixture and asserts listings under the recommended heading are not returned.
5. [ ] Run the test suite (or at minimum the parser tests) to confirm coverage of the new behavior.
✅ Verify by running: python -m pytest

## Technical Constraints
- Keep parsing resilient to both Estonian and English heading variants if the site localizes the recommended section.
- Avoid false negatives by ensuring the main listings section remains fully parsed.
- Do not change CSV schema or listing model fields for this behavior change.

## Dependencies
- No new dependencies

## Notes / Edge Cases
- The recommended section may not always appear; parsing should behave identically to current output when the heading is absent.
- Recommended listings might share the same `article[data-object-id]` markup as main listings, so the filter should be based on section context rather than card structure alone.

## Claude Code Handoff
- Save this plan to `.plans/current.md`.
- Claude Code command: `claude "Read .plans/current.md and implement the plan step by step"`
- While implementing:
  1. Read the full plan first
  2. Execute steps in order
  3. Check off completed items
  4. Record deviations/blockers directly in the plan file
