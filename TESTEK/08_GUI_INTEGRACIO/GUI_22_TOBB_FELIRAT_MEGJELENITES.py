"""GUI_22: C.1 több felirat megjelenítés — primary a subtitle_pref szerint.

Motor pairing / kijelölés / rename kapu érintetlen (L2.3).
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

from i18n import t
from main import COL_ORIG, COL_TYPE, MainWindow, is_ui_primary_sub, type_cell_text

APP = QApplication.instance() or QApplication(sys.argv)


def make_case(root, *names):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in names:
        p = root / name
        p.write_bytes(b"GUI22")
        paths.append(p)
    return paths


class TestGui22MultiSubDisplay(unittest.TestCase):
    def setUp(self):
        self.original_data = os.environ.get("SERIESRENAMER_DATA")
        self.data_dir = Path(tempfile.mkdtemp(prefix="sr_gui22_data_"))
        os.environ["SERIESRENAMER_DATA"] = str(self.data_dir)
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_gui22_"))
        self.win = MainWindow()
        self.win.show_welcome = False
        self.win.show()
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

    def _load_names(self, *names):
        paths = make_case(self.tmp, *names)
        self.win.add_paths(paths)
        self.win.analyze()
        APP.processEvents()
        return {Path(i.path).name: i for i in self.win.items}

    def _load_sample(self):
        return self._load_names(
            "Show.S01E01.mkv",
            "Show.S01E01.hu.srt",
            "Show.S01E01.en.srt",
            "Show.S01E01.ass",
        )

    def _row_for(self, filename):
        for row in range(self.win.table.rowCount()):
            cell = self.win.table.item(row, COL_ORIG)
            if cell and cell.text() == filename:
                return row
        self.fail(f"Nincs sor: {filename}")

    def _type_text(self, filename):
        return self.win.table.item(self._row_for(filename), COL_TYPE).text()

    def _type_tip(self, filename):
        return self.win.table.item(self._row_for(filename), COL_TYPE).toolTip()

    def _assert_no_hscroll(self):
        bar = self.win.table.horizontalScrollBar()
        self.assertEqual(bar.maximum(), 0)

    def test_type_labels_and_engine_untouched(self):
        by_name = self._load_sample()
        self.assertEqual(len(self.win.items), 4)
        videos = [i for i in self.win.items if i.kind == "video"]
        subs = [i for i in self.win.items if i.kind == "sub"]
        self.assertEqual(len(videos), 1)
        self.assertEqual(len(subs), 3)

        selected_before = {id(i): i.selected for i in self.win.items}
        status_before = {id(i): i.status for i in self.win.items}
        groups = {i.group for i in self.win.items}
        self.assertEqual(len(groups), 1)

        self.win.set_language("hu")
        APP.processEvents()
        mkv = by_name["Show.S01E01.mkv"]
        hu = by_name["Show.S01E01.hu.srt"]
        en = by_name["Show.S01E01.en.srt"]
        ass = by_name["Show.S01E01.ass"]
        pref = self.win.subtitle_pref

        self.assertEqual(pref, "hu")
        self.assertEqual(type_cell_text(mkv, pref), t("kind.video"))
        self.assertEqual(type_cell_text(hu, pref), "Magyar · SRT · elsődleges")
        self.assertEqual(type_cell_text(en, pref), "Angol · SRT")
        self.assertEqual(type_cell_text(ass, pref), "— · ASS")
        self.assertTrue(is_ui_primary_sub(hu, pref))
        self.assertFalse(is_ui_primary_sub(en, pref))
        self.assertFalse(is_ui_primary_sub(ass, pref))
        self.assertIsNone(ass.lang)
        self.assertNotEqual(ass.lang, "hu")

        hu_row = self._row_for("Show.S01E01.hu.srt")
        self.assertEqual(self.win.table.item(hu_row, COL_TYPE).text(), "Magyar · SRT · elsődleges")
        self.assertIn("Nyelv: Magyar", self.win.table.item(hu_row, COL_TYPE).toolTip())
        self.assertIn("Elsődleges: igen", self.win.table.item(hu_row, COL_TYPE).toolTip())
        self._assert_no_hscroll()

        preview = self.win.preview_text.toPlainText()
        self.assertIn("1 videó · 3 felirat", preview)
        self.assertIn("felirat · Magyar · SRT · elsődleges", preview)
        self.assertIn("felirat · Angol · SRT", preview)
        self.assertIn("felirat · — · ASS", preview)

        self.win.filter_edit.setText("hu")
        self.win.refresh(reanalyze=False)
        APP.processEvents()
        visible_hu = [Path(i.path).name for i in self.win._visible_items()]
        self.assertIn("Show.S01E01.hu.srt", visible_hu)

        self.win.filter_edit.setText("ass")
        self.win.refresh(reanalyze=False)
        APP.processEvents()
        visible_ass = [Path(i.path).name for i in self.win._visible_items()]
        self.assertIn("Show.S01E01.ass", visible_ass)
        self.win.filter_edit.setText("")
        self.win.refresh(reanalyze=False)

        self.win.set_language("en")
        APP.processEvents()
        self.assertEqual(type_cell_text(mkv, pref), "video")
        self.assertEqual(type_cell_text(hu, pref), "Hungarian · SRT · primary")
        self.assertEqual(type_cell_text(en, pref), "English · SRT")
        self.assertEqual(type_cell_text(ass, pref), "— · ASS")
        self._assert_no_hscroll()

        self.win.filter_edit.setText("primary")
        self.win.refresh(reanalyze=False)
        APP.processEvents()
        visible_p = [Path(i.path).name for i in self.win._visible_items()]
        self.assertIn("Show.S01E01.hu.srt", visible_p)
        self.win.filter_edit.setText("")
        self.win.refresh(reanalyze=False)

        self.win.set_language("hu")
        APP.processEvents()

        for item in self.win.items:
            self.assertEqual(item.selected, selected_before[id(item)])
            self.assertEqual(item.status, status_before[id(item)])
        self.assertEqual({i.group for i in self.win.items}, groups)

    def test_l22_pref_hu_forced_not_primary(self):
        by_name = self._load_names(
            "Show.S01E01.mkv",
            "Show.S01E01.hu.srt",
            "Show.S01E01.hu.forced.srt",
            "Show.S01E01.de.srt",
        )
        self.win.set_subtitle_pref("hu")
        APP.processEvents()
        pref = self.win.subtitle_pref
        hu = by_name["Show.S01E01.hu.srt"]
        forced = by_name["Show.S01E01.hu.forced.srt"]
        de = by_name["Show.S01E01.de.srt"]
        self.assertTrue(is_ui_primary_sub(hu, pref))
        self.assertFalse(is_ui_primary_sub(forced, pref))
        self.assertFalse(is_ui_primary_sub(de, pref))
        self.assertIn("elsődleges", self._type_text("Show.S01E01.hu.srt"))
        self.assertNotIn("elsődleges", self._type_text("Show.S01E01.hu.forced.srt"))
        self.assertNotIn("elsődleges", self._type_text("Show.S01E01.de.srt"))

    def test_l22_pref_de_primary_surfaces(self):
        by_name = self._load_names(
            "Show.S01E01.mkv",
            "Show.S01E01.de.srt",
            "Show.S01E01.de.forced.srt",
            "Show.S01E01.hu.srt",
            "Show.S01E01.en.srt",
        )
        self.win.set_language("hu")
        self.win.set_subtitle_pref("de")
        APP.processEvents()
        pref = self.win.subtitle_pref
        de = by_name["Show.S01E01.de.srt"]
        forced = by_name["Show.S01E01.de.forced.srt"]
        hu = by_name["Show.S01E01.hu.srt"]
        en = by_name["Show.S01E01.en.srt"]
        self.assertTrue(is_ui_primary_sub(de, pref))
        self.assertFalse(is_ui_primary_sub(forced, pref))
        self.assertFalse(is_ui_primary_sub(hu, pref))
        self.assertFalse(is_ui_primary_sub(en, pref))
        self.assertEqual(self._type_text("Show.S01E01.de.srt"), "Német · SRT · elsődleges")
        self.assertIn("Elsődleges: igen", self._type_tip("Show.S01E01.de.srt"))
        self.assertIn("Elsődleges: nem", self._type_tip("Show.S01E01.hu.srt"))
        self.assertNotIn("elsődleges", self._type_text("Show.S01E01.de.forced.srt"))
        self.assertNotIn("elsődleges", self._type_text("Show.S01E01.hu.srt"))
        self.assertNotIn("elsődleges", self._type_text("Show.S01E01.en.srt"))
        preview = self.win.preview_text.toPlainText()
        self.assertIn("felirat · Német · SRT · elsődleges", preview)
        self.assertNotIn("Magyar · SRT · elsődleges", preview)
        self._assert_no_hscroll()

        self.win.filter_edit.setText("elsődleges")
        self.win.refresh(reanalyze=False)
        APP.processEvents()
        visible = [Path(i.path).name for i in self.win._visible_items()]
        self.assertIn("Show.S01E01.de.srt", visible)
        self.assertNotIn("Show.S01E01.hu.srt", visible)
        self.win.filter_edit.setText("")
        self.win.refresh(reanalyze=False)

    def test_l22_pref_en_and_es(self):
        by_name = self._load_names(
            "Show.S01E01.mkv",
            "Show.S01E01.en.srt",
            "Show.S01E01.en.forced.srt",
            "Show.S01E01.es.srt",
            "Show.S01E01.es.forced.srt",
        )
        self.win.set_subtitle_pref("en")
        APP.processEvents()
        self.assertTrue(is_ui_primary_sub(by_name["Show.S01E01.en.srt"], "en"))
        self.assertFalse(is_ui_primary_sub(by_name["Show.S01E01.en.forced.srt"], "en"))
        self.assertFalse(is_ui_primary_sub(by_name["Show.S01E01.es.srt"], "en"))
        self.assertIn("elsődleges", self._type_text("Show.S01E01.en.srt"))
        self.assertNotIn("elsődleges", self._type_text("Show.S01E01.en.forced.srt"))
        self.assertNotIn("elsődleges", self._type_text("Show.S01E01.es.srt"))

        self.win.set_subtitle_pref("es")
        APP.processEvents()
        self.assertTrue(is_ui_primary_sub(by_name["Show.S01E01.es.srt"], "es"))
        self.assertFalse(is_ui_primary_sub(by_name["Show.S01E01.es.forced.srt"], "es"))
        self.assertFalse(is_ui_primary_sub(by_name["Show.S01E01.en.srt"], "es"))
        self.assertIn("elsődleges", self._type_text("Show.S01E01.es.srt"))
        self.assertNotIn("elsődleges", self._type_text("Show.S01E01.es.forced.srt"))
        self.assertNotIn("elsődleges", self._type_text("Show.S01E01.en.srt"))

    def test_l22_two_plain_de_both_primary(self):
        by_name = self._load_names(
            "Show.S01E01.mkv",
            "Show.S01E01.de.srt",
            "Show.S01E01.ger.srt",
        )
        self.win.set_subtitle_pref("de")
        APP.processEvents()
        de = by_name["Show.S01E01.de.srt"]
        ger = by_name["Show.S01E01.ger.srt"]
        self.assertEqual(de.lang, "de")
        self.assertEqual(ger.lang, "de")
        self.assertTrue(is_ui_primary_sub(de, "de"))
        self.assertTrue(is_ui_primary_sub(ger, "de"))
        self.assertIn("elsődleges", self._type_text("Show.S01E01.de.srt"))
        self.assertIn("elsődleges", self._type_text("Show.S01E01.ger.srt"))
        preview = self.win.preview_text.toPlainText()
        self.assertEqual(preview.count("elsődleges"), 2)

    def test_l22_pref_de_no_fallback_primary(self):
        by_name = self._load_sample()
        self.win.set_subtitle_pref("de")
        APP.processEvents()
        hu = by_name["Show.S01E01.hu.srt"]
        en = by_name["Show.S01E01.en.srt"]
        ass = by_name["Show.S01E01.ass"]
        self.assertEqual(self.win.subtitle_pref, "de")
        self.assertFalse(is_ui_primary_sub(hu, self.win.subtitle_pref))
        self.assertFalse(is_ui_primary_sub(en, self.win.subtitle_pref))
        self.assertFalse(is_ui_primary_sub(ass, self.win.subtitle_pref))
        self.assertNotIn("elsődleges", self._type_text("Show.S01E01.hu.srt"))
        self.assertNotIn("elsődleges", self._type_text("Show.S01E01.en.srt"))
        mkv = by_name["Show.S01E01.mkv"]
        self.assertEqual(mkv.status, "OK")
        self.assertEqual(mkv.note, "Nincs sima DE felirat")

    def test_l22_ui_language_independent(self):
        by_name = self._load_names(
            "Show.S01E01.mkv",
            "Show.S01E01.de.srt",
            "Show.S01E01.hu.srt",
        )
        de = by_name["Show.S01E01.de.srt"]
        hu = by_name["Show.S01E01.hu.srt"]

        self.win.set_language("hu")
        self.win.set_subtitle_pref("de")
        APP.processEvents()
        self.assertEqual(self.win.language, "hu")
        self.assertEqual(self.win.subtitle_pref, "de")
        self.assertTrue(is_ui_primary_sub(de, self.win.subtitle_pref))
        self.assertFalse(is_ui_primary_sub(hu, self.win.subtitle_pref))
        self.assertEqual(self._type_text("Show.S01E01.de.srt"), "Német · SRT · elsődleges")
        self.assertEqual(self.win.subtitle_pref_label.text(), "Preferált felirat nyelve:")
        self._assert_no_hscroll()

        self.win.set_language("en")
        APP.processEvents()
        self.assertEqual(self.win.language, "en")
        self.assertEqual(self.win.subtitle_pref, "de")
        self.assertTrue(is_ui_primary_sub(de, self.win.subtitle_pref))
        self.assertFalse(is_ui_primary_sub(hu, self.win.subtitle_pref))
        self.assertEqual(self._type_text("Show.S01E01.de.srt"), "German · SRT · primary")
        self.assertIn("Primary: yes", self._type_tip("Show.S01E01.de.srt"))
        self.assertEqual(self.win.subtitle_pref_label.text(), "Preferred subtitle language:")
        self._assert_no_hscroll()

        self.win.filter_edit.setText("primary")
        self.win.refresh(reanalyze=False)
        APP.processEvents()
        visible = [Path(i.path).name for i in self.win._visible_items()]
        self.assertIn("Show.S01E01.de.srt", visible)
        self.assertNotIn("Show.S01E01.hu.srt", visible)
        self.win.filter_edit.setText("")
        self.win.refresh(reanalyze=False)

        self.win.set_language("hu")
        APP.processEvents()
        self.assertEqual(self.win.subtitle_pref, "de")
        self.assertTrue(is_ui_primary_sub(de, self.win.subtitle_pref))
        self.assertEqual(self._type_text("Show.S01E01.de.srt"), "Német · SRT · elsődleges")


if __name__ == "__main__":
    unittest.main(verbosity=2)
