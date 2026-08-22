"""
M10: destination_for — másolás vs helyben, source_path a helybeni mappa.
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

from main import MainWindow

APP = QApplication.instance() or QApplication(sys.argv)

VIDEO = b"M10_TEST_VIDEO_0.6.1"
SUB = b"M10_TEST_SUB_0.6.1"


def make_case(root, *files):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for rel, data in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return root


class TestM10DestinationFor(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_m10_"))
        self.win = MainWindow()
        self.win.show_welcome = False
        APP.processEvents()

    def tearDown(self):
        self.win.close()
        self.win.deleteLater()
        APP.processEvents()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_copy_mode_uses_output_dir(self):
        src = make_case(self.tmp / "src", ("Show.S01E01.mkv", VIDEO))
        out = self.tmp / "out"
        out.mkdir()
        self.win.output_mode = "Másolás kimeneti mappába és átnevezés"
        self.win.output_dir = str(out)
        self.win.add_paths([src / "Show.S01E01.mkv"])
        item = self.win.items[0]
        dest = self.win.destination_for(item)
        self.assertEqual(dest, out.resolve() / item.new_name)
        self.assertEqual(self.win._intended_destination(item), dest)

    def test_inplace_uses_source_parent_not_mutated_path(self):
        src = make_case(self.tmp / "src", ("Show.S01E01.mkv", VIDEO))
        fake_dest_dir = self.tmp / "copied"
        fake_dest_dir.mkdir()
        self.win.output_mode = "Helyben átnevezés"
        self.win.add_paths([src / "Show.S01E01.mkv"])
        item = self.win.items[0]
        expected = Path(item.source_path).parent / item.new_name
        self.assertEqual(self.win.destination_for(item), expected)
        item.path = str(fake_dest_dir / "Show.S01E01.mkv")
        self.assertEqual(
            self.win.destination_for(item),
            expected,
            "helyben a forrásmappa számít, nem a másolás utáni path",
        )

    def test_copy_without_output_dir_is_none(self):
        src = make_case(self.tmp / "src", ("Show.S01E01.mkv", VIDEO))
        self.win.output_mode = "Másolás kimeneti mappába és átnevezés"
        self.win.output_dir = ""
        self.win.add_paths([src / "Show.S01E01.mkv"])
        self.assertIsNone(self.win.destination_for(self.win.items[0]))

    def test_select_missing_uses_helper(self):
        src = make_case(
            self.tmp / "src",
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
        )
        out = self.tmp / "out"
        out.mkdir()
        self.win.output_mode = "Másolás kimeneti mappába és átnevezés"
        self.win.output_dir = str(out)
        self.win.add_paths([src / "Show.S01E01.mkv", src / "Show.S01E01.hu.srt"])
        for i in self.win.items:
            i.selected = False
        self.win.select_missing_items()
        self.assertTrue(all(i.selected for i in self.win.items if i.kind in ("video", "sub")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
