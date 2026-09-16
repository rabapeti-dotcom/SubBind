"""GUI_27: HU/EN localization — key parity, live switch, Help language."""
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
ORIGINAL_DATA = os.environ.get("SERIESRENAMER_DATA")
TEST_DATA_ROOT = Path(tempfile.mkdtemp(prefix="sr_gui27_data_"))
os.environ["SERIESRENAMER_DATA"] = str(TEST_DATA_ROOT)

from PySide6.QtWidgets import QApplication, QDialog, QTextEdit, QPushButton

from i18n import STRINGS, note_text, set_active_language, t
from main import MainWindow
from version import APP_NAME, APP_VERSION

APP = QApplication.instance() or QApplication(sys.argv)

HU_HELP_MARKERS = (
    "Súgó",
    "ELSŐ LÉPÉSEK",
    "SOROZAT MÓD",
    "FILM MÓD",
    "FONTOS",
    "Verzió:",
)
EN_HELP_MARKERS = (
    "Help",
    "FIRST STEPS",
    "SERIES MODE",
    "MOVIE MODE",
    "IMPORTANT",
    "Version:",
)


class TestGui27I18nLocalization(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_gui27_"))
        self.win = MainWindow()
        self.win.show_welcome = False
        self.win.show()
        APP.processEvents()

    def tearDown(self):
        self.win.close()
        self.win.deleteLater()
        APP.processEvents()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _capture_help(self):
        captured = {}
        original = QDialog.exec

        def fake_exec(self):
            captured["title"] = self.windowTitle()
            text = self.findChild(QTextEdit)
            captured["body"] = text.toPlainText() if text else ""
            buttons = [b.text() for b in self.findChildren(QPushButton)]
            captured["buttons"] = buttons
            return QDialog.DialogCode.Rejected

        QDialog.exec = fake_exec
        try:
            self.win.show_help()
        finally:
            QDialog.exec = original
        return captured

    def test_01_hu_en_key_parity(self):
        hu_keys = set(STRINGS["hu"])
        en_keys = set(STRINGS["en"])
        self.assertEqual(hu_keys - en_keys, set())
        self.assertEqual(en_keys - hu_keys, set())

    def test_02_help_follows_language_without_restart(self):
        self.win.set_language("hu")
        APP.processEvents()
        hu = self._capture_help()
        self.assertIn("Súgó", hu["title"])
        for marker in HU_HELP_MARKERS:
            self.assertIn(marker, hu["body"], marker)
        self.assertIn("Bezárás", hu["buttons"])

        self.win.set_language("en")
        APP.processEvents()
        en = self._capture_help()
        self.assertTrue(en["title"].startswith("Help"))
        self.assertNotIn("Súgó", en["title"])
        for marker in EN_HELP_MARKERS:
            self.assertIn(marker, en["body"], marker)
        for marker in HU_HELP_MARKERS:
            self.assertNotIn(marker, en["body"], marker)
        self.assertIn("Close", en["buttons"])
        self.assertNotIn("Bezárás", en["buttons"])

        self.win.set_language("hu")
        APP.processEvents()
        hu2 = self._capture_help()
        self.assertIn("Súgó", hu2["title"])
        self.assertIn("ELSŐ LÉPÉSEK", hu2["body"])

    def test_03_live_switch_updates_visible_chrome(self):
        self.win.set_language("hu")
        APP.processEvents()
        self.assertEqual(self.win.help_btn.text(), t("btn.help"))
        self.assertEqual(self.win.tabs.tabText(0), t("tab.files"))
        self.assertEqual(self.win.rename_btn.text(), t("btn.rename"))
        self.assertEqual(self.win.advanced_box.title(), t("adv.mode"))
        self.assertEqual(self.win.hist_undo_btn.text(), t("hist.undo"))

        self.win.set_language("en")
        APP.processEvents()
        self.assertEqual(self.win.help_btn.text(), "Help ▾")
        self.assertEqual(self.win.tabs.tabText(0), "Files")
        self.assertEqual(self.win.tabs.tabText(1), "Template and settings")
        self.assertEqual(self.win.tabs.tabText(2), "Preview")
        self.assertEqual(self.win.tabs.tabText(3), "History")
        self.assertEqual(self.win.rename_btn.text(), "Rename")
        self.assertEqual(self.win.check_btn.text(), "Check")
        self.assertEqual(self.win.refresh_preview_btn.text(), "Refresh preview")
        self.assertEqual(self.win.advanced_box.title(), "Advanced mode")
        self.assertEqual(self.win.output_folder_label.text(), "Output folder:")
        self.assertEqual(self.win.subtitle_pref_label.text(), "Preferred subtitle language:")
        self.assertEqual(self.win.select_missing_btn.text(), "Missing only")
        self.assertEqual(self.win.hist_undo_btn.text(), "Undo selected operation")
        self.assertIn("Previous operations", self.win.history_info.text())
        self.assertNotIn("Súgó", self.win.help_btn.text())
        self.assertNotIn("Haladó", self.win.advanced_box.title())

        self.win.set_language("hu")
        APP.processEvents()
        self.assertEqual(self.win.help_btn.text(), "Súgó ▾")
        self.assertEqual(self.win.advanced_box.title(), "Haladó mód")
        self.assertEqual(self.win.rename_btn.text(), "Átnevezés")

    def test_04_help_keys_match_app_version(self):
        set_active_language("en")
        body = t("help.body", name=APP_NAME, version=APP_VERSION)
        self.assertIn(APP_VERSION, body)
        self.assertIn(APP_NAME, body)
        self.assertIn("FIRST STEPS", body)
        set_active_language("hu")
        body_hu = t("help.body", name=APP_NAME, version=APP_VERSION)
        self.assertIn("ELSŐ LÉPÉSEK", body_hu)

    def test_05_engine_notes_display_in_active_language(self):
        set_active_language("en")
        self.assertEqual(
            note_text("Több fájl ugyanarra a célra kerülne"),
            "Several files would go to the same destination",
        )
        self.assertEqual(
            note_text("Nincs sima HU felirat"),
            "No plain HU subtitle",
        )
        set_active_language("hu")
        self.assertEqual(
            note_text("Több fájl ugyanarra a célra kerülne"),
            "Több fájl ugyanarra a célra kerülne",
        )

    def test_06_p1_rename_output_gate_untouched(self):
        self.win.output_mode = "Másolás kimeneti mappába és átnevezés"
        self.win.output_dir = ""
        self.assertFalse(self.win._rename_output_ok())
        self.win.output_mode = "Helyben átnevezés"
        self.assertTrue(self.win._rename_output_ok())


def tearDownModule():
    if ORIGINAL_DATA is None:
        os.environ.pop("SERIESRENAMER_DATA", None)
    else:
        os.environ["SERIESRENAMER_DATA"] = ORIGINAL_DATA
    shutil.rmtree(TEST_DATA_ROOT, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
