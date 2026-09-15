"""
F51/F52 history állapot: pair rollback, maradék changes, váratlan hiba, részleges undo.
"""
from pathlib import Path
import os
import shutil
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ORIGINAL_DATA = os.environ.get("SERIESRENAMER_DATA")
TEST_DATA_ROOT = Path(tempfile.mkdtemp(prefix="sr_f52_hist_data_"))
os.environ["SERIESRENAMER_DATA"] = str(TEST_DATA_ROOT)

from PySide6.QtWidgets import QApplication, QMessageBox

import main as app_main
from main import MainWindow
from renamer_engine import copy_to_destination

APP = QApplication.instance() or QApplication(sys.argv)

VIDEO = b"F52_HIST_VIDEO_0.6.1"
SUB = b"F52_HIST_SUB_0.6.1"


def make_case(root, *files):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for rel, data in files:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return root


class TestF52HistoryState(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        if ORIGINAL_DATA is None:
            os.environ.pop("SERIESRENAMER_DATA", None)
        else:
            os.environ["SERIESRENAMER_DATA"] = ORIGINAL_DATA
        shutil.rmtree(TEST_DATA_ROOT, ignore_errors=True)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_f52_hist_"))
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
        app_main.copy_to_destination = copy_to_destination
        self.win.close()
        self.win.deleteLater()
        APP.processEvents()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def add(self, *paths):
        self.win.add_paths([Path(path) for path in paths])
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

    def set_copy_mode(self, output):
        self.win.output_mode = "Másolás kimeneti mappába és átnevezés"
        self.win.output_dir = str(output)
        self.win.output_mode_combo.setCurrentText(
            "Másolás kimeneti mappába és átnevezés"
        )
        self.win.output_edit.setText(str(output))
        APP.processEvents()

    def prepare_pair(self, *names):
        src = make_case(self.tmp / "src", *((name, VIDEO if name.endswith(".mkv") else SUB) for name in names))
        out = self.tmp / "out"
        self.set_copy_mode(out)
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(*[src / name for name in names])
        self.win.analyze()
        for item in self.win.items:
            if item.status == "OK":
                item.selected = True
        self.confirm_dialogs()
        return src, out

    def test_pair_copy_error_rolls_back_and_keeps_only_failed(self):
        src, out = self.prepare_pair("Show.S01E01.mkv", "Show.S01E01.hu.srt")
        original = app_main.copy_to_destination

        def fail_subtitle(old, new, progress=None):
            if Path(old).suffix.lower() == ".srt":
                raise OSError("Simulated pair copy error")
            return original(old, new, progress)

        app_main.copy_to_destination = fail_subtitle
        self.win.rename()
        APP.processEvents()

        self.assertFalse((out / "Show.S01E01.mkv").exists())
        self.assertFalse((out / "Show.S01E01.srt").exists())
        self.assertTrue((src / "Show.S01E01.mkv").is_file())
        self.assertTrue((src / "Show.S01E01.hu.srt").is_file())
        self.assertEqual(len(self.win.history), 1)
        record = self.win.history[0]
        self.assertEqual(record["status"], "Részben elkészült")
        self.assertEqual(record["changes"], [])
        self.assertEqual(len(record["failed"]), 2)
        reasons = " ".join(entry["reason"] for entry in record["failed"])
        self.assertIn("Simulated pair copy error", reasons)
        self.assertIn("pár visszaállítva", reasons)

    def test_rollback_unlink_failure_keeps_leftover_in_changes(self):
        src, out = self.prepare_pair("Show.S01E01.mkv", "Show.S01E01.hu.srt")
        video_dest = out / "Show.S01E01.mkv"
        original_copy = app_main.copy_to_destination
        original_unlink = Path.unlink

        def fail_subtitle(old, new, progress=None):
            if Path(old).suffix.lower() == ".srt":
                raise OSError("Simulated pair copy error")
            return original_copy(old, new, progress)

        def fail_video_dest_unlink(path, *args, **kwargs):
            current = Path(path)
            try:
                same = current.resolve() == video_dest.resolve()
            except OSError:
                same = os.path.normcase(str(current)) == os.path.normcase(str(video_dest))
            if same:
                raise OSError("Simulated rollback unlink error")
            return original_unlink(path, *args, **kwargs)

        app_main.copy_to_destination = fail_subtitle
        Path.unlink = fail_video_dest_unlink
        try:
            self.win.rename()
            APP.processEvents()
        finally:
            Path.unlink = original_unlink

        self.assertTrue(video_dest.is_file())
        self.assertFalse((out / "Show.S01E01.srt").exists())
        self.assertEqual(len(self.win.history), 1)
        record = self.win.history[0]
        self.assertEqual(record["status"], "Részben elkészült")
        self.assertEqual(len(record["changes"]), 1)
        self.assertEqual(Path(record["changes"][0]["new"]).name, "Show.S01E01.mkv")
        self.assertTrue(any("rollbackje sikertelen" in entry["reason"] for entry in record["failed"]))
        self.assertTrue(any("Simulated pair copy error" in entry["reason"] for entry in record["failed"]))

    def test_unexpected_error_after_first_pair_still_saves_history(self):
        src, out = self.prepare_pair(
            "Show.S01E01.mkv",
            "Show.S01E01.hu.srt",
            "Show.S01E02.mkv",
            "Show.S01E02.hu.srt",
        )
        original_usage = app_main.shutil.disk_usage
        calls = {"n": 0}

        def fail_on_second_pair(path):
            calls["n"] += 1
            if calls["n"] >= 3:
                raise OSError("Simulated volume error")
            return original_usage(path)

        app_main.shutil.disk_usage = fail_on_second_pair
        try:
            self.win.rename()
            APP.processEvents()
        finally:
            app_main.shutil.disk_usage = original_usage

        self.assertTrue((out / "Show.S01E01.mkv").is_file())
        self.assertTrue((out / "Show.S01E01.srt").is_file())
        self.assertFalse((out / "Show.S01E02.mkv").exists())
        self.assertEqual(len(self.win.history), 1)
        record = self.win.history[0]
        self.assertEqual(record["status"], "Részben elkészült")
        self.assertEqual(len(record["changes"]), 2)
        self.assertTrue(all(change["action"] == "copy" for change in record["changes"]))
        self.assertTrue((src / "Show.S01E01.mkv").is_file())

    def test_partial_copy_undo_keeps_remaining_change_retryable(self):
        src, out = self.prepare_pair("Show.S01E01.mkv", "Show.S01E01.hu.srt")
        self.win.rename()
        APP.processEvents()
        video_dest = out / "Show.S01E01.mkv"
        sub_dest = out / "Show.S01E01.srt"
        self.assertTrue(video_dest.is_file())
        self.assertTrue(sub_dest.is_file())
        original_unlink = Path.unlink

        def fail_video_dest_unlink(path, *args, **kwargs):
            current = Path(path)
            try:
                same = current.resolve() == video_dest.resolve()
            except OSError:
                same = os.path.normcase(str(current)) == os.path.normcase(str(video_dest))
            if same:
                raise OSError("Simulated undo unlink error")
            return original_unlink(path, *args, **kwargs)

        Path.unlink = fail_video_dest_unlink
        try:
            self.win.history_select_all()
            self.win.undo_selected()
            APP.processEvents()
        finally:
            Path.unlink = original_unlink

        self.assertTrue(video_dest.is_file())
        self.assertFalse(sub_dest.exists())
        record = self.win.history[0]
        self.assertEqual(record["status"], "Részben elkészült")
        self.assertEqual(len(record["changes"]), 1)
        self.assertEqual(Path(record["changes"][0]["new"]).name, "Show.S01E01.mkv")
        self.assertTrue(any("Visszaállítás sikertelen" in entry["reason"] for entry in record["failed"]))

        self.win.history_select_all()
        self.win.undo_selected()
        APP.processEvents()
        self.assertFalse(video_dest.exists())
        self.assertEqual(self.win.history[0]["status"], "Visszavonva")
        self.assertTrue((src / "Show.S01E01.mkv").is_file())
        self.assertTrue((src / "Show.S01E01.hu.srt").is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
