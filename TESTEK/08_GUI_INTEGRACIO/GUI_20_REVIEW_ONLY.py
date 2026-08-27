"""R3.1: Csak az ellenőrzendők — nézetszűrő, nem kijelölés."""
from pathlib import Path
import os
import sys
import shutil
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from main import MainWindow

APP = QApplication.instance() or QApplication(sys.argv)

VIDEO = b"GUI20_VIDEO_0.6.1"
SUB = b"GUI20_SUB_0.6.1"


def make_case(root, *files):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for rel, data in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return root


class TestShowReviewOnly(unittest.TestCase):
    def setUp(self):
        self.original_data = os.environ.get("SERIESRENAMER_DATA")
        self.data_dir = Path(tempfile.mkdtemp(prefix="sr_gui20_data_"))
        os.environ["SERIESRENAMER_DATA"] = str(self.data_dir)
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_gui20_"))
        self.win = MainWindow()
        self.win.show_welcome = False
        self.win.show()
        APP.processEvents()

    def tearDown(self):
        self.win.close()
        self.win.deleteLater()
        APP.processEvents()
        if self.original_data is None:
            os.environ.pop("SERIESRENAMER_DATA", None)
        else:
            os.environ["SERIESRENAMER_DATA"] = self.original_data
        shutil.rmtree(self.tmp, ignore_errors=True)
        shutil.rmtree(self.data_dir, ignore_errors=True)

    def test_review_only_hides_ok_rows_without_touching_selection(self):
        src = make_case(
            self.tmp,
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
            ("Show.S01E02.mkv", VIDEO),
            ("Other.S01E02.hu.srt", SUB),
            ("Show.S01E03.mkv", VIDEO),
        )
        self.win.add_paths(list(src.iterdir()))
        APP.processEvents()

        self.assertEqual(len(self.win.items), 5)
        self.assertEqual(self.win.table.rowCount(), 5)
        before_selected = [i.selected for i in self.win.items]
        before_status = [i.status for i in self.win.items]
        review_count = sum(
            1 for i in self.win.items if self.win._review_kind(i) != "ok"
        )
        self.assertGreaterEqual(review_count, 3)

        self.win.show_review_only_btn.setChecked(True)
        APP.processEvents()

        visible = self.win._visible_items()
        self.assertEqual(len(visible), review_count)
        self.assertEqual(self.win.table.rowCount(), review_count)
        self.assertTrue(all(self.win._review_kind(i) != "ok" for i in visible))
        self.assertEqual([i.selected for i in self.win.items], before_selected)
        self.assertEqual([i.status for i in self.win.items], before_status)
        self.assertEqual(len(self.win.items), 5)

        self.win.show_review_only_btn.setChecked(False)
        APP.processEvents()
        self.assertEqual(self.win.table.rowCount(), 5)
        self.assertEqual([i.selected for i in self.win.items], before_selected)

    def test_select_review_still_only_toggles_checkboxes(self):
        src = make_case(
            self.tmp,
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
            ("Show.S01E02.mkv", VIDEO),
        )
        self.win.add_paths(list(src.iterdir()))
        APP.processEvents()
        self.win.set_all(False)
        self.win.select_review_items()
        APP.processEvents()
        self.assertEqual(self.win.table.rowCount(), 3)
        for item in self.win.items:
            needs = self.win._review_kind(item) != "ok" and item.kind in ("video", "sub")
            self.assertEqual(item.selected, needs)


if __name__ == "__main__":
    unittest.main(verbosity=2)
