# Plan: Kv.ee Anti-Bot Handling & Parser Alignment

## Context
- No git remote is configured in this repo, so `git fetch master` cannot be performed here.
- Live kv.ee requests return HTTP 403 when browser-like headers are missing, indicating anti-bot gating.
- Parser fixtures are needed to mirror the real search-results DOM before updating selectors.
- Parser expectations in tests must align with the real-world HTML once captured.
- Fetcher configuration should include browser-like headers and potentially a headless fallback if 403 persists.

## Files to Create/Modify
- `tests/fixtures/kv_ee_search_results.html` — captured real kv.ee search results HTML fixture for parser tests.
- `src/kv_pet/parser.py` — update selectors to match real DOM structure (e.g., listing card container, price, address fields).
- `tests/test_parser.py` — update expected parsed fields to match the new fixture structure.
- `src/kv_pet/fetcher.py` — ensure request headers emulate a browser and optionally add a headless fallback path.
- `src/kv_pet/config.py` — define default browser-like headers (user agent, accept, accept-language, etc.) and any fallback config.
- `src/kv_pet/cli.py` — use the inspect command to validate live-site connectivity and log/handle 403s.
- `docs/...` or `README.md` — document anti-bot handling expectations and fixture provenance.

## Implementation Steps
1. [ ] Capture a real kv.ee search results HTML page into `tests/fixtures/kv_ee_search_results.html` (record the URL, query parameters, and capture timestamp).
2. [ ] Update parser selectors in `src/kv_pet/parser.py` (e.g., functions/classes parsing listing cards and key fields) to match the captured DOM.
3. [ ] Align `tests/test_parser.py` expectations with the new fixture content, including any updated field names or values.
4. [ ] Revisit `src/kv_pet/config.py` to define browser-like headers and expose configuration for header overrides or fallback toggles.
5. [ ] Update `src/kv_pet/fetcher.py` to apply the new headers and define a headless-browser fallback strategy if 403 persists.
6. [ ] Use the CLI inspect command in `src/kv_pet/cli.py` to validate live connectivity and confirm 403 handling/logging behavior.
7. [ ] Update documentation (e.g., `README.md` or `docs/`) with notes on anti-bot behavior and fixture provenance.
✅ Verify by running: python -m pytest tests/test_parser.py; python -m kv_pet.cli inspect --url "https://kv.ee/" (or equivalent inspect command)

## Technical Constraints
- Use only browser-like headers (User-Agent, Accept, Accept-Language, Referer) without adding third-party scraping dependencies.
- Keep fixture data in `tests/fixtures/` and ensure it is a real capture, not synthetic HTML.
- Avoid altering public CLI semantics unless required for the inspect connectivity check.

## Dependencies
- No new dependencies

## Notes / Edge Cases
- kv.ee may block based on IP or missing JS; be prepared to document a headless fallback.
- Ensure fixture updates do not embed sensitive data; consider redacting personally identifiable details if present.
- Update tests to be deterministic even if the live site changes later.

## Claude Code Handoff
- Save this plan to `.plans/current.md`.
- Claude Code command: `claude "Read .plans/current.md and implement the plan step by step"`
- While implementing:
  1. Read the full plan first
  2. Execute steps in order
  3. Check off completed items
  4. Record deviations/blockers directly in the plan file
