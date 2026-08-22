"""
R1/C: felhasználói verzió 0.6.1, TEST/DEBUG/DEV nincs a főablak címében.
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

from version import APP_NAME, APP_VERSION, APP_VERSION_DEV
from main import MainWindow, RELEASE_ENV

APP = QApplication.instance() or QApplication(sys.argv)


class TestR1CReleaseBranding(unittest.TestCase):
    def setUp(self):
        self.original_release = os.environ.get(RELEASE_ENV)
        self.original_data = os.environ.get("SERIESRENAMER_DATA")
        self.data_dir = Path(tempfile.mkdtemp(prefix="sr_r1c_data_"))
        os.environ["SERIESRENAMER_DATA"] = str(self.data_dir)

    def tearDown(self):
        if self.original_release is None:
            os.environ.pop(RELEASE_ENV, None)
        else:
            os.environ[RELEASE_ENV] = self.original_release
        if self.original_data is None:
            os.environ.pop("SERIESRENAMER_DATA", None)
        else:
            os.environ["SERIESRENAMER_DATA"] = self.original_data
        shutil.rmtree(self.data_dir, ignore_errors=True)

    def test_canonical_version_is_user_release(self):
        self.assertEqual(APP_VERSION, "0.6.1")
        self.assertNotIn("TEST", APP_VERSION)
        self.assertNotIn("DEBUG", APP_VERSION)
        self.assertNotIn("DEV", APP_VERSION)
        self.assertEqual(APP_VERSION_DEV, "0.6.1-TEST")

    def test_main_window_title_has_no_test_channel(self):
        os.environ[RELEASE_ENV] = "1"
        win = MainWindow()
        win.show()
        APP.processEvents()
        try:
            title = win.windowTitle()
            self.assertEqual(title, f"{APP_NAME} v{APP_VERSION}")
            upper = title.upper()
            self.assertNotIn("TEST", upper)
            self.assertNotIn("DEBUG", upper)
            self.assertNotIn("DEV", upper)
        finally:
            win.close()
            win.deleteLater()
            APP.processEvents()


if __name__ == "__main__":
    unittest.main(verbosity=2)
