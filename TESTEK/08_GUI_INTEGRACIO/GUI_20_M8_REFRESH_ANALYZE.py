"""
M8 GUI: szűrés/rendezés nem analyze; Előnézet frissítése igen.
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

from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

from main import MainWindow

APP = QApplication.instance() or QApplication(sys.argv)

VIDEO = b"M8_GUI_VIDEO_0.6.1"
SUB = b"M8_GUI_SUB_0.6.1"


def make_case(root, *files):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for rel, data in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return root


class TestGuiM8Refresh(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_m8_gui_"))
        self._info = QMessageBox.information
        QMessageBox.information = staticmethod(
            lambda *a, **k: QMessageBox.StandardButton.Ok
        )
        self.win = MainWindow()
        self.win.show_welcome = False
        self.win.show()
        APP.processEvents()
        self.analyze_calls = 0
        orig = self.win.analyze

        def counted():
            self.analyze_calls += 1
            return orig()

        self.win.analyze = counted

    def tearDown(self):
        QMessageBox.information = self._info
        self.win.close()
        self.win.deleteLater()
        APP.processEvents()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def add(self, *paths):
        self.win.add_paths([Path(p) for p in paths])
        APP.processEvents()

    def test_filter_and_sort_redraw_only(self):
        src = make_case(
            self.tmp,
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
        )
        self.add(src / "Show.S01E01.mkv", src / "Show.S01E01.hu.srt")
        self.assertEqual(self.win.table.rowCount(), 2)
        before = [i.new_name for i in self.win.items]
        self.analyze_calls = 0
        self.win.filter_edit.setText("srt")
        APP.processEvents()
        self.assertEqual(self.analyze_calls, 0)
        self.assertEqual(self.win.table.rowCount(), 1)
        self.win.filter_edit.setText("")
        APP.processEvents()
        self.win.sort_combo.setCurrentText("Fájltípus")
        APP.processEvents()
        self.assertEqual(self.analyze_calls, 0)
        self.assertEqual([i.new_name for i in self.win.items], before)

    def test_preview_refresh_button_analyzes(self):
        src = make_case(
            self.tmp / "p",
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
        )
        self.add(src / "Show.S01E01.mkv", src / "Show.S01E01.hu.srt")
        btn = None
        for child in self.win.findChildren(QPushButton):
            if child.text() == "Előnézet frissítése":
                btn = child
                break
        self.assertIsNotNone(btn)
        self.analyze_calls = 0
        btn.click()
        APP.processEvents()
        self.assertGreaterEqual(self.analyze_calls, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
