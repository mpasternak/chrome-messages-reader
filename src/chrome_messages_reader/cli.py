"""Command-line entry point."""

import argparse
import json
import shutil
import sys

from playwright.sync_api import sync_playwright

from .chrome import (
    CDP_PORT,
    create_temp_profile,
    ensure_chrome_closed,
    launch_chrome_with_debugging,
    reopen_chrome,
)
from .parsers import parse_pzepuap_messages
from .scraper import (
    dump_dom,
    open_conversation,
    scrape_message_texts,
    wait_for_conversations,
    wait_for_messages,
)

MESSAGES_URL = "https://messages.google.com/web/"
CONTACT_NAME = "PZePUAP"


def main():
    parser = argparse.ArgumentParser(
        description="Read PZePUAP codes from Google Messages for Web"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (default: headed)",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Automatically close/reopen Chrome without asking",
    )
    parser.add_argument(
        "--wait-timeout",
        type=int,
        default=30,
        help="Timeout in seconds for waiting for page load (default: 30)",
    )
    parser.add_argument(
        "--debug-dom",
        action="store_true",
        help="Dump DOM snapshots to HTML files for debugging",
    )
    args = parser.parse_args()

    should_reopen = ensure_chrome_closed(args.auto)
    timeout_ms = args.wait_timeout * 1000

    print("Creating temp Chrome profile...", file=sys.stderr)
    tmp_profile = create_temp_profile()
    chrome_proc = launch_chrome_with_debugging(tmp_profile, args.headless)

    try:
        with sync_playwright() as p:
            print("Connecting to Chrome via CDP...", file=sys.stderr)
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP_PORT}")
            context = browser.contexts[0]

            page = context.new_page()
            for other_page in context.pages:
                if other_page != page:
                    other_page.close()

            print(f"Navigating to {MESSAGES_URL}...", file=sys.stderr)
            page.goto(MESSAGES_URL, wait_until="domcontentloaded", timeout=timeout_ms)
            print(f"  Title: {page.title()}", file=sys.stderr)
            page.wait_for_load_state("load", timeout=timeout_ms)

            if args.debug_dom:
                dump_dom(page, "after_load")

            print("Waiting for conversations to load...", file=sys.stderr)
            conv_selector = wait_for_conversations(page, timeout_ms)

            if not conv_selector:
                print(
                    "ERROR: Could not find conversation list.\n"
                    "  - Phone not paired? Run without --headless to pair.\n"
                    "  - Use --debug-dom to inspect DOM structure.",
                    file=sys.stderr,
                )
                dump_dom(page, "no_conversations")
                browser.close()
                sys.exit(1)

            print(f"Found conversations (selector: {conv_selector})", file=sys.stderr)

            path = open_conversation(page, conv_selector, CONTACT_NAME)
            if not path:
                print(
                    f"ERROR: Conversation '{CONTACT_NAME}' not found.",
                    file=sys.stderr,
                )
                browser.close()
                sys.exit(1)

            print(f"Opened {CONTACT_NAME} conversation, loading messages...", file=sys.stderr)
            wait_for_messages(page, timeout_ms)

            if args.debug_dom:
                dump_dom(page, "conversation_opened")

            texts = scrape_message_texts(page)
            print(f"Scraped {len(texts)} message elements", file=sys.stderr)

            results = parse_pzepuap_messages(texts)
            print(json.dumps(results, ensure_ascii=False, indent=2))

            browser.close()
    finally:
        chrome_proc.terminate()
        chrome_proc.wait(timeout=5)
        shutil.rmtree(tmp_profile, ignore_errors=True)
        if should_reopen:
            reopen_chrome()

    print("Done.", file=sys.stderr)
