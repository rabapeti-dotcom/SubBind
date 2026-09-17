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
        self.assertEqual(self.win.tabs.tabText(1), t("tab.settings"))
        self.assertEqual(self.win.tabs.tabText(1), "Haladó beállítások")
        self.assertEqual(self.win.rename_btn.text(), t("btn.rename"))
        self.win.tabs.setCurrentIndex(1)
        APP.processEvents()
        self.assertTrue(self.win.normalize_cb.isVisible())
        self.assertTrue(self.win.lang_norm_cb.isVisible())
        self.assertTrue(self.win.subdirs_cb.isVisible())
        self.assertTrue(self.win.conflicts_cb.isVisible())
        self.assertTrue(self.win.preserve_cb.isVisible())
        self.assertTrue(self.win.adv_vars_label.isVisible())
        self.assertEqual(self.win.hist_undo_btn.text(), t("hist.undo"))

        self.win.set_language("en")
        APP.processEvents()
        self.assertEqual(self.win.help_btn.text(), "Help ▾")
        self.assertEqual(self.win.tabs.tabText(0), "Files")
        self.assertEqual(self.win.tabs.tabText(1), "Advanced settings")
        self.assertEqual(self.win.tabs.tabText(2), "Preview")
        self.assertEqual(self.win.tabs.tabText(3), "History")
        self.assertEqual(self.win.rename_btn.text(), "Rename")
        self.assertEqual(self.win.check_btn.text(), "Check")
        self.assertEqual(self.win.refresh_preview_btn.text(), "Refresh preview")
        self.win.tabs.setCurrentIndex(1)
        APP.processEvents()
        self.assertTrue(self.win.normalize_cb.isVisible())
        self.assertEqual(self.win.normalize_cb.text(), "Normalize file names")
        self.assertEqual(self.win.output_folder_label.text(), "Output folder:")
        self.assertEqual(self.win.subtitle_pref_label.text(), "Preferred subtitle language:")
        self.assertEqual(self.win.select_missing_btn.text(), "Missing only")
        self.assertEqual(self.win.hist_undo_btn.text(), "Undo selected operation")
        self.assertIn("Previous operations", self.win.history_info.text())
        self.assertNotIn("Súgó", self.win.help_btn.text())
        self.assertNotIn("Haladó mód", self.win.tabs.tabText(1))

        self.win.set_language("hu")
        APP.processEvents()
        self.assertEqual(self.win.help_btn.text(), "Súgó ▾")
        self.assertEqual(self.win.tabs.tabText(1), "Haladó beállítások")
        self.win.tabs.setCurrentIndex(1)
        APP.processEvents()
        self.assertTrue(self.win.normalize_cb.isVisible())
        self.assertEqual(self.win.rename_btn.text(), "Átnevezés")
        self.assertEqual(self.win.naming_heading.text(), "Névadás")
        self.assertEqual(self.win.mode_label.text(), "Mód:")
        self.assertEqual(self.win.normalize_cb.text(), "Fájlnév normalizálása")
        self.assertNotEqual(self.win.normalize_cb.text(), "Normalize file names")

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

    def _settings_tab_snapshot(self):
        self.win.tabs.setCurrentIndex(1)
        APP.processEvents()
        return {
            "tab": self.win.tabs.tabText(1),
            "intro": self.win.settings_intro.text(),
            "heading": self.win.naming_heading.text(),
            "mode": self.win.mode_label.text(),
            "mode_items": tuple(
                self.win.mode_combo.itemText(i)
                for i in range(self.win.mode_combo.count())
            ),
            "name": self.win.name_label.text(),
            "template": self.win.template_label.text(),
            "vars": self.win.base_vars_label.text(),
            "var_cim": self.win.var_buttons["{CIM}"].text(),
            "var_szezon": self.win.var_buttons["{SZEZON}"].text(),
            "var_epizod": self.win.var_buttons["{EPIZOD}"].text(),
            "tpl": self.win.default_template_label.text(),
            "pref": self.win.subtitle_pref_label.text(),
            "pref_items": tuple(
                self.win.subtitle_pref_combo.itemText(i)
                for i in range(self.win.subtitle_pref_combo.count())
            ),
            "normalize": self.win.normalize_cb.text(),
            "lang_norm": self.win.lang_norm_cb.text(),
            "subdirs": self.win.subdirs_cb.text(),
            "conflicts": self.win.conflicts_cb.text(),
            "preserve": self.win.preserve_cb.text(),
            "adv_vars": self.win.adv_vars_label.text(),
            "save": self.win.save_settings_btn.text(),
            "refresh": self.win.refresh_list_btn.text(),
            "reset": self.win.reset_settings_btn.text(),
        }

    def test_07_advanced_settings_tab_visible_language(self):
        """HU/EN a Haladó beállítások fül LÁTHATÓ szövegein, nem csak kulcsokon."""
        en_forbidden = (
            "Naming",
            "Mode:",
            "Series name:",
            "Desired name template:",
            "Basic variables:",
            "Default series template:",
            "Preferred subtitle language:",
            "Normalize file names",
            "Normalize subtitle names",
            "Include subfolders",
            "Check name conflicts in advance",
            "Keep selections",
            "Advanced template variables",
            "subtitle language",
            "season+episode",
            "Title {CIM}",
            "Season {SZEZON}",
            "Episode {EPIZOD}",
            "Save settings",
            "Refresh list",
            "Reset settings",
            "Automatic / Mixed",
        )

        self.win.set_language("en")
        APP.processEvents()
        en = self._settings_tab_snapshot()
        self.assertEqual(en["tab"], "Advanced settings")
        self.assertEqual(en["heading"], "Naming")
        self.assertEqual(en["mode"], "Mode:")
        self.assertEqual(en["mode_items"], ("Automatic / Mixed", "Series", "Movie"))
        self.assertEqual(en["name"], "Series name:")
        self.assertEqual(en["template"], "Desired name template:")
        self.assertEqual(en["vars"], "Basic variables:")
        self.assertEqual(en["var_cim"], "Title {CIM}")
        self.assertEqual(en["var_szezon"], "Season {SZEZON}")
        self.assertEqual(en["var_epizod"], "Episode {EPIZOD}")
        self.assertEqual(en["tpl"], "Default series template: {CIM}.{SZEZON}{EPIZOD}")
        self.assertEqual(en["pref"], "Preferred subtitle language:")
        self.assertEqual(en["pref_items"], ("Hungarian", "German", "English", "Spanish"))
        self.assertEqual(en["normalize"], "Normalize file names")
        self.assertEqual(en["lang_norm"], "Normalize subtitle names")
        self.assertEqual(en["subdirs"], "Include subfolders")
        self.assertEqual(en["conflicts"], "Check name conflicts in advance")
        self.assertEqual(en["preserve"], "Keep selections")
        self.assertEqual(
            en["adv_vars"],
            "Advanced template variables: subtitle language {NYELV}, "
            "extension {KITERJ}, season+episode {EP}, extension {EXT}",
        )
        self.assertEqual(en["save"], "Save settings")
        self.assertEqual(en["refresh"], "Refresh list")
        self.assertEqual(en["reset"], "Reset settings")

        self.win.tabs.setCurrentIndex(0)
        APP.processEvents()
        self.win.set_language("hu")
        APP.processEvents()
        self.assertEqual(self.win.tabs.tabText(1), "Haladó beállítások")
        hu = self._settings_tab_snapshot()
        self.assertEqual(hu["tab"], "Haladó beállítások")
        self.assertEqual(hu["heading"], "Névadás")
        self.assertEqual(hu["mode"], "Mód:")
        self.assertEqual(hu["mode_items"], ("Automatikus / Vegyes", "Sorozat", "Film"))
        self.assertEqual(hu["name"], "Sorozat neve:")
        self.assertEqual(hu["template"], "Kívánt név sablon:")
        self.assertEqual(hu["vars"], "Alap változók:")
        self.assertEqual(hu["var_cim"], "Cím {CIM}")
        self.assertEqual(hu["var_szezon"], "Évad {SZEZON}")
        self.assertEqual(hu["var_epizod"], "Epizód {EPIZOD}")
        self.assertEqual(hu["tpl"], "Alapértelmezett sorozatsablon: {CIM}.{SZEZON}{EPIZOD}")
        self.assertEqual(hu["pref"], "Preferált felirat nyelve:")
        self.assertEqual(hu["pref_items"], ("Magyar", "Német", "Angol", "Spanyol"))
        self.assertEqual(hu["normalize"], "Fájlnév normalizálása")
        self.assertEqual(hu["lang_norm"], "Feliratnevek normalizálása")
        self.assertEqual(hu["subdirs"], "Almappák bevonása")
        self.assertEqual(hu["conflicts"], "Névütközések előzetes ellenőrzése")
        self.assertEqual(hu["preserve"], "Kijelölések megőrzése")
        self.assertEqual(
            hu["adv_vars"],
            "Haladó sablonváltozók: felirat nyelve {NYELV}, "
            "kiterjesztés {KITERJ}, évad+epizód {EP}, kiterjesztés {EXT}",
        )
        self.assertEqual(hu["save"], "Beállítások mentése")
        self.assertEqual(hu["refresh"], "Lista frissítése")
        self.assertEqual(hu["reset"], "Beállítások visszaállítása")
        blob = "\n".join(str(v) for v in hu.values())
        for marker in en_forbidden:
            self.assertNotIn(marker, blob, marker)
        self.assertIn("napi használathoz", hu["intro"])

        self.win.set_language("en")
        APP.processEvents()
        en2 = self._settings_tab_snapshot()
        self.assertEqual(en2["heading"], "Naming")
        self.assertEqual(en2["normalize"], "Normalize file names")
        self.assertEqual(en2["mode_items"], ("Automatic / Mixed", "Series", "Movie"))
        self.assertEqual(en2["var_cim"], "Title {CIM}")
        self.assertEqual(en2["var_szezon"], "Season {SZEZON}")
        self.assertEqual(en2["adv_vars"], en["adv_vars"])

        original = self.win.template_edit.text()
        self.win.template_edit.setText("")
        self.win.var_buttons["{CIM}"].click()
        APP.processEvents()
        self.assertEqual(self.win.template_edit.text(), "{CIM}")
        self.win.var_buttons["{SZEZON}"].click()
        APP.processEvents()
        self.assertEqual(self.win.template_edit.text(), "{CIM}{SZEZON}")
        self.win.template_edit.setText(original)
        APP.processEvents()


def tearDownModule():
    if ORIGINAL_DATA is None:
        os.environ.pop("SERIESRENAMER_DATA", None)
    else:
        os.environ["SERIESRENAMER_DATA"] = ORIGINAL_DATA
    shutil.rmtree(TEST_DATA_ROOT, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
