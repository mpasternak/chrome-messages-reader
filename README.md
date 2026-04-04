# chrome-messages-reader

[![CI](https://github.com/mpasternak/chrome-messages-reader/actions/workflows/ci.yml/badge.svg)](https://github.com/mpasternak/chrome-messages-reader/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> **Experimental software — use at your own risk.** While the tool runs a second Chrome instance from a cloned profile, incoming SMS messages may be delivered to the temporary copy instead of your real Chrome session and **could be lost**. Do not use this tool if you cannot afford to miss messages.

Read SMS messages from [Google Messages for Web](https://messages.google.com/web/) by scraping Chrome's local session data with [Playwright](https://playwright.dev/).

Currently extracts **PZePUAP** (Polish government e-signature platform) authorization and document-signing codes. The parser module can be extended to handle other message formats.

## How it works

Google Messages for Web pairs with your Android phone and mirrors SMS conversations in Chrome. The pairing session, cookies and message data are stored in Chrome's profile directory.

This tool:

1. **Closes Chrome** (required — Chrome locks its profile directory)
2. **Copies** the relevant profile data (cookies, IndexedDB, Local Storage) to a temporary directory
3. **Launches Chrome** from the temp profile with `--remote-debugging-port`
4. **Connects via CDP** (Chrome DevTools Protocol) using Playwright
5. **Navigates** to the PZePUAP conversation and scrapes the messages from the DOM
6. **Outputs JSON** to stdout
7. **Cleans up** the temp profile and reopens Chrome if it was running before

## Platform

**macOS only.** Uses `osascript` (AppleScript) to quit Chrome gracefully and `open -a` to relaunch it.

## Tested with

| Component | Version |
|---|---|
| macOS | 26.3 (Tahoe) |
| Google Chrome | 146.0.7680.178 |
| Playwright | 1.58.0 |
| Python | 3.13 |
| Date | 2026-04-04 |

Google Messages for Web is a single-page application whose DOM structure may change without notice. If selectors break, use `--debug-dom` to dump the page HTML and adjust `scraper.py`.

## Installation

Requires [uv](https://docs.astral.sh/uv/) (or pip).

```bash
git clone https://github.com/mpasternak/chrome-messages-reader.git
cd chrome-messages-reader
uv sync
uv run playwright install chromium
```

## Usage

```bash
# Interactive — asks before closing Chrome
uv run chrome-messages-reader

# Automatic — closes and reopens Chrome without prompting
uv run chrome-messages-reader --auto

# Headless (no browser window)
uv run chrome-messages-reader --auto --headless

# Debug — dumps DOM snapshots to dom_dump_*.html files
uv run chrome-messages-reader --auto --debug-dom
```

### Options

| Flag | Description |
|---|---|
| `--auto` | Close/reopen Chrome without asking |
| `--headless` | Run Chrome in headless mode |
| `--wait-timeout N` | Seconds to wait for page load (default: 30) |
| `--debug-dom` | Dump DOM snapshots to HTML files for debugging |

### Output

JSON array on stdout. Status messages go to stderr.

```json
[
  {
    "type": "auth_code",
    "number": "1",
    "date": "03.04.2026",
    "code": "38703276"
  },
  {
    "type": "signing_code",
    "date": "03.04.2026",
    "time": "13:25:17",
    "code": "37933629"
  }
]
```

## Project structure

```
src/chrome_messages_reader/
    cli.py        # Command-line entry point
    chrome.py     # Chrome process management, profile cloning
    scraper.py    # DOM scraping (conversation list, messages)
    parsers.py    # Regex-based message text parsing
```

## Extending

To scrape a different conversation or parse different message formats:

- Change `CONTACT_NAME` in `cli.py`
- Add new regex patterns and parser functions in `parsers.py`

## Limitations

- **macOS only** (AppleScript for Chrome management, hardcoded Chrome path)
- **Chrome must be closed** during scraping (profile locking)
- DOM selectors may break when Google updates the Messages web app
- Only reads messages currently visible in the conversation (no scroll/pagination yet)

## License

MIT
