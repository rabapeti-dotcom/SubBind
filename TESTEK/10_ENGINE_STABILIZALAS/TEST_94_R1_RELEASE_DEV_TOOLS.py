"""
R1/B: Tesztlabor / Patch a felhasználói (release) buildben nincs a főablakban.
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

from main import MainWindow, dev_tools_enabled, RELEASE_ENV

APP = QApplication.instance() or QApplication(sys.argv)


class TestR1BDevToolsGating(unittest.TestCase):
    def setUp(self):
        self.original_release = os.environ.get(RELEASE_ENV)
        self.data = Path(tempfile.mkdtemp(prefix="sr_r1b_"))
        self.original_data = os.environ.get("SERIESRENAMER_DATA")
        os.environ["SERIESRENAMER_DATA"] = str(self.data)

    def tearDown(self):
        if self.original_release is None:
            os.environ.pop(RELEASE_ENV, None)
        else:
            os.environ[RELEASE_ENV] = self.original_release
        if self.original_data is None:
            os.environ.pop("SERIESRENAMER_DATA", None)
        else:
            os.environ["SERIESRENAMER_DATA"] = self.original_data
        shutil.rmtree(self.data, ignore_errors=True)

    def test_dev_mode_shows_tool_buttons(self):
        os.environ.pop(RELEASE_ENV, None)
        self.assertTrue(dev_tools_enabled())
        win = MainWindow()
        win.show()
        APP.processEvents()
        try:
            self.assertTrue(hasattr(win, "test_lab_btn"))
            self.assertTrue(hasattr(win, "patch_btn"))
            self.assertFalse(win.test_lab_btn.isHidden())
            self.assertFalse(win.patch_btn.isHidden())
        finally:
            win.close()
            win.deleteLater()
            APP.processEvents()

    def test_release_flag_hides_tools_and_noop_open(self):
        os.environ[RELEASE_ENV] = "1"
        self.assertFalse(dev_tools_enabled())
        win = MainWindow()
        try:
            self.assertFalse(hasattr(win, "test_lab_btn"))
            self.assertFalse(hasattr(win, "patch_btn"))
            win.open_test_lab()
            win.open_patch_center()
            self.assertFalse(hasattr(win, "_test_lab_dialog"))
        finally:
            win.close()
            win.deleteLater()
            APP.processEvents()


if __name__ == "__main__":
    unittest.main(verbosity=2)
