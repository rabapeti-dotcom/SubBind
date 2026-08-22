"""
M5: GUI kijelölés, Kész megőrzés/törlés, Undo listaállapot, regresszió.
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
ORIGINAL_DATA = os.environ.get("SERIESRENAMER_DATA")
TEST_DATA_ROOT = Path(tempfile.mkdtemp(prefix="sr_m5_data_"))
os.environ["SERIESRENAMER_DATA"] = str(TEST_DATA_ROOT)

from PySide6.QtWidgets import QApplication, QCheckBox, QMessageBox

from main import MainWindow

APP = QApplication.instance() or QApplication(sys.argv)

VIDEO = b"M5_TEST_VIDEO_0.6.1"
SUB = b"M5_TEST_SUB_0.6.1"


def make_case(root, *files):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for rel, data in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return root


class TestM5Allapot(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        if ORIGINAL_DATA is None:
            os.environ.pop("SERIESRENAMER_DATA", None)
        else:
            os.environ["SERIESRENAMER_DATA"] = ORIGINAL_DATA
        shutil.rmtree(TEST_DATA_ROOT, ignore_errors=True)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_m5_"))
        self.message_box_methods = {
            "question": QMessageBox.question,
            "information": QMessageBox.information,
            "warning": QMessageBox.warning,
            "critical": QMessageBox.critical,
        }
        self.win = MainWindow()
        self.win.show_welcome = False
        self.win.history = []
        self.win.history_selected_keys.clear()
        self.win.save_history()
        self.win.show()
        APP.processEvents()

    def tearDown(self):
        for name, method in self.message_box_methods.items():
            setattr(QMessageBox, name, method)
        self.win.close()
        self.win.deleteLater()
        APP.processEvents()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def add(self, *paths):
        self.win.add_paths([Path(p) for p in paths])
        APP.processEvents()

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

    def set_copy_mode(self, output):
        self.win.output_mode = "Másolás kimeneti mappába és átnevezés"
        self.win.output_dir = str(output)
        self.win.output_mode_combo.setCurrentText(
            "Másolás kimeneti mappába és átnevezés"
        )
        self.win.output_edit.setText(str(output))
        APP.processEvents()

    def test_checkbox_select_and_deselect_match_item_selected(self):
        src = make_case(
            self.tmp,
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(src / "Show.S01E01.mkv", src / "Show.S01E01.hu.srt")
        check, item = self.checkbox_for("Show.S01E01.mkv")
        check.setChecked(False)
        APP.processEvents()
        self.assertFalse(item.selected)
        self.assertFalse(check.isChecked())
        check, item = self.checkbox_for("Show.S01E01.mkv")
        check.setChecked(True)
        APP.processEvents()
        self.assertTrue(item.selected)
        check, item = self.checkbox_for("Show.S01E01.mkv")
        self.assertTrue(check.isChecked())
        selected_before = item.selected
        visible = self.win._visible_items()
        self.win._table_cell_clicked(visible.index(item), 0)
        APP.processEvents()
        self.assertEqual(item.selected, selected_before)

    def test_select_all_none_missing_and_refresh_keep_selection(self):
        src = make_case(
            self.tmp,
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(src / "Show.S01E01.mkv", src / "Show.S01E01.hu.srt")
        self.win.select_all_items()
        self.assertTrue(all(i.selected for i in self.win.items))
        self.win.select_none_items()
        self.assertTrue(all(not i.selected for i in self.win.items))
        self.win.refresh()
        self.assertTrue(all(not i.selected for i in self.win.items))
        self.win.select_missing_items()
        self.assertTrue(all(i.selected for i in self.win.items))

    def test_ready_status_kept_when_output_exists_cleared_when_gone(self):
        src = make_case(
            self.tmp / "src",
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
        )
        out = self.tmp / "out"
        self.set_copy_mode(out)
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(src / "Show.S01E01.mkv", src / "Show.S01E01.hu.srt")
        self.win.analyze()
        for item in self.win.items:
            item.selected = True
        self.confirm_dialogs()
        self.win.rename()
        APP.processEvents()
        video = self.by_name("Show.S01E01.mkv")
        self.assertEqual(video.status, "Kész")
        self.assertEqual(video.copy_status, "Átmásolva")
        self.win.refresh()
        video = self.by_name("Show.S01E01.mkv")
        self.assertEqual(video.status, "Kész")
        self.assertEqual(video.copy_status, "Átmásolva")
        dest = out / "Show.S01E01.mkv"
        dest.unlink()
        self.win.refresh()
        video = next(i for i in self.win.items if i.kind == "video")
        self.assertNotEqual(video.status, "Kész")
        self.assertEqual(video.copy_status, "Várakozik")

    def test_undo_restores_gui_and_survives_refresh(self):
        src = make_case(
            self.tmp / "src",
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
        )
        out = self.tmp / "out"
        self.set_copy_mode(out)
        self.win.mode_combo.setCurrentText("Sorozat")
        video_path = src / "Show.S01E01.mkv"
        self.add(video_path, src / "Show.S01E01.hu.srt")
        self.win.analyze()
        for item in self.win.items:
            item.selected = True
        self.confirm_dialogs()
        self.win.rename()
        APP.processEvents()
        self.win.history_select_all()
        self.win.undo_selected()
        APP.processEvents()
        video = next(i for i in self.win.items if i.kind == "video")
        self.assertEqual(Path(video.path).resolve(), video_path.resolve())
        self.assertNotEqual(video.status, "Kész")
        self.assertEqual(video.copy_status, "Várakozik")
        self.win.refresh()
        video = next(i for i in self.win.items if i.kind == "video")
        self.assertEqual(Path(video.path).resolve(), video_path.resolve())
        self.assertEqual(video.status, "OK")
        self.assertEqual(video.new_name, "Show.S01E01.mkv")

    def test_unsupported_stays_unselected(self):
        src = make_case(
            self.tmp,
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
            ("notes.txt", b"x"),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(src / "Show.S01E01.mkv", src / "Show.S01E01.hu.srt", src / "notes.txt")
        extra = self.by_name("notes.txt")
        self.assertEqual(extra.status, "Nem támogatott")
        self.assertFalse(extra.selected)
        self.win.select_all_items()
        self.assertFalse(extra.selected)
        extra.selected = True
        self.win.refresh()
        extra = self.by_name("notes.txt")
        self.assertFalse(extra.selected)

    def test_m11_m2_m4_regressions(self):
        src = make_case(
            self.tmp,
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
            ("Other.Show.S01E01.hu.srt", SUB),
            ("Invasion.S01E01.WEBRip.x264.mkv", VIDEO),
            ("Invasion.S01E01.WEBRip.x264-ION10.hun.srt", SUB),
            ("Show.S02E01.mkv", VIDEO),
            ("Show.S02E01.hu.srt", SUB),
            ("Show.S02E01.hu.forced.srt", SUB),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(
            src / "Show.S01E01.mkv",
            src / "Show.S01E01.hu.srt",
            src / "Other.Show.S01E01.hu.srt",
            src / "Invasion.S01E01.WEBRip.x264.mkv",
            src / "Invasion.S01E01.WEBRip.x264-ION10.hun.srt",
            src / "Show.S02E01.mkv",
            src / "Show.S02E01.hu.srt",
            src / "Show.S02E01.hu.forced.srt",
        )
        self.win.analyze()
        self.assertEqual(self.by_name("Show.S01E01.mkv").status, "OK")
        self.assertEqual(self.by_name("Show.S01E01.hu.srt").status, "OK")
        self.assertNotEqual(self.by_name("Other.Show").status, "OK")
        self.assertEqual(
            self.by_name("Invasion.S01E01.WEBRip.x264.mkv").new_name,
            "Invasion.S01E01.mkv",
        )
        self.assertEqual(self.by_name("ION10").new_name, "Invasion.S01E01.srt")
        self.assertEqual(self.by_name("Show.S02E01.hu.srt").new_name, "Show.S02E01.srt")
        self.assertEqual(self.by_name("forced").new_name, "Show.S02E01.forced.srt")


if __name__ == "__main__":
    unittest.main(verbosity=2)
