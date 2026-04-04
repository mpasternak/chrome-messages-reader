"""Message text parsers — extract structured data from raw SMS text."""

import re

AUTH_CODE_RE = re.compile(
    r"Kod autoryzacyjny nr\s+(\S+)\s+z\s+(\S+):\s+(\S+)"
)
SIGNING_CODE_RE = re.compile(
    r"Podpisanie dokumentu:\s+([^,]+),\s*godz\.?\s*(\S+)\.\s*Kod:\s+(\S+)"
)


def parse_pzepuap_messages(texts):
    """Extract PZePUAP auth and signing codes from raw message texts.

    Returns a list of dicts, each with a ``type`` key (``auth_code`` or
    ``signing_code``) and the extracted fields.  Messages that don't match
    either pattern are silently skipped.
    """
    results = []
    for text in texts:
        m = AUTH_CODE_RE.search(text)
        if m:
            results.append({
                "type": "auth_code",
                "number": m.group(1),
                "date": m.group(2),
                "code": m.group(3),
            })
            continue
        m = SIGNING_CODE_RE.search(text)
        if m:
            results.append({
                "type": "signing_code",
                "date": m.group(1).strip(),
                "time": m.group(2),
                "code": m.group(3),
            })
    return results
