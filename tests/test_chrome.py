"""Tests for chrome_messages_reader.chrome — profile cloning logic."""

import os

from chrome_messages_reader import chrome


def _create_fake_profile(base_dir):
    """Create a minimal fake Chrome profile directory."""
    default = os.path.join(base_dir, "Default")
    os.makedirs(default)

    # Create dirs that should be copied
    idb_dir = os.path.join(
        default, "IndexedDB", "https_messages.google.com_0.indexeddb.leveldb"
    )
    os.makedirs(idb_dir)
    with open(os.path.join(idb_dir, "000001.ldb"), "w") as f:
        f.write("fake-leveldb-data")

    ls_dir = os.path.join(default, "Local Storage", "leveldb")
    os.makedirs(ls_dir)
    with open(os.path.join(ls_dir, "000001.log"), "w") as f:
        f.write("fake-localstorage")

    sw_dir = os.path.join(default, "Service Worker")
    os.makedirs(sw_dir)
    with open(os.path.join(sw_dir, "Database"), "w") as f:
        f.write("fake-sw")

    # Create files that should be copied
    for fname in ("Cookies", "Preferences", "Login Data"):
        with open(os.path.join(default, fname), "w") as f:
            f.write(f"fake-{fname}")

    # Create a file that should NOT be copied
    with open(os.path.join(default, "History"), "w") as f:
        f.write("should-not-be-copied")

    return base_dir


def test_create_temp_profile_copies_expected_files(tmp_path, monkeypatch):
    fake_profile = _create_fake_profile(str(tmp_path / "chrome_profile"))
    monkeypatch.setattr(chrome, "CHROME_PROFILE_DIR", fake_profile)

    tmp_profile = chrome.create_temp_profile()

    try:
        dst_default = os.path.join(tmp_profile, "Default")
        assert os.path.isdir(dst_default)

        # IndexedDB should be copied
        idb = os.path.join(
            dst_default, "IndexedDB",
            "https_messages.google.com_0.indexeddb.leveldb",
            "000001.ldb",
        )
        assert os.path.isfile(idb)

        # Local Storage should be copied
        ls = os.path.join(dst_default, "Local Storage", "leveldb", "000001.log")
        assert os.path.isfile(ls)

        # Service Worker should be copied
        sw = os.path.join(dst_default, "Service Worker", "Database")
        assert os.path.isfile(sw)

        # Individual files should be copied
        assert os.path.isfile(os.path.join(dst_default, "Cookies"))
        assert os.path.isfile(os.path.join(dst_default, "Preferences"))
        assert os.path.isfile(os.path.join(dst_default, "Login Data"))

        # History should NOT be copied
        assert not os.path.exists(os.path.join(dst_default, "History"))
    finally:
        import shutil
        shutil.rmtree(tmp_profile, ignore_errors=True)


def test_create_temp_profile_handles_missing_files(tmp_path, monkeypatch):
    """If some expected files/dirs don't exist, they are silently skipped."""
    fake_profile = str(tmp_path / "chrome_profile")
    default = os.path.join(fake_profile, "Default")
    os.makedirs(default)
    # Only create Cookies — everything else is missing
    with open(os.path.join(default, "Cookies"), "w") as f:
        f.write("fake")

    monkeypatch.setattr(chrome, "CHROME_PROFILE_DIR", fake_profile)

    tmp_profile = chrome.create_temp_profile()

    try:
        dst_default = os.path.join(tmp_profile, "Default")
        assert os.path.isfile(os.path.join(dst_default, "Cookies"))
        assert not os.path.exists(os.path.join(dst_default, "IndexedDB"))
    finally:
        import shutil
        shutil.rmtree(tmp_profile, ignore_errors=True)
