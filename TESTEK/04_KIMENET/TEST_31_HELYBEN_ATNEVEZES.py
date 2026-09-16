"""
SubBind – automatizált GUI/engine teszt.
A teszt izolált ideiglenes könyvtárban dolgozik.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from renamer_engine import parse_item, render_template, common_title
except Exception as exc:
    raise RuntimeError(
        f"Nem tölthető be a renamer_engine a projektből: {SRC_ROOT}"
    ) from exc

VIDEO = b"TEST_VIDEO_CONTENT_0.6.1"
SUB = b"TEST_SUBTITLE_CONTENT_0.6.1"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_case(root, *files):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for rel, data in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return root


def parse(path):
    return parse_item(Path(path))


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_test_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def assert_same_file(self, path, digest):
        self.assertEqual(sha256(path), digest, f"A fájl megváltozott: {path}")



class TestInPlaceRename(BaseTest):
    def test_rename_changes_name_only(self):
        src = make_case(self.tmp, ("old.mkv", VIDEO)) / "old.mkv"
        digest = sha256(src)
        dst = self.tmp / "new.mkv"
        src.rename(dst)
        self.assertFalse(src.exists())
        self.assertTrue(dst.exists())
        self.assert_same_file(dst, digest)
if __name__ == "__main__":
    unittest.main(verbosity=2)
