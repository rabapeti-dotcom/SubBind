"""
F5.1: copy_to_destination — .part másolás, forrás érintetlen, GUI nélkül.
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

from renamer_engine import copy_to_destination

PAYLOAD = b"F51_PART_COPY_PAYLOAD_0.6.1" * 100


class TestF51CopyToDestination(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_f51_"))
        self.src = self.tmp / "src.bin"
        self.src.write_bytes(PAYLOAD)
        self.dest_dir = self.tmp / "out"
        self.dest_dir.mkdir()
        self.dest = self.dest_dir / "dest.bin"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_copies_bytes_and_leaves_source(self):
        src_before = self.src.read_bytes()
        stat_result = copy_to_destination(self.src, self.dest)
        self.assertTrue(self.dest.is_file())
        self.assertEqual(self.dest.read_bytes(), PAYLOAD)
        self.assertEqual(self.src.read_bytes(), src_before)
        self.assertTrue(self.src.is_file())
        self.assertEqual(stat_result.st_size, len(PAYLOAD))
        self.assertFalse(Path(str(self.dest) + ".part").exists())

    def test_progress_callback_receives_counts(self):
        seen = []

        def progress(copied, total):
            seen.append((copied, total))

        copy_to_destination(self.src, self.dest, progress=progress)
        self.assertTrue(seen)
        self.assertEqual(seen[-1][0], len(PAYLOAD))
        self.assertGreaterEqual(seen[-1][1], 1)

    def test_stale_part_is_replaced(self):
        leftover = Path(str(self.dest) + ".part")
        leftover.write_bytes(b"STALE_PART")
        copy_to_destination(self.src, self.dest)
        self.assertEqual(self.dest.read_bytes(), PAYLOAD)
        self.assertFalse(leftover.exists())

    def test_final_destination_stat_error_does_not_fail_copy(self):
        original_stat = Path.stat

        def stat_with_final_destination_error(path, *args, **kwargs):
            if path == self.dest:
                raise OSError("Simulated final destination stat error")
            return original_stat(path, *args, **kwargs)

        Path.stat = stat_with_final_destination_error
        try:
            stat_result = copy_to_destination(self.src, self.dest)
        finally:
            Path.stat = original_stat

        self.assertTrue(self.dest.is_file())
        self.assertEqual(self.dest.read_bytes(), PAYLOAD)
        self.assertFalse(Path(str(self.dest) + ".part").exists())
        self.assertEqual(stat_result.st_size, len(PAYLOAD))

    def test_oserror_cleans_part_and_does_not_write_dest(self):
        missing = self.tmp / "missing.bin"
        with self.assertRaises(OSError):
            copy_to_destination(missing, self.dest)
        self.assertFalse(self.dest.exists())
        self.assertFalse(Path(str(self.dest) + ".part").exists())

    def test_write_oserror_cleans_part_and_does_not_write_dest(self):
        original_open = Path.open

        def exploding_open(path, mode="r", *args, **kwargs):
            handle = original_open(path, mode, *args, **kwargs)
            if "w" in str(mode) and str(path).endswith(".part"):
                def boom(_data):
                    raise OSError("Simulated copy write error")
                handle.write = boom
            return handle

        Path.open = exploding_open
        try:
            with self.assertRaises(OSError):
                copy_to_destination(self.src, self.dest)
        finally:
            Path.open = original_open

        self.assertTrue(self.src.is_file())
        self.assertEqual(self.src.read_bytes(), PAYLOAD)
        self.assertFalse(self.dest.exists())
        self.assertFalse(Path(str(self.dest) + ".part").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
