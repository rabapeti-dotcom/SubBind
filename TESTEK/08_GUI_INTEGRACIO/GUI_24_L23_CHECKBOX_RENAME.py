"""GUI_24: L2.3 checkbox + rename kapu — automatikus partner a subtitle_pref szerint.

Nincs fallback. C.1 / pairing érintetlen. L2.4: kimeneti nevek a B stratégia szerint.
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

from PySide6.QtWidgets import QApplication, QCheckBox, QMessageBox

from main import COL_ORIG, COL_TYPE, MainWindow, is_ui_primary_sub

APP = QApplication.instance() or QApplication(sys.argv)

VIDEO = b"GUI24_VIDEO"
SUB = b"GUI24_SUB"


def make_case(root, *names):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in names:
        p = root / name
        p.write_bytes(VIDEO if p.suffix.lower() == ".mkv" else SUB)
        paths.append(p)
    return paths


class TestGui24CheckboxRenameGate(unittest.TestCase):
    def setUp(self):
        self.original_data = os.environ.get("SERIESRENAMER_DATA")
        self.data_dir = Path(tempfile.mkdtemp(prefix="sr_gui24_data_"))
        os.environ["SERIESRENAMER_DATA"] = str(self.data_dir)
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_gui24_"))
        self.out = Path(tempfile.mkdtemp(prefix="sr_gui24_out_"))
        self.message_box_methods = {
            "question": QMessageBox.question,
            "information": QMessageBox.information,
            "warning": QMessageBox.warning,
            "critical": QMessageBox.critical,
        }
        self.win = MainWindow()
        self.win.show_welcome = False
        self.win.show()
        APP.processEvents()

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
        shutil.rmtree(self.out, ignore_errors=True)

    def _load(self, *names):
        paths = make_case(self.tmp, *names)
        self.win.add_paths(paths)
        self.win.analyze()
        APP.processEvents()
        return {Path(i.path).name: i for i in self.win.items}

    def by_name(self, fragment):
        return next(
            i for i in self.win.items
            if fragment.lower() in Path(i.path).name.lower()
        )

    def checkbox_for(self, fragment):
        item = self.by_name(fragment)
        visible = self.win._visible_items()
        row = visible.index(item)
        holder = self.win.table.cellWidget(row, 0)
        return holder.findChild(QCheckBox), item

    def check_video(self):
        self.win.select_none_items()
        APP.processEvents()
        check, item = self.checkbox_for(".mkv")
        check.setChecked(True)
        APP.processEvents()
        return item

    def check_file(self, fragment):
        check, item = self.checkbox_for(fragment)
        check.setChecked(True)
        APP.processEvents()
        return item

    def selected_names(self):
        return {
            Path(i.path).name for i in self.win.items if i.selected
        }

    def set_copy_mode(self):
        self.win.output_mode = "Másolás kimeneti mappába és átnevezés"
        self.win.output_dir = str(self.out)
        self.win.output_mode_combo.setCurrentText(
            "Másolás kimeneti mappába és átnevezés"
        )
        self.win.output_edit.setText(str(self.out))
        APP.processEvents()

    def confirm_dialogs(self):
        QMessageBox.question = staticmethod(
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes
        )
        QMessageBox.information = staticmethod(
            lambda *args, **kwargs: QMessageBox.StandardButton.Ok
        )
        QMessageBox.warning = staticmethod(
            lambda *args, **kwargs: QMessageBox.StandardButton.Ok
        )
        QMessageBox.critical = staticmethod(
            lambda *args, **kwargs: QMessageBox.StandardButton.Ok
        )
        self.win._confirm_rename = lambda *args, **kwargs: True

    def out_names(self):
        return {p.name for p in self.out.iterdir() if p.is_file()}

    def _type_text(self, filename):
        for row in range(self.win.table.rowCount()):
            cell = self.win.table.item(row, COL_ORIG)
            if cell and cell.text() == filename:
                return self.win.table.item(row, COL_TYPE).text()
        self.fail(f"Nincs sor: {filename}")

    def test_01_pref_de_one_de_auto_selects(self):
        self._load("Show.S01E01.mkv", "Show.S01E01.de.srt")
        self.win.set_subtitle_pref("de")
        APP.processEvents()
        self.check_video()
        self.assertEqual(
            self.selected_names(),
            {"Show.S01E01.mkv", "Show.S01E01.de.srt"},
        )
        self.assertTrue(is_ui_primary_sub(self.by_name(".de.srt"), "de"))

    def test_02_pref_de_de_plus_hu_only_de_auto(self):
        self._load(
            "Show.S01E01.mkv",
            "Show.S01E01.de.srt",
            "Show.S01E01.hu.srt",
        )
        self.win.set_subtitle_pref("de")
        APP.processEvents()
        self.check_video()
        self.assertTrue(self.by_name(".mkv").selected)
        self.assertTrue(self.by_name(".de.srt").selected)
        self.assertFalse(self.by_name(".hu.srt").selected)

    def test_03_pref_de_only_hu_no_auto_sub(self):
        self._load("Show.S01E01.mkv", "Show.S01E01.hu.srt")
        self.win.set_subtitle_pref("de")
        APP.processEvents()
        self.check_video()
        self.assertTrue(self.by_name(".mkv").selected)
        self.assertFalse(self.by_name(".hu.srt").selected)

    def test_04_pref_de_hu_en_no_auto_sub(self):
        self._load(
            "Show.S01E01.mkv",
            "Show.S01E01.hu.srt",
            "Show.S01E01.en.srt",
        )
        self.win.set_subtitle_pref("de")
        APP.processEvents()
        self.check_video()
        self.assertEqual(self.selected_names(), {"Show.S01E01.mkv"})
        self.assertFalse(self.by_name(".hu.srt").selected)
        self.assertFalse(self.by_name(".en.srt").selected)

    def test_05_pref_de_two_plain_de_no_auto_sub(self):
        self._load(
            "Show.S01E01.mkv",
            "Show.S01E01.de.srt",
            "Show.S01E01.ger.srt",
        )
        self.win.set_subtitle_pref("de")
        APP.processEvents()
        self.check_video()
        self.assertTrue(self.by_name(".mkv").selected)
        self.assertFalse(self.by_name("Show.S01E01.de.srt").selected)
        self.assertFalse(self.by_name("Show.S01E01.ger.srt").selected)
        self.assertEqual(self.by_name(".mkv").status, "Ellenőrzést igényel")

    def test_06_pref_de_one_de_rename_allowed(self):
        self._load("Show.S01E01.mkv", "Show.S01E01.de.srt")
        self.win.set_subtitle_pref("de")
        self.set_copy_mode()
        self.confirm_dialogs()
        self.check_video()
        self.win.rename()
        APP.processEvents()
        self.assertEqual(self.out_names(), {"Show.S01E01.mkv", "Show.S01E01.srt"})

    def test_07_pref_de_only_hu_no_fallback_partner(self):
        self._load("Show.S01E01.mkv", "Show.S01E01.hu.srt")
        self.win.set_subtitle_pref("de")
        self.set_copy_mode()
        self.confirm_dialogs()
        self.check_video()
        self.assertFalse(self.by_name(".hu.srt").selected)
        self.win.rename()
        APP.processEvents()
        self.assertEqual(self.out_names(), {"Show.S01E01.mkv"})
        self.assertFalse((self.out / "Show.S01E01.srt").exists())

    def test_08_pref_de_forced_is_not_partner(self):
        self._load("Show.S01E01.mkv", "Show.S01E01.de.forced.srt")
        self.win.set_subtitle_pref("de")
        self.set_copy_mode()
        self.confirm_dialogs()
        self.check_video()
        self.assertTrue(self.by_name(".mkv").selected)
        self.assertFalse(self.by_name("forced").selected)
        self.win.rename()
        APP.processEvents()
        self.assertEqual(self.out_names(), {"Show.S01E01.mkv"})

    def test_09_pref_de_plain_plus_forced_plain_is_partner(self):
        self._load(
            "Show.S01E01.mkv",
            "Show.S01E01.de.srt",
            "Show.S01E01.de.forced.srt",
        )
        self.win.set_subtitle_pref("de")
        self.set_copy_mode()
        self.confirm_dialogs()
        self.check_video()
        self.assertTrue(self.by_name("Show.S01E01.de.srt").selected)
        self.assertFalse(self.by_name("forced").selected)
        self.win.rename()
        APP.processEvents()
        self.assertEqual(self.out_names(), {"Show.S01E01.mkv", "Show.S01E01.srt"})

    def test_10_explicit_hu_kept_with_de_partner(self):
        self._load(
            "Show.S01E01.mkv",
            "Show.S01E01.de.srt",
            "Show.S01E01.hu.srt",
        )
        self.win.set_subtitle_pref("de")
        self.set_copy_mode()
        self.confirm_dialogs()
        self.check_video()
        self.check_file(".hu.srt")
        self.assertTrue(self.by_name(".de.srt").selected)
        self.assertTrue(self.by_name(".hu.srt").selected)
        self.win.rename()
        APP.processEvents()
        self.assertEqual(
            self.out_names(),
            {"Show.S01E01.mkv", "Show.S01E01.srt", "Show.S01E01.hu.srt"},
        )

    def test_11_explicit_hu_processable_without_de(self):
        self._load("Show.S01E01.mkv", "Show.S01E01.hu.srt")
        self.win.set_subtitle_pref("de")
        self.set_copy_mode()
        self.confirm_dialogs()
        self.check_video()
        self.check_file(".hu.srt")
        self.assertTrue(self.by_name(".mkv").selected)
        self.assertTrue(self.by_name(".hu.srt").selected)
        self.win.rename()
        APP.processEvents()
        self.assertEqual(self.out_names(), {"Show.S01E01.mkv", "Show.S01E01.hu.srt"})

    def test_12_explicit_hu_en_with_de_partner_all_processable(self):
        self._load(
            "Show.S01E01.mkv",
            "Show.S01E01.de.srt",
            "Show.S01E01.hu.srt",
            "Show.S01E01.en.srt",
        )
        self.win.set_subtitle_pref("de")
        self.set_copy_mode()
        self.confirm_dialogs()
        self.check_video()
        self.check_file(".hu.srt")
        self.check_file(".en.srt")
        self.assertEqual(
            self.selected_names(),
            {
                "Show.S01E01.mkv",
                "Show.S01E01.de.srt",
                "Show.S01E01.hu.srt",
                "Show.S01E01.en.srt",
            },
        )
        self.win.rename()
        APP.processEvents()
        self.assertEqual(
            self.out_names(),
            {
                "Show.S01E01.mkv",
                "Show.S01E01.srt",
                "Show.S01E01.hu.srt",
                "Show.S01E01.en.srt",
            },
        )

    def test_13_c1_and_ui_language_independent(self):
        self._load(
            "Show.S01E01.mkv",
            "Show.S01E01.de.srt",
            "Show.S01E01.hu.srt",
        )
        self.win.set_language("hu")
        self.win.set_subtitle_pref("hu")
        APP.processEvents()
        self.check_video()
        self.assertTrue(self.by_name(".hu.srt").selected)
        self.assertFalse(self.by_name(".de.srt").selected)
        self.assertIn("elsődleges", self._type_text("Show.S01E01.hu.srt"))
        self.assertNotIn("elsődleges", self._type_text("Show.S01E01.de.srt"))

        self.win.set_subtitle_pref("de")
        APP.processEvents()
        self.check_video()
        self.assertTrue(self.by_name(".de.srt").selected)
        self.assertFalse(self.by_name(".hu.srt").selected)
        self.assertEqual(self._type_text("Show.S01E01.de.srt"), "Német · SRT · elsődleges")
        self.assertNotIn("elsődleges", self._type_text("Show.S01E01.hu.srt"))

        self.win.set_language("en")
        APP.processEvents()
        self.assertEqual(self.win.subtitle_pref, "de")
        self.assertTrue(self.by_name(".de.srt").selected)
        self.assertEqual(self._type_text("Show.S01E01.de.srt"), "German · SRT · primary")


if __name__ == "__main__":
    unittest.main(verbosity=2)
