# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync --extra test

# Install Playwright browser
uv run playwright install chromium

# Run the tool
uv run chrome-messages-reader          # interactive
uv run chrome-messages-reader --auto   # non-interactive

# Run tests
uv run pytest -v

# Run a single test
uv run pytest tests/test_parsers.py -v
uv run pytest tests/test_parsers.py::test_name -v

# Lint
uv run ruff check src/ tests/
```

## Architecture

macOS-only CLI tool that scrapes SMS messages from Google Messages for Web using Playwright and Chrome DevTools Protocol (CDP). Currently extracts PZePUAP (Polish government e-signature) codes.

**Flow:** Close Chrome → clone profile to temp dir → launch Chrome with `--remote-debugging-port` → connect via CDP with Playwright → navigate to Messages → scrape DOM → output JSON to stdout → cleanup.

Four modules in `src/chrome_messages_reader/`:

- **cli.py** — Entry point (`main()`). Orchestrates the full flow. `CONTACT_NAME` controls which conversation to open.
- **chrome.py** — Chrome process lifecycle: quit via AppleScript (`osascript`), launch with CDP, clone profile data to temp dir. Uses `pgrep`/`open -a` (macOS-specific).
- **scraper.py** — DOM interaction via Playwright. Uses multi-selector fallback patterns (tries several CSS selectors) since Google Messages is a SPA with unstable DOM structure.
- **parsers.py** — Regex extraction of auth/signing codes from message text. Pure functions, no I/O.

**Key patterns:**
- Status messages go to stderr; JSON output goes to stdout.
- Temp Chrome profile is always cleaned up via `finally` block.
- Chrome is conditionally reopened at exit (only if it was running before).
- Scraper functions try multiple CSS selectors sequentially because Google Messages DOM structure changes across versions.
- `--debug-dom` dumps page HTML to `dom_dump_*.html` files for diagnosing selector breakage.

## Testing

Tests are pure unit tests (no browser needed). Only `parsers.py` and `chrome.py` helpers have tests. Scraper/CLI testing requires a real Chrome + Messages session and is not automated.
