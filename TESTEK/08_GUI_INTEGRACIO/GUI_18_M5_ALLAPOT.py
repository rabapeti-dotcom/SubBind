"""M5 GUI: kijelölés, Kész, Undo, M1.1/M2/M4 regresszió."""
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
TEST_DATA_ROOT = Path(tempfile.mkdtemp(prefix="sr_gui_m5_data_"))
os.environ["SERIESRENAMER_DATA"] = str(TEST_DATA_ROOT)

from PySide6.QtWidgets import QApplication, QCheckBox, QMessageBox

try:
    from main import MainWindow
except Exception as exc:
    raise RuntimeError(f"MainWindow nem tölthető be: {SRC / 'main.py'}") from exc

APP = QApplication.instance() or QApplication(sys.argv)

VIDEO = b"GUI_TEST_VIDEO_0.6.1"
SUB = b"GUI_TEST_SUB_0.6.1"


def make_case(root, *files):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for rel, data in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return root


class TestM5GuiAllapot(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        if ORIGINAL_DATA is None:
            os.environ.pop("SERIESRENAMER_DATA", None)
        else:
            os.environ["SERIESRENAMER_DATA"] = ORIGINAL_DATA
        shutil.rmtree(TEST_DATA_ROOT, ignore_errors=True)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_gui_m5_"))
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

    def test_checkbox_and_selection_commands(self):
        src = make_case(
            self.tmp,
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(src / "Show.S01E01.mkv", src / "Show.S01E01.hu.srt")
        item = self.by_name("Show.S01E01.mkv")
        row = self.win._visible_items().index(item)
        check = self.win.table.cellWidget(row, 0).findChild(QCheckBox)
        check.setChecked(False)
        APP.processEvents()
        self.assertFalse(item.selected)
        check = self.win.table.cellWidget(
            self.win._visible_items().index(item), 0
        ).findChild(QCheckBox)
        check.setChecked(True)
        APP.processEvents()
        self.assertTrue(item.selected)
        self.win.select_none_items()
        self.assertTrue(all(not i.selected for i in self.win.items))
        self.win.refresh()
        self.assertTrue(all(not i.selected for i in self.win.items))
        self.win.select_all_items()
        self.assertTrue(all(i.selected for i in self.win.items))
        self.win.select_missing_items()
        self.assertTrue(all(i.selected for i in self.win.items))

    def test_ready_undo_unsupported_and_regressions(self):
        src = make_case(
            self.tmp / "src",
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
            ("notes.txt", b"x"),
            ("Other.Show.S01E01.hu.srt", SUB),
        )
        out = self.tmp / "out"
        self.win.output_mode = "Másolás kimeneti mappába és átnevezés"
        self.win.output_dir = str(out)
        self.win.output_mode_combo.setCurrentText(
            "Másolás kimeneti mappába és átnevezés"
        )
        self.win.output_edit.setText(str(out))
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(
            src / "Show.S01E01.mkv",
            src / "Show.S01E01.hu.srt",
            src / "notes.txt",
            src / "Other.Show.S01E01.hu.srt",
        )
        extra = self.by_name("notes.txt")
        self.assertEqual(extra.status, "Nem támogatott")
        self.assertFalse(extra.selected)
        self.assertEqual(self.by_name("Show.S01E01.mkv").status, "OK")
        self.assertNotEqual(self.by_name("Other.Show").status, "OK")
        for item in self.win.items:
            if item.kind in ("video", "sub") and item.status == "OK":
                item.selected = True
        self.confirm_dialogs()
        self.win.rename()
        APP.processEvents()
        video = next(i for i in self.win.items if i.kind == "video")
        self.assertEqual(video.status, "Kész")
        self.win.refresh()
        video = next(i for i in self.win.items if i.kind == "video")
        self.assertEqual(video.status, "Kész")
        self.win.history_select_all()
        self.win.undo_selected()
        APP.processEvents()
        video = next(i for i in self.win.items if i.kind == "video")
        self.assertEqual(video.copy_status, "Várakozik")
        self.assertNotEqual(video.status, "Kész")
        self.win.refresh()
        video = next(i for i in self.win.items if i.kind == "video")
        self.assertEqual(video.status, "OK")
        extra = self.by_name("notes.txt")
        self.assertFalse(extra.selected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
