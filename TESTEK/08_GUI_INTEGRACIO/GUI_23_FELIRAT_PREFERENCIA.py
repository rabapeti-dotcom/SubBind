"""GUI_23: subtitle_pref setting — load/save/reset, combo, UI-tól független.

L2.2: C.1 primary a prefet követi; naming / rename továbbra is HU.
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

from PySide6.QtWidgets import QApplication, QGridLayout

from i18n import combo_id, t
from main import MainWindow, WelcomeDialog, is_ui_primary_sub
from renamer_engine import (
    DEFAULT_SUBTITLE_PREF,
    SUBTITLE_PREF_CHOICES,
    parse_item,
    render_template,
)
from version import APP_VERSION

APP = QApplication.instance() or QApplication(sys.argv)


class TestGui23SubtitlePrefSetting(unittest.TestCase):
    def setUp(self):
        self.original_data = os.environ.get("SERIESRENAMER_DATA")
        self.data_dir = Path(tempfile.mkdtemp(prefix="sr_gui23_data_"))
        os.environ["SERIESRENAMER_DATA"] = str(self.data_dir)
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_gui23_"))
        self.win = None

    def tearDown(self):
        if self.win is not None:
            self.win.close()
            self.win.deleteLater()
            APP.processEvents()
            self.win = None
        if self.original_data is None:
            os.environ.pop("SERIESRENAMER_DATA", None)
        else:
            os.environ["SERIESRENAMER_DATA"] = self.original_data
        shutil.rmtree(self.tmp, ignore_errors=True)
        shutil.rmtree(self.data_dir, ignore_errors=True)

    def _open(self):
        if self.win is not None:
            self.win.close()
            self.win.deleteLater()
            APP.processEvents()
        self.win = MainWindow()
        self.win.show_welcome = False
        self.win.show()
        APP.processEvents()
        return self.win

    def _write_settings(self, **extra):
        config = {
            "template": "{CIM}.{SZEZON}{EPIZOD}",
            "mode": "Sorozat",
            "show_welcome": False,
            "language": "hu",
            "version": APP_VERSION,
        }
        config.update(extra)
        (self.data_dir / "settings.json").write_text(
            json.dumps(config, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _saved_pref(self):
        data = json.loads((self.data_dir / "settings.json").read_text(encoding="utf-8"))
        return data.get("subtitle_pref"), data.get("language")

    def _assert_combo_above_advanced(self, win):
        grid = win.subtitle_pref_combo.parent().layout()
        self.assertIsInstance(grid, QGridLayout)
        pref_row, _, _, _ = grid.getItemPosition(grid.indexOf(win.subtitle_pref_combo))
        adv_row, _, _, _ = grid.getItemPosition(grid.indexOf(win.advanced_box))
        self.assertEqual(pref_row, 5)
        self.assertEqual(adv_row, 6)
        self.assertLess(pref_row, adv_row)

    def test_01_default_install_is_hu(self):
        win = self._open()
        self.assertEqual(DEFAULT_SUBTITLE_PREF, "hu")
        self.assertEqual(win.subtitle_pref, "hu")
        self.assertEqual(combo_id(win.subtitle_pref_combo), "hu")
        self.assertEqual(tuple(SUBTITLE_PREF_CHOICES), ("hu", "de", "en", "es"))
        self.assertEqual(win.subtitle_pref_combo.count(), 4)
        self._assert_combo_above_advanced(win)
        self.assertEqual(win.subtitle_pref_label.text(), t("pref.label"))
        self.assertEqual(win.subtitle_pref_combo.toolTip(), t("pref.tip"))

    def test_02_old_settings_without_key_is_hu(self):
        self._write_settings()
        raw = json.loads((self.data_dir / "settings.json").read_text(encoding="utf-8"))
        self.assertNotIn("subtitle_pref", raw)
        win = self._open()
        self.assertEqual(win.subtitle_pref, "hu")
        self.assertEqual(combo_id(win.subtitle_pref_combo), "hu")

    def test_03_de_saves_and_reloads(self):
        win = self._open()
        win.set_subtitle_pref("de")
        APP.processEvents()
        self.assertEqual(win.subtitle_pref, "de")
        pref, lang = self._saved_pref()
        self.assertEqual(pref, "de")
        self.assertEqual(lang, "hu")
        win = self._open()
        self.assertEqual(win.subtitle_pref, "de")
        self.assertEqual(combo_id(win.subtitle_pref_combo), "de")

    def test_04_en_selection(self):
        win = self._open()
        win.set_subtitle_pref("en")
        self.assertEqual(win.subtitle_pref, "en")
        self.assertEqual(self._saved_pref()[0], "en")
        win = self._open()
        self.assertEqual(win.subtitle_pref, "en")
        self.assertEqual(combo_id(win.subtitle_pref_combo), "en")

    def test_05_es_selection(self):
        win = self._open()
        win.set_subtitle_pref("es")
        self.assertEqual(win.subtitle_pref, "es")
        self.assertEqual(self._saved_pref()[0], "es")
        win = self._open()
        self.assertEqual(win.subtitle_pref, "es")
        self.assertEqual(combo_id(win.subtitle_pref_combo), "es")

    def test_06_invalid_value_falls_back_to_hu(self):
        self._write_settings(subtitle_pref="ru")
        win = self._open()
        self.assertEqual(win.subtitle_pref, "hu")
        self.assertEqual(combo_id(win.subtitle_pref_combo), "hu")
        win.set_subtitle_pref("not-a-lang")
        self.assertEqual(win.subtitle_pref, "hu")
        self.assertEqual(self._saved_pref()[0], "hu")

    def test_07_ui_hu_pref_de(self):
        win = self._open()
        win.set_language("hu")
        win.set_subtitle_pref("de")
        APP.processEvents()
        self.assertEqual(win.language, "hu")
        self.assertEqual(win.subtitle_pref, "de")
        self.assertEqual(win.subtitle_pref_label.text(), "Preferált felirat nyelve:")
        self.assertEqual(win.subtitle_pref_combo.currentText(), "Német")
        pref, lang = self._saved_pref()
        self.assertEqual(pref, "de")
        self.assertEqual(lang, "hu")

    def test_08_ui_en_pref_de(self):
        win = self._open()
        win.set_subtitle_pref("de")
        win.set_language("en")
        APP.processEvents()
        self.assertEqual(win.language, "en")
        self.assertEqual(win.subtitle_pref, "de")
        self.assertEqual(win.subtitle_pref_label.text(), "Preferred subtitle language:")
        self.assertEqual(win.subtitle_pref_combo.currentText(), "German")
        self.assertIn("Independent of the program language", win.subtitle_pref_combo.toolTip())
        pref, lang = self._saved_pref()
        self.assertEqual(pref, "de")
        self.assertEqual(lang, "en")

    def test_09_ui_language_does_not_change_pref(self):
        win = self._open()
        win.set_subtitle_pref("de")
        win.set_language("en")
        APP.processEvents()
        self.assertEqual(win.subtitle_pref, "de")
        win.set_language("hu")
        APP.processEvents()
        self.assertEqual(win.subtitle_pref, "de")
        self.assertEqual(combo_id(win.subtitle_pref_combo), "de")
        pref, lang = self._saved_pref()
        self.assertEqual(pref, "de")
        self.assertEqual(lang, "hu")

    def test_l1_does_not_change_naming(self):
        win = self._open()
        win.set_subtitle_pref("de")
        hu = self.tmp / "Show.S01E01.hu.srt"
        de = self.tmp / "Show.S01E01.de.srt"
        hu.write_bytes(b"sub")
        de.write_bytes(b"sub")
        hu_item = parse_item(hu)
        de_item = parse_item(de)
        self.assertTrue(is_ui_primary_sub(hu_item))
        self.assertFalse(is_ui_primary_sub(de_item))
        self.assertFalse(is_ui_primary_sub(hu_item, win.subtitle_pref))
        self.assertTrue(is_ui_primary_sub(de_item, win.subtitle_pref))
        self.assertEqual(
            render_template("{CIM}.{SZEZON}{EPIZOD}", hu_item, hu_item.title),
            "Show.S01E01.srt",
        )
        self.assertEqual(
            render_template("{CIM}.{SZEZON}{EPIZOD}", de_item, de_item.title),
            "Show.S01E01.de.srt",
        )

    def test_l21_pref_change_refreshes_pair_note(self):
        win = self._open()
        video = self.tmp / "Show.S01E01.mkv"
        hu = self.tmp / "Show.S01E01.hu.srt"
        video.write_bytes(b"vid")
        hu.write_bytes(b"sub")
        win.add_paths([video, hu])
        APP.processEvents()
        mkv = next(i for i in win.items if i.kind == "video")
        hu_item = next(i for i in win.items if i.kind == "sub")
        self.assertEqual(mkv.status, "OK")
        self.assertNotEqual(mkv.note, "Nincs sima HU felirat")
        self.assertTrue(is_ui_primary_sub(hu_item, win.subtitle_pref))
        hu_name = hu_item.new_name
        win.set_subtitle_pref("de")
        APP.processEvents()
        mkv = next(i for i in win.items if i.kind == "video")
        hu_item = next(i for i in win.items if i.kind == "sub")
        self.assertEqual(win.subtitle_pref, "de")
        self.assertEqual(mkv.status, "OK")
        self.assertEqual(mkv.note, "Nincs sima DE felirat")
        self.assertNotEqual(mkv.status, "Nem egyező pár")
        self.assertNotEqual(mkv.status, "Ellenőrzést igényel")
        self.assertFalse(is_ui_primary_sub(hu_item, win.subtitle_pref))
        self.assertEqual(hu_item.new_name, "Show.S01E01.hu.srt")
        self.assertNotEqual(hu_item.new_name, hu_name)

    def test_welcome_dialog_unchanged(self):
        win = self._open()
        dlg = WelcomeDialog(win, language="hu")
        self.assertFalse(hasattr(dlg, "subtitle_pref_combo"))
        self.assertTrue(hasattr(dlg, "hu_btn"))
        self.assertTrue(hasattr(dlg, "en_btn"))
        dlg.close()

    def test_reset_returns_pref_to_hu(self):
        win = self._open()
        win.set_subtitle_pref("es")
        win.reset_settings()
        APP.processEvents()
        self.assertEqual(win.subtitle_pref, "hu")
        self.assertEqual(combo_id(win.subtitle_pref_combo), "hu")


if __name__ == "__main__":
    unittest.main(verbosity=2)
