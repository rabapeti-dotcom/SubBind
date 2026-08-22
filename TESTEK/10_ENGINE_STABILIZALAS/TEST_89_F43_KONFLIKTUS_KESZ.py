"""
F4.3: apply_destination_conflicts + apply_completion_status — analyze-szabály, rename nélkül.
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

from renamer_engine import (
    Item,
    apply_destination_conflicts,
    apply_completion_status,
    destination_matches_output,
)


def make_item(path, new_name, **kwargs):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(kwargs.pop("data", b"SRC_BYTES_F43"))
    defaults = dict(
        path=str(path),
        ext=path.suffix,
        kind="video",
        new_name=new_name,
        status="OK",
        selected=True,
        source_path=str(path),
        copy_status="Várakozik",
        copy_percent=0,
    )
    defaults.update(kwargs)
    return Item(**defaults)


class TestF43ConflictCompletion(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_f43_"))
        self.out = self.tmp / "out"
        self.out.mkdir()
        self.src_dir = self.tmp / "src"
        self.src_dir.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def dest_fn(self, folder=None):
        folder = folder or self.out

        def destination_for(item):
            if not item.new_name:
                return None
            return folder / Path(item.new_name).name

        return destination_for

    def source_fn(self):
        def source_path(item):
            return Path(item.source_path or item.path)

        return source_path

    def apply_conflicts(self, items, folder=None):
        apply_destination_conflicts(items, self.dest_fn(folder), self.source_fn())

    def apply_ready(self, items, folder=None):
        apply_completion_status(items, self.dest_fn(folder), self.source_fn())

    def test_two_inputs_same_target(self):
        a = make_item(self.src_dir / "A.mkv", "Show.S01E01.mkv")
        b = make_item(self.src_dir / "B.mkv", "Show.S01E01.mkv")
        self.apply_conflicts([a, b])
        for item in (a, b):
            self.assertEqual(item.status, "Névütközés")
            self.assertEqual(item.copy_status, "Névütközés")
            self.assertEqual(item.note, "Több fájl ugyanarra a célra kerülne")

    def test_existing_foreign_target(self):
        (self.out / "Show.S01E01.mkv").write_bytes(b"FOREIGN")
        item = make_item(self.src_dir / "Show.S01E01.mkv", "Show.S01E01.mkv")
        self.apply_conflicts([item])
        self.assertEqual(item.status, "Névütközés")
        self.assertEqual(item.note, "A célfájl már létezik – a program nem írta felül")

    def test_source_is_destination_not_conflict(self):
        item = make_item(self.src_dir / "Show.S01E01.mkv", "Show.S01E01.mkv")
        self.apply_conflicts([item], folder=self.src_dir)
        self.assertEqual(item.status, "OK")
        self.assertEqual(item.copy_status, "Várakozik")

    def test_own_copied_output_skipped_then_ready(self):
        dest = self.out / "Show.S01E01.mkv"
        dest.write_bytes(b"SRC_BYTES_F43")
        item = make_item(
            self.src_dir / "Show.S01E01.mkv",
            "Show.S01E01.mkv",
            copy_status="Átmásolva",
            copy_percent=100,
        )
        self.apply_conflicts([item])
        self.assertEqual(item.status, "OK")
        self.assertEqual(item.copy_status, "Átmásolva")
        self.apply_ready([item])
        self.assertEqual(item.status, "Kész")
        self.assertEqual(item.copy_status, "Átmásolva")

    def test_ready_cleared_when_output_gone(self):
        """A Kész státuszt az analyze naming reseteli; a completion csak a copy_status-t törli."""
        item = make_item(
            self.src_dir / "Show.S01E01.mkv",
            "Show.S01E01.mkv",
            status="Kész",
            copy_status="Átmásolva",
            copy_percent=100,
        )
        self.apply_ready([item])
        self.assertEqual(item.copy_status, "Várakozik")
        self.assertEqual(item.copy_percent, 0)
        self.assertEqual(item.status, "Kész")

    def test_unselected_ok_not_marked(self):
        (self.out / "Show.S01E01.mkv").write_bytes(b"FOREIGN")
        item = make_item(
            self.src_dir / "Show.S01E01.mkv",
            "Show.S01E01.mkv",
            selected=False,
        )
        self.apply_conflicts([item])
        self.assertEqual(item.status, "OK")

    def test_m11_mismatch_not_overwritten_by_conflict(self):
        (self.out / "Other.S01E01.srt").write_bytes(b"FOREIGN")
        item = make_item(
            self.src_dir / "Other.S01E01.hu.srt",
            "Other.S01E01.srt",
            kind="sub",
            ext=".srt",
            status="Nem egyező pár",
            note="A videó másik címhez tartozik: Show",
        )
        self.apply_conflicts([item])
        self.assertEqual(item.status, "Nem egyező pár")
        self.assertEqual(item.note, "A videó másik címhez tartozik: Show")

    def test_destination_matches_same_file_true(self):
        item = make_item(self.src_dir / "Show.S01E01.mkv", "Show.S01E01.mkv")
        self.assertTrue(
            destination_matches_output(item, self.dest_fn(self.src_dir), self.source_fn())
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
