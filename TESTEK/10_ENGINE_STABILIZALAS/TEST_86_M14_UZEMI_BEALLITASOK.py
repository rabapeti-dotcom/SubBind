"""
M14: üzemi prefs visszatöltés; title_var nem töltődik (M2).
"""
from pathlib import Path
import json
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
from version import APP_VERSION

APP = QApplication.instance() or QApplication(sys.argv)


class TestM14OperationalPrefs(unittest.TestCase):
    def setUp(self):
        self.original_data = os.environ.get("SERIESRENAMER_DATA")
        self.data_dir = Path(tempfile.mkdtemp(prefix="sr_m14_data_"))
        os.environ["SERIESRENAMER_DATA"] = str(self.data_dir)

    def tearDown(self):
        if self.original_data is None:
            os.environ.pop("SERIESRENAMER_DATA", None)
        else:
            os.environ["SERIESRENAMER_DATA"] = self.original_data
        shutil.rmtree(self.data_dir, ignore_errors=True)

    def _write_settings(self, **extra):
        config = {
            "template": "{CIM}.{SZEZON}{EPIZOD}.{NYELV}",
            "title_var": "Acme",
            "mode": "Film",
            "normalize": False,
            "lang_norm": True,
            "include_subdirs": False,
            "check_conflicts": False,
            "preserve_selection": False,
            "sort_mode": "Név",
            "show_welcome": False,
            "language": "hu",
            "output_mode": "Helyben átnevezés",
            "output_dir": "",
            "appearance": "Világos",
            "version": APP_VERSION,
        }
        config.update(extra)
        (self.data_dir / "settings.json").write_text(
            json.dumps(config, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _open(self):
        from main import MainWindow
        win = MainWindow()
        win.show_welcome = False
        APP.processEvents()
        return win

    def test_operational_prefs_restore_without_title(self):
        self._write_settings()
        win = self._open()
        try:
            self.assertEqual(win.mode_combo.currentText(), "Film")
            self.assertEqual(win.template_edit.text(), "{CIM}.{SZEZON}{EPIZOD}.{NYELV}")
            self.assertFalse(win.normalize_cb.isChecked())
            self.assertFalse(win.subdirs_cb.isChecked())
            self.assertFalse(win.conflicts_cb.isChecked())
            self.assertEqual(win.sort_combo.currentText(), "Név")
            self.assertEqual(win.output_mode, "Helyben átnevezés")
            self.assertEqual(win.title_edit.text(), "")
            self.assertFalse(win.title_manual)
            self.assertEqual(win.title_value, "")
            self.assertTrue(win.preserve_cb.isChecked())
        finally:
            win.close()
            win.deleteLater()
            APP.processEvents()

    def test_missing_settings_keeps_defaults(self):
        win = self._open()
        try:
            self.assertEqual(win.mode_combo.currentText(), "Sorozat")
            self.assertEqual(win.template_edit.text(), "{CIM}.{SZEZON}{EPIZOD}")
            self.assertTrue(win.normalize_cb.isChecked())
            self.assertTrue(win.subdirs_cb.isChecked())
            self.assertTrue(win.conflicts_cb.isChecked())
            self.assertEqual(win.sort_combo.currentText(), "Évad → epizód")
            self.assertEqual(win.title_edit.text(), "")
        finally:
            win.close()
            win.deleteLater()
            APP.processEvents()


if __name__ == "__main__":
    unittest.main(verbosity=2)
