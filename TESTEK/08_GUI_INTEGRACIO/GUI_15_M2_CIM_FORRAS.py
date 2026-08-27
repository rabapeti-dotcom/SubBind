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
        self.original_data = os.environ.get("SERIESRENAMER_DATA")
        self.data_dir = Path(tempfile.mkdtemp(prefix="sr_gui_m2_data_"))
        self.out = Path(tempfile.mkdtemp(prefix="sr_gui_m2_out_"))
        os.environ["SERIESRENAMER_DATA"] = str(self.data_dir)
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_gui_m2_"))
        self.win = MainWindow()
        self.win.show_welcome = False
        self.win.output_dir = str(self.out)
        if hasattr(self.win, "output_edit"):
            self.win.output_edit.setText(str(self.out))
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
        shutil.rmtree(self.out, ignore_errors=True)

    def add(self, *paths):
        self.win.add_paths([Path(p) for p in paths])
        APP.processEvents()

    def by_name(self, fragment):
        return next(
            i for i in self.win.items
            if fragment.lower() in Path(i.path).name.lower()
        )


class TestM2CimForras(GuiBase):
    def test_m2_1_idegen_s01e01_does_not_steal_title(self):
        src = make_case(
            self.tmp,
            ("Invasion.S01E01.WEBRip.x264-ION10.hu.srt", SUB),
            ("Murderbot.S01E01.480p.WEB-DL.mkv", VIDEO),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(
            src / "Invasion.S01E01.WEBRip.x264-ION10.hu.srt",
            src / "Murderbot.S01E01.480p.WEB-DL.mkv",
        )
        self.win.analyze()
        video = self.by_name("Murderbot")
        sub = self.by_name("Invasion")
        self.assertEqual(video.title, "Murderbot")
        self.assertEqual(sub.title, "Invasion")
        self.assertEqual(video.new_name, "Murderbot.S01E01.mkv")
        self.assertNotEqual(video.new_name, "Invasion.ION10.hu.S01E01.mkv")
        self.assertNotIn("ION10", video.new_name)
        self.assertEqual(video.status, "Nem egyező pár")
        self.assertEqual(sub.status, "Nem egyező pár")

    def test_m2_2_single_series_keeps_parsed_title(self):
        src = make_case(
            self.tmp,
            ("Show.Name.S02E04.1080p.WEB-DL.mkv", VIDEO),
            ("Show.Name.S02E04.hu.srt", SUB),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(
            src / "Show.Name.S02E04.1080p.WEB-DL.mkv",
            src / "Show.Name.S02E04.hu.srt",
        )
        self.win.analyze()
        video = self.by_name(".mkv")
        sub = self.by_name(".srt")
        self.assertEqual(video.new_name, "Show.Name.S02E04.mkv")
        self.assertEqual(sub.new_name, "Show.Name.S02E04.srt")
        self.assertNotIn("WEB-DL", video.new_name)
        self.assertNotIn("WEB-DL", sub.new_name)
        self.assertEqual(video.status, "OK")
        self.assertEqual(sub.status, "OK")

    def test_m2_3_manual_shared_title_acme(self):
        src = make_case(
            self.tmp,
            ("Invasion.S01E01.WEBRip.x264-ION10.hu.srt", SUB),
            ("Murderbot.S01E01.480p.WEB-DL.mkv", VIDEO),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(
            src / "Invasion.S01E01.WEBRip.x264-ION10.hu.srt",
            src / "Murderbot.S01E01.480p.WEB-DL.mkv",
        )
        self.win.title_edit.setText("Acme")
        APP.processEvents()
        self.assertTrue(self.win.title_manual)
        self.win.analyze()
        video = self.by_name("Murderbot")
        sub = self.by_name("Invasion")
        self.assertEqual(video.new_name, "Acme.S01E01.mkv")
        self.assertEqual(sub.new_name, "Acme.S01E01.srt")

    def test_m2_4_mixed_mode_keeps_own_titles(self):
        src = make_case(
            self.tmp,
            ("Invasion.S01E01.WEBRip.x264-ION10.hu.srt", SUB),
            ("Murderbot.S01E01.480p.WEB-DL.mkv", VIDEO),
        )
        self.win.mode_combo.setCurrentText("Automatikus / Vegyes")
        self.add(
            src / "Invasion.S01E01.WEBRip.x264-ION10.hu.srt",
            src / "Murderbot.S01E01.480p.WEB-DL.mkv",
        )
        self.win.analyze()
        video = self.by_name("Murderbot")
        sub = self.by_name("Invasion")
        self.assertEqual(video.new_name, "Murderbot.S01E01.mkv")
        self.assertEqual(sub.new_name, "Invasion.S01E01.srt")
        self.assertNotEqual(video.new_name, "Invasion.ION10.hu.S01E01.mkv")

    def test_m2_5_repeated_analyze_is_stable(self):
        src = make_case(
            self.tmp,
            ("Invasion.S01E01.WEBRip.x264-ION10.hu.srt", SUB),
            ("Murderbot.S01E01.480p.WEB-DL.mkv", VIDEO),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(
            src / "Invasion.S01E01.WEBRip.x264-ION10.hu.srt",
            src / "Murderbot.S01E01.480p.WEB-DL.mkv",
        )
        self.win.analyze()
        first = self.by_name("Murderbot").new_name
        self.win.analyze()
        self.win.refresh()
        APP.processEvents()
        self.assertEqual(first, "Murderbot.S01E01.mkv")
        self.assertEqual(self.by_name("Murderbot").new_name, first)


if __name__ == "__main__":
    unittest.main(verbosity=2)
