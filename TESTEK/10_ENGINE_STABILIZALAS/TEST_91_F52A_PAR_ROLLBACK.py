"""
F5.2-A: rollback_copied_files / rollback_renamed_files — pár IO, GUI nélkül.
"""
from pathlib import Path
import sys
import shutil
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from renamer_engine import rollback_copied_files, rollback_renamed_files


class TestF52APairRollback(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_f52a_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_copied_dests_deleted_sources_untouched(self):
        src_a = self.tmp / "src_a.bin"
        src_b = self.tmp / "src_b.bin"
        src_a.write_bytes(b"SRC_A")
        src_b.write_bytes(b"SRC_B")
        dest_a = self.tmp / "out_a.bin"
        dest_b = self.tmp / "out_b.bin"
        dest_a.write_bytes(b"SRC_A")
        dest_b.write_bytes(b"SRC_B")
        rollback_copied_files([dest_a, dest_b])
        self.assertFalse(dest_a.exists())
        self.assertFalse(dest_b.exists())
        self.assertEqual(src_a.read_bytes(), b"SRC_A")
        self.assertEqual(src_b.read_bytes(), b"SRC_B")

    def test_copied_does_not_delete_part_or_unlisted(self):
        dest = self.tmp / "out.bin"
        part = Path(str(dest) + ".part")
        other = self.tmp / "keep.bin"
        dest.write_bytes(b"DEST")
        part.write_bytes(b"PART")
        other.write_bytes(b"KEEP")
        rollback_copied_files([dest])
        self.assertFalse(dest.exists())
        self.assertTrue(part.exists())
        self.assertEqual(other.read_bytes(), b"KEEP")

    def test_copied_swallows_missing_and_continues(self):
        missing = self.tmp / "gone.bin"
        kept = self.tmp / "exists.bin"
        kept.write_bytes(b"X")
        rollback_copied_files([missing, kept])
        self.assertFalse(kept.exists())

    def test_renamed_restored_in_reverse(self):
        old_a = self.tmp / "old_a.bin"
        old_b = self.tmp / "old_b.bin"
        new_a = self.tmp / "new_a.bin"
        new_b = self.tmp / "new_b.bin"
        new_a.write_bytes(b"A")
        new_b.write_bytes(b"B")
        order = []
        orig_rename = Path.rename

        def tracking_rename(self, target):
            order.append((self.name, Path(target).name))
            return orig_rename(self, target)

        Path.rename = tracking_rename
        try:
            rollback_renamed_files([(old_a, new_a), (old_b, new_b)])
        finally:
            Path.rename = orig_rename

        self.assertEqual(order, [("new_b.bin", "old_b.bin"), ("new_a.bin", "old_a.bin")])
        self.assertTrue(old_a.exists())
        self.assertTrue(old_b.exists())
        self.assertFalse(new_a.exists())
        self.assertFalse(new_b.exists())
        self.assertEqual(old_a.read_bytes(), b"A")
        self.assertEqual(old_b.read_bytes(), b"B")

    def test_renamed_skips_missing_new_and_continues(self):
        old_a = self.tmp / "old_a.bin"
        new_a = self.tmp / "new_a.bin"
        old_b = self.tmp / "old_b.bin"
        new_b = self.tmp / "new_b.bin"
        new_b.write_bytes(b"B")
        rollback_renamed_files([(old_a, new_a), (old_b, new_b)])
        self.assertFalse(new_a.exists())
        self.assertTrue(old_b.exists())
        self.assertEqual(old_b.read_bytes(), b"B")


if __name__ == "__main__":
    unittest.main(verbosity=2)
