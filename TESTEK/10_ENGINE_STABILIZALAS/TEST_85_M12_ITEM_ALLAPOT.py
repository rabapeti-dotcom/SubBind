"""
M12: Item dataclass mezők; source_path nem üres string; parse_item kitölti.
"""
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

from renamer_engine import parse_item, Item
from main import MainWindow

APP = QApplication.instance() or QApplication(sys.argv)

VIDEO = b"M12_TEST_VIDEO_0.6.1"


class TestM12ItemFields(unittest.TestCase):
    def test_parse_item_sets_source_path_not_empty(self):
        item = parse_item("Show.S01E01.mkv")
        self.assertIsNotNone(item.source_path)
        self.assertNotEqual(item.source_path, "")
        self.assertEqual(item.source_path, str(Path("Show.S01E01.mkv")))
        self.assertEqual(item.path, str(Path("Show.S01E01.mkv")))
        self.assertEqual(item.copy_status, "Várakozik")
        self.assertEqual(item.copy_percent, 0)
        self.assertEqual(item.size_bytes, 0)
        self.assertEqual(item.mtime_ns, 0)

    def test_source_path_none_falls_back_to_path(self):
        win = MainWindow()
        win.show_welcome = False
        APP.processEvents()
        try:
            item = parse_item("Show.S01E01.mkv")
            item.source_path = None
            self.assertEqual(win._source_path(item), Path(item.path))
            item.source_path = ""
            self.assertEqual(win._source_path(item), Path(item.path))
        finally:
            win.close()
            win.deleteLater()
            APP.processEvents()

    def test_add_paths_fills_size_and_keeps_source(self):
        tmp = Path(tempfile.mkdtemp(prefix="sr_m12_"))
        win = MainWindow()
        win.show_welcome = False
        APP.processEvents()
        try:
            p = tmp / "Show.S01E01.mkv"
            p.write_bytes(VIDEO)
            win.add_paths([p])
            item = win.items[0]
            self.assertEqual(item.size_bytes, len(VIDEO))
            self.assertTrue(item.mtime_ns)
            self.assertEqual(Path(item.source_path).resolve(), p.resolve())
            item.path = str(tmp / "copied" / "Show.S01E01.mkv")
            self.assertEqual(win._source_path(item).resolve(), p.resolve())
        finally:
            win.close()
            win.deleteLater()
            APP.processEvents()
            shutil.rmtree(tmp, ignore_errors=True)

    def test_item_constructor_defaults(self):
        item = Item("a.mkv", ".mkv", "video")
        self.assertIsNone(item.source_path)
        self.assertEqual(item.copy_status, "Várakozik")
        self.assertEqual(item.size_bytes, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
