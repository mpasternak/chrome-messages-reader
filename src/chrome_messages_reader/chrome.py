"""Chrome process management — quit, launch with CDP, profile cloning."""

import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

CHROME_PROFILE_DIR = os.path.expanduser(
    "~/Library/Application Support/Google/Chrome"
)
CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CDP_PORT = 9222

# Files/dirs to copy from the real Chrome profile into the temp one.
# IndexedDB, Local Storage, Service Worker are copied as directory trees;
# the rest are individual files.
_COPY_DIRS = [
    ("IndexedDB/https_messages.google.com_0.indexeddb.leveldb",),
    ("Local Storage",),
    ("Service Worker",),
]
_COPY_FILES = [
    "Cookies",
    "Cookies-journal",
    "Preferences",
    "Secure Preferences",
    "Login Data",
    "Login Data-journal",
    "Web Data",
    "Web Data-journal",
]


def is_chrome_running():
    result = subprocess.run(["pgrep", "-f", "Google Chrome"], capture_output=True)
    return result.returncode == 0


def quit_chrome():
    """Gracefully quit Chrome via AppleScript and wait for it to close."""
    subprocess.run(
        ["osascript", "-e", 'tell application "Google Chrome" to quit'],
        capture_output=True,
    )
    for _ in range(20):
        time.sleep(0.5)
        if not is_chrome_running():
            return True
    print("ERROR: Chrome did not close within 10 seconds.", file=sys.stderr)
    return False


def ensure_chrome_closed(auto):
    """Ensure Chrome is closed. Returns True if it was running (should be reopened later)."""
    if not is_chrome_running():
        return False

    if auto:
        print("Closing Chrome (--auto)...", file=sys.stderr)
    else:
        answer = input("Chrome is running. Close it? [y/n] ").strip().lower()
        if answer not in ("t", "y", "tak", "yes"):
            print("Cancelled.", file=sys.stderr)
            sys.exit(1)
        print("Closing Chrome...", file=sys.stderr)

    if not quit_chrome():
        sys.exit(1)
    return True


def reopen_chrome():
    subprocess.Popen(["open", "-a", "Google Chrome"])
    print("Chrome reopened.", file=sys.stderr)


def create_temp_profile():
    """Clone messages.google.com data into a temporary Chrome profile.

    Chrome refuses ``--remote-debugging-port`` on its default profile,
    so we create a throwaway copy containing only the data we need.
    """
    tmp_profile = tempfile.mkdtemp(prefix="chrome_messages_")
    default_src = os.path.join(CHROME_PROFILE_DIR, "Default")
    default_dst = os.path.join(tmp_profile, "Default")
    os.makedirs(default_dst, exist_ok=True)

    for (subdir,) in _COPY_DIRS:
        src = os.path.join(default_src, subdir)
        if os.path.exists(src):
            print(f"  Copying {subdir}...", file=sys.stderr)
            shutil.copytree(src, os.path.join(default_dst, subdir))

    for fname in _COPY_FILES:
        src = os.path.join(default_src, fname)
        if os.path.exists(src):
            print(f"  Copying {fname}...", file=sys.stderr)
            shutil.copy2(src, os.path.join(default_dst, fname))

    return tmp_profile


def launch_chrome_with_debugging(user_data_dir, headless=False):
    """Launch Chrome with ``--remote-debugging-port`` and wait for CDP."""
    cmd = [
        CHROME_PATH,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--disable-session-crashed-bubble",
        "--hide-crash-restore-bubble",
        "--noerrdialogs",
    ]
    if headless:
        cmd.append("--headless=new")

    print(f"Launching Chrome with debugging on port {CDP_PORT}...", file=sys.stderr)
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for i in range(30):
        time.sleep(1)
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/version")
            print(f"  Chrome ready (took {i + 1}s)", file=sys.stderr)
            return proc
        except Exception:
            pass

    print("ERROR: Chrome did not start with debugging port.", file=sys.stderr)
    proc.kill()
    sys.exit(1)
