"""
M4 GUI: feliratvariáns célnevek, nem támogatott típus, ütközés, M1.1/M2.
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
os.environ["SERIESRENAMER_DATA"] = tempfile.mkdtemp(prefix="sr_gui17_data_")

from PySide6.QtWidgets import QApplication

try:
    from main import MainWindow
except Exception as exc:
    raise RuntimeError(f"MainWindow nem tölthető be: {SRC / 'main.py'}") from exc

APP = QApplication.instance() or QApplication(sys.argv)

VIDEO = b"GUI_TEST_VIDEO_0.6.1"
SUB = b"GUI_TEST_SUB_0.6.1"


def make_case(root, *files):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for rel, data in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return root


class GuiBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_gui_m4_"))
        self.win = MainWindow()
        self.win.show()
        APP.processEvents()

    def tearDown(self):
        self.win.close()
        self.win.deleteLater()
        APP.processEvents()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def add(self, *paths):
        self.win.add_paths([Path(p) for p in paths])
        APP.processEvents()

    def by_name(self, fragment):
        return next(
            i for i in self.win.items
            if fragment.lower() in Path(i.path).name.lower()
        )


class TestM4GuiStabilizalas(GuiBase):
    def test_hu_and_forced_distinct_after_analyze(self):
        src = make_case(
            self.tmp,
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
            ("Show.S01E01.hu.forced.srt", SUB),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(
            src / "Show.S01E01.mkv",
            src / "Show.S01E01.hu.srt",
            src / "Show.S01E01.hu.forced.srt",
        )
        self.win.analyze()
        hu = self.by_name("Show.S01E01.hu.srt")
        forced = self.by_name("forced")
        self.assertEqual(hu.new_name, "Show.S01E01.srt")
        self.assertEqual(forced.new_name, "Show.S01E01.forced.srt")
        self.assertEqual(hu.status, "OK")
        self.assertEqual(forced.status, "OK")

    def test_unsupported_nfo_is_not_ok(self):
        src = make_case(
            self.tmp,
            ("Show.S01E01.mkv", VIDEO),
            ("notes.txt", b"hello"),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(src / "Show.S01E01.mkv", src / "notes.txt")
        self.win.analyze()
        extra = self.by_name("notes.txt")
        self.assertEqual(extra.status, "Nem támogatott")
        self.assertFalse(extra.new_name)

    def test_duplicate_video_targets_marked_before_copy(self):
        src = make_case(
            self.tmp,
            ("Show.S01E01.A.mkv", VIDEO),
            ("Show.S01E01.B.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.win.output_mode = "Helyben átnevezés"
        if hasattr(self.win, "output_mode_combo"):
            self.win.output_mode_combo.setCurrentText("Helyben átnevezés")
        self.win.conflicts_cb.setChecked(True)
        self.add(
            src / "Show.S01E01.A.mkv",
            src / "Show.S01E01.B.mkv",
            src / "Show.S01E01.hu.srt",
        )
        self.win.analyze()
        self.assertEqual(self.by_name("S01E01.A").status, "Névütközés")
        self.assertEqual(self.by_name("S01E01.B").status, "Névütközés")

    def test_m11_and_m2_regressions(self):
        src = make_case(
            self.tmp,
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
            ("Other.Show.S01E01.hu.srt", SUB),
            ("Invasion.S01E01.WEBRip.x264.mkv", VIDEO),
            ("Invasion.S01E01.WEBRip.x264-ION10.hun.srt", SUB),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(
            src / "Show.S01E01.mkv",
            src / "Show.S01E01.hu.srt",
            src / "Other.Show.S01E01.hu.srt",
            src / "Invasion.S01E01.WEBRip.x264.mkv",
            src / "Invasion.S01E01.WEBRip.x264-ION10.hun.srt",
        )
        self.win.analyze()
        self.assertEqual(self.by_name("Show.S01E01.mkv").status, "OK")
        self.assertEqual(self.by_name("Show.S01E01.hu.srt").status, "OK")
        self.assertNotEqual(self.by_name("Other.Show").status, "OK")
        self.assertEqual(
            self.by_name("Invasion.S01E01.WEBRip.x264.mkv").new_name,
            "Invasion.S01E01.mkv",
        )
        self.assertEqual(self.by_name("ION10").new_name, "Invasion.S01E01.srt")


if __name__ == "__main__":
    unittest.main(verbosity=2)
