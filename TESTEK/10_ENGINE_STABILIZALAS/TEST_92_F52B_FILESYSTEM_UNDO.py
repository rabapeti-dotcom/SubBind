"""
F5.2-B: copy/inplace history undo fájlművelet — GUI és Item nélkül.
"""
from pathlib import Path
import os
import sys
import shutil
import tempfile
import time
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from renamer_engine import (
    verify_copy_undo,
    apply_copy_undo,
    verify_inplace_undo,
    apply_inplace_undo,
)


def copy_change(src, dest):
    dest.write_bytes(src.read_bytes())
    st = dest.stat()
    return {
        "old": str(src),
        "new": str(dest),
        "action": "copy",
        "size": st.st_size,
        "mtime_ns": st.st_mtime_ns,
    }


class TestF52BFilesystemUndo(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_f52b_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_copy_undo_deletes_dest_keeps_source(self):
        src = self.tmp / "src.bin"
        dest = self.tmp / "out.bin"
        src.write_bytes(b"KEEP_SOURCE")
        change = copy_change(src, dest)
        self.assertIsNone(verify_copy_undo([change]))
        apply_copy_undo([change])
        self.assertFalse(dest.exists())
        self.assertEqual(src.read_bytes(), b"KEEP_SOURCE")

    def test_copy_undo_rejects_missing_new(self):
        src = self.tmp / "src.bin"
        dest = self.tmp / "out.bin"
        src.write_bytes(b"X")
        change = copy_change(src, dest)
        dest.unlink()
        kind, path = verify_copy_undo([change])
        self.assertEqual(kind, "missing")
        self.assertEqual(Path(path), dest)

    def test_copy_undo_rejects_size_or_mtime_change(self):
        src = self.tmp / "src.bin"
        dest = self.tmp / "out.bin"
        src.write_bytes(b"ORIG")
        change = copy_change(src, dest)
        dest.write_bytes(b"CHANGED")
        kind, path = verify_copy_undo([change])
        self.assertEqual(kind, "changed")
        self.assertEqual(Path(path), dest)
        self.assertTrue(dest.exists())

        dest.write_bytes(b"ORIG")
        change = copy_change(src, dest)
        os.utime(dest, (time.time() + 120, time.time() + 120))
        kind, path = verify_copy_undo([change])
        self.assertEqual(kind, "changed")
        apply_copy_undo([])
        self.assertTrue(dest.exists())

    def test_copy_undo_stops_before_any_delete_if_later_file_changed(self):
        src_a = self.tmp / "a.bin"
        src_b = self.tmp / "b.bin"
        dest_a = self.tmp / "out_a.bin"
        dest_b = self.tmp / "out_b.bin"
        src_a.write_bytes(b"A")
        src_b.write_bytes(b"B")
        ch_a = copy_change(src_a, dest_a)
        ch_b = copy_change(src_b, dest_b)
        dest_b.write_bytes(b"B!")
        self.assertEqual(verify_copy_undo([ch_a, ch_b])[0], "changed")
        self.assertTrue(dest_a.exists())
        self.assertTrue(dest_b.exists())

    def test_inplace_undo_renames_back(self):
        old = self.tmp / "old.bin"
        new = self.tmp / "new.bin"
        new.write_bytes(b"DATA")
        changes = [{"old": str(old), "new": str(new), "action": "rename"}]
        self.assertTrue(verify_inplace_undo(changes))
        apply_inplace_undo(changes)
        self.assertTrue(old.exists())
        self.assertFalse(new.exists())
        self.assertEqual(old.read_bytes(), b"DATA")

    def test_inplace_undo_rejects_if_old_exists_or_new_missing(self):
        old = self.tmp / "old.bin"
        new = self.tmp / "new.bin"
        new.write_bytes(b"DATA")
        old.write_bytes(b"STALE")
        changes = [{"old": str(old), "new": str(new)}]
        self.assertFalse(verify_inplace_undo(changes))
        old.unlink()
        new.unlink()
        self.assertFalse(verify_inplace_undo(changes))

    def test_copy_undo_reports_unlink_error_and_continues(self):
        src_a = self.tmp / "a.bin"
        src_b = self.tmp / "b.bin"
        dest_a = self.tmp / "out_a.bin"
        dest_b = self.tmp / "out_b.bin"
        src_a.write_bytes(b"A")
        src_b.write_bytes(b"B")
        ch_a = copy_change(src_a, dest_a)
        ch_b = copy_change(src_b, dest_b)
        original_unlink = Path.unlink

        def failing_unlink(path, *args, **kwargs):
            if path == dest_a:
                raise OSError("Simulated copy undo unlink error")
            return original_unlink(path, *args, **kwargs)

        Path.unlink = failing_unlink
        try:
            failures = apply_copy_undo([ch_a, ch_b])
        finally:
            Path.unlink = original_unlink

        self.assertTrue(dest_a.exists())
        self.assertFalse(dest_b.exists())
        self.assertEqual(src_a.read_bytes(), b"A")
        self.assertEqual(src_b.read_bytes(), b"B")
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["path"], str(dest_a))
        self.assertIn("Simulated copy undo unlink error", failures[0]["error"])

    def test_inplace_undo_reports_rename_error_and_continues(self):
        old_a = self.tmp / "old_a.bin"
        old_b = self.tmp / "old_b.bin"
        new_a = self.tmp / "new_a.bin"
        new_b = self.tmp / "new_b.bin"
        new_a.write_bytes(b"A")
        new_b.write_bytes(b"B")
        changes = [
            {"old": str(old_a), "new": str(new_a), "action": "rename"},
            {"old": str(old_b), "new": str(new_b), "action": "rename"},
        ]
        original_rename = Path.rename

        def failing_rename(path, target):
            if path == new_a:
                raise OSError("Simulated inplace undo rename error")
            return original_rename(path, target)

        Path.rename = failing_rename
        try:
            failures = apply_inplace_undo(changes)
        finally:
            Path.rename = original_rename

        self.assertTrue(new_a.exists())
        self.assertFalse(new_b.exists())
        self.assertTrue(old_b.exists())
        self.assertEqual(old_b.read_bytes(), b"B")
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["old"], str(old_a))
        self.assertEqual(failures[0]["new"], str(new_a))
        self.assertIn("Simulated inplace undo rename error", failures[0]["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
