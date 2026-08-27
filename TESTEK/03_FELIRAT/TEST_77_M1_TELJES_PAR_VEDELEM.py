"""
M1.1: teljes group (videó + felirat) státuszát idegen, azonos SxxEyy
hiányos group nem minősítheti át.
"""
from pathlib import Path
import os
import sys
import shutil
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from main import MainWindow

APP = QApplication.instance() or QApplication(sys.argv)

VIDEO = b"M11_TEST_VIDEO_0.6.1"
SUB = b"M11_TEST_SUB_0.6.1"


def make_case(root, *files):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for rel, data in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return root


class TestM1TeljesParVedlem(unittest.TestCase):
    def setUp(self):
        self.original_data = os.environ.get("SERIESRENAMER_DATA")
        self.data_dir = Path(tempfile.mkdtemp(prefix="sr_m11_data_"))
        self.out = Path(tempfile.mkdtemp(prefix="sr_m11_out_"))
        os.environ["SERIESRENAMER_DATA"] = str(self.data_dir)
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_m11_"))
        self.win = MainWindow()
        self.win.show_welcome = False
        self.win.output_dir = str(self.out)
        if hasattr(self.win, "output_edit"):
            self.win.output_edit.setText(str(self.out))
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

    def test_a_complete_pair_not_marked_by_foreign_same_episode(self):
        src = make_case(
            self.tmp,
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
            ("Other.Show.S01E01.hu.srt", SUB),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(
            src / "Show.S01E01.mkv",
            src / "Show.S01E01.hu.srt",
            src / "Other.Show.S01E01.hu.srt",
        )
        self.win.analyze()
        video = self.by_name("Show.S01E01.mkv")
        good = self.by_name("Show.S01E01.hu.srt")
        other = self.by_name("Other.Show")
        self.assertEqual(video.status, "OK")
        self.assertEqual(good.status, "OK")
        self.assertNotEqual(video.status, "Nem egyező pár")
        self.assertNotEqual(good.status, "Nem egyező pár")
        self.assertNotEqual(other.status, "OK")
        self.assertIn(other.status, ("Videó nélkül", "Nem egyező pár"))

    def test_b_classic_m1_mismatch_unchanged(self):
        src = make_case(
            self.tmp,
            ("Show.S01E01.mkv", VIDEO),
            ("Other.Show.S01E01.hu.srt", SUB),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(
            src / "Show.S01E01.mkv",
            src / "Other.Show.S01E01.hu.srt",
        )
        self.win.analyze()
        video = self.by_name("Show.S01E01.mkv")
        other = self.by_name("Other.Show")
        self.assertEqual(video.status, "Nem egyező pár")
        self.assertEqual(other.status, "Nem egyező pár")

    def test_c_m2_two_complete_series_keep_own_titles(self):
        src = make_case(
            self.tmp,
            ("Invasion.S01E01.WEBRip.x264.mkv", VIDEO),
            ("Invasion.S01E01.WEBRip.x264-ION10.hun.srt", SUB),
            ("Murderbot.S01E01.480p.ATVP.WEB-DL.AAC2.0.H264-B9R.mkv", VIDEO),
            ("Murderbot.S01E01.FreeCommerce.ATVP.WEB-DL.hu.srt", SUB),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(
            src / "Invasion.S01E01.WEBRip.x264.mkv",
            src / "Invasion.S01E01.WEBRip.x264-ION10.hun.srt",
            src / "Murderbot.S01E01.480p.ATVP.WEB-DL.AAC2.0.H264-B9R.mkv",
            src / "Murderbot.S01E01.FreeCommerce.ATVP.WEB-DL.hu.srt",
        )
        self.win.analyze()
        inv_v = self.by_name("Invasion.S01E01.WEBRip.x264.mkv")
        inv_s = self.by_name("ION10")
        mur_v = self.by_name("Murderbot.S01E01.480p")
        mur_s = self.by_name("FreeCommerce")
        self.assertEqual(inv_v.new_name, "Invasion.S01E01.mkv")
        self.assertEqual(inv_s.new_name, "Invasion.S01E01.srt")
        self.assertEqual(mur_v.new_name, "Murderbot.S01E01.mkv")
        self.assertEqual(mur_s.new_name, "Murderbot.S01E01.srt")
        self.assertEqual(inv_v.status, "OK")
        self.assertEqual(inv_s.status, "OK")
        self.assertEqual(mur_v.status, "OK")
        self.assertEqual(mur_s.status, "OK")


if __name__ == "__main__":
    unittest.main(verbosity=2)
