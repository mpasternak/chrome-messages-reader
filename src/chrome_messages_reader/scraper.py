"""DOM scraping logic for Google Messages for Web."""

import os
import sys

from playwright.sync_api import TimeoutError as PlaywrightTimeout


def wait_for_conversations(page, timeout_ms):
    """Wait for the conversation list to appear. Returns the working CSS selector."""
    selectors = [
        "mws-conversation-list-item",
        "a[href*='conversation']",
        "[data-e2e-conversation-list-item]",
        "mw-conversation-list-item",
    ]
    for selector in selectors:
        try:
            page.wait_for_selector(selector, timeout=timeout_ms)
            return selector
        except PlaywrightTimeout:
            continue

    found = page.evaluate("""() => {
        const candidates = [
            ...document.querySelectorAll('[role="listitem"]'),
            ...document.querySelectorAll('[role="option"]'),
            ...document.querySelectorAll('[data-conversation-id]'),
        ];
        if (candidates.length > 0) return candidates[0].tagName.toLowerCase();
        return null;
    }""")
    return found


def wait_for_messages(page, timeout_ms):
    """Wait for message elements to appear in the open conversation."""
    selectors = [
        "mws-message-wrapper",
        "mws-message-part",
        "[data-message-id]",
        "mws-text-message-part",
        ".message-text",
        "[class*='message-content']",
        "mws-message-list mws-message-wrapper",
    ]
    for selector in selectors:
        try:
            page.wait_for_selector(selector, timeout=timeout_ms)
            return selector
        except PlaywrightTimeout:
            continue
    return None


def find_conversation_url(page, conv_selector, contact_name):
    """Find a conversation URL by contact name."""
    return page.evaluate("""([selector, name]) => {
        const items = document.querySelectorAll(selector);
        for (const item of items) {
            if (item.innerText.includes(name)) {
                const link = item.querySelector('a[href*="conversations/"]')
                    || item.closest('a[href*="conversations/"]');
                if (link) return link.getAttribute('href');
                if (item.tagName === 'A') return item.getAttribute('href');
            }
        }
        return null;
    }""", [conv_selector, contact_name])


def open_conversation(page, conv_selector, contact_name):
    """Click on a conversation by contact name. Returns the conversation path or None."""
    path = find_conversation_url(page, conv_selector, contact_name)
    if not path:
        return None

    link = page.query_selector(f'a[href="{path}"]')
    if link:
        link.click()
    else:
        page.click(f'{conv_selector}:has-text("{contact_name}")')
    return path


def scrape_message_texts(page):
    """Scrape all message texts from the currently open conversation."""
    return page.evaluate("""() => {
        const texts = [];
        const selectors = [
            'mws-message-wrapper',
            'mws-message-part',
            '[data-message-id]',
            'mws-text-message-part',
            '.message-text',
            '[class*="message-content"]',
            'mws-message-list mws-message-wrapper',
        ];
        for (const selector of selectors) {
            const els = document.querySelectorAll(selector);
            if (els.length > 0) {
                for (const el of els) {
                    const text = el.innerText?.trim();
                    if (text) texts.push(text);
                }
                return texts;
            }
        }
        const main = document.querySelector(
            'mws-messages-list, mws-conversation, [role="main"]'
        );
        if (main) {
            texts.push('FULL_MAIN_TEXT:' + main.innerText);
        }
        return texts;
    }""")


def dump_dom(page, label="page"):
    """Dump full page HTML to a file for inspection."""
    html = page.content()
    dump_path = os.path.join(os.getcwd(), f"dom_dump_{label}.html")
    with open(dump_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  DOM dumped to {dump_path} ({len(html)} bytes)", file=sys.stderr)
