"""
M8: refresh(reanalyze=False) nem indít analyze-t szűrés/rendezés/check második körén.
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

from PySide6.QtWidgets import QApplication, QMessageBox

from main import MainWindow

APP = QApplication.instance() or QApplication(sys.argv)

VIDEO = b"M8_TEST_VIDEO_0.6.1"
SUB = b"M8_TEST_SUB_0.6.1"


def make_case(root, *files):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for rel, data in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return root


class TestM8RefreshAnalyze(unittest.TestCase):
    def setUp(self):
        self.original_data = os.environ.get("SERIESRENAMER_DATA")
        self.data_dir = Path(tempfile.mkdtemp(prefix="sr_m8_data_"))
        self.out_dir = Path(tempfile.mkdtemp(prefix="sr_m8_out_"))
        os.environ["SERIESRENAMER_DATA"] = str(self.data_dir)
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_m8_"))
        self.message_box_methods = {
            "question": QMessageBox.question,
            "information": QMessageBox.information,
            "warning": QMessageBox.warning,
            "critical": QMessageBox.critical,
        }
        QMessageBox.information = staticmethod(
            lambda *a, **k: QMessageBox.StandardButton.Ok
        )
        self.win = MainWindow()
        self.win.show_welcome = False
        self.win.output_dir = str(self.out_dir)
        self.win.show()
        APP.processEvents()
        self.analyze_calls = 0
        self._orig_analyze = self.win.analyze

        def counted_analyze():
            self.analyze_calls += 1
            return self._orig_analyze()

        self.win.analyze = counted_analyze

    def tearDown(self):
        for name, method in self.message_box_methods.items():
            setattr(QMessageBox, name, method)
        self.win.close()
        self.win.deleteLater()
        APP.processEvents()
        if self.original_data is None:
            os.environ.pop("SERIESRENAMER_DATA", None)
        else:
            os.environ["SERIESRENAMER_DATA"] = self.original_data
        shutil.rmtree(self.tmp, ignore_errors=True)
        shutil.rmtree(self.data_dir, ignore_errors=True)
        shutil.rmtree(self.out_dir, ignore_errors=True)

    def add(self, *paths):
        self.win.add_paths([Path(p) for p in paths])
        APP.processEvents()

    def by_name(self, fragment):
        return next(
            i for i in self.win.items
            if fragment.lower() in Path(i.path).name.lower()
        )

    def test_refresh_false_does_not_call_analyze(self):
        src = make_case(
            self.tmp / "a",
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
        )
        self.add(src / "Show.S01E01.mkv", src / "Show.S01E01.hu.srt")
        self.analyze_calls = 0
        names_before = [i.new_name for i in self.win.items]
        status_before = [i.status for i in self.win.items]
        self.win.refresh(reanalyze=False)
        self.assertEqual(self.analyze_calls, 0)
        self.assertEqual([i.new_name for i in self.win.items], names_before)
        self.assertEqual([i.status for i in self.win.items], status_before)

    def test_refresh_default_calls_analyze(self):
        src = make_case(self.tmp / "b", ("Show.S01E01.mkv", VIDEO))
        self.add(src / "Show.S01E01.mkv")
        self.analyze_calls = 0
        self.win.refresh()
        self.assertGreaterEqual(self.analyze_calls, 1)

    def test_filter_does_not_analyze(self):
        src = make_case(
            self.tmp / "c",
            ("Show.S01E01.mkv", VIDEO),
            ("Other.S01E02.mkv", VIDEO),
        )
        self.add(src / "Show.S01E01.mkv", src / "Other.S01E02.mkv")
        names_before = [i.new_name for i in self.win.items]
        self.analyze_calls = 0
        self.win.filter_edit.setText("Show")
        APP.processEvents()
        self.assertEqual(self.analyze_calls, 0)
        self.assertEqual([i.new_name for i in self.win.items], names_before)
        self.assertEqual(self.win.table.rowCount(), 1)

    def test_sort_does_not_analyze(self):
        src = make_case(
            self.tmp / "d",
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
        )
        self.add(src / "Show.S01E01.mkv", src / "Show.S01E01.hu.srt")
        names_before = [i.new_name for i in self.win.items]
        self.analyze_calls = 0
        self.win.sort_combo.setCurrentText("Név")
        APP.processEvents()
        self.assertEqual(self.analyze_calls, 0)
        self.assertEqual([i.new_name for i in self.win.items], names_before)

    def test_check_analyzes_once(self):
        src = make_case(
            self.tmp / "e",
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
        )
        self.add(src / "Show.S01E01.mkv", src / "Show.S01E01.hu.srt")
        self.analyze_calls = 0
        self.win.check()
        APP.processEvents()
        self.assertEqual(self.analyze_calls, 1)

    def test_add_paths_still_analyzes(self):
        src = make_case(self.tmp / "f", ("Show.S01E01.mkv", VIDEO))
        self.analyze_calls = 0
        self.add(src / "Show.S01E01.mkv")
        self.assertGreaterEqual(self.analyze_calls, 1)
        self.assertTrue(self.win.items[0].new_name)

    def test_m5_selection_survives_filter(self):
        src = make_case(
            self.tmp / "g",
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
        )
        self.add(src / "Show.S01E01.mkv", src / "Show.S01E01.hu.srt")
        video = self.by_name(".mkv")
        video.selected = False
        self.win.refresh(reanalyze=False)
        self.win.filter_edit.setText("Show")
        APP.processEvents()
        self.assertFalse(self.by_name(".mkv").selected)

    def test_m2_regression(self):
        src = make_case(
            self.tmp / "m2",
            ("Invasion.S01E01.WEBRip.x264-ION10.hu.srt", SUB),
            ("Murderbot.S01E01.480p.WEB-DL.mkv", VIDEO),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(
            src / "Invasion.S01E01.WEBRip.x264-ION10.hu.srt",
            src / "Murderbot.S01E01.480p.WEB-DL.mkv",
        )
        self.win.refresh()
        self.assertEqual(self.by_name("Murderbot").new_name, "Murderbot.S01E01.mkv")

    def test_m4_other_unchanged(self):
        src = make_case(self.tmp / "m4", ("notes.txt", b"x"))
        self.add(src / "notes.txt")
        self.win.filter_edit.setText("notes")
        APP.processEvents()
        item = self.win.items[0]
        self.assertEqual(item.kind, "other")
        self.assertFalse(item.selected)
        self.assertEqual(item.status, "Nem támogatott")


if __name__ == "__main__":
    unittest.main(verbosity=2)
