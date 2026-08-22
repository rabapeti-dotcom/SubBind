"""GUI-integrációs regressziós teszt a másolásos előzmény visszavonására."""
from pathlib import Path
import hashlib
import json
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
TEST_DATA_ROOT = Path(tempfile.mkdtemp(prefix="sr_gui_data_"))
os.environ["SERIESRENAMER_DATA"] = str(TEST_DATA_ROOT)

from PySide6.QtWidgets import QApplication, QMessageBox

try:
    from main import MainWindow
except Exception as exc:
    raise RuntimeError(f"MainWindow nem tölthető be: {SRC / 'main.py'}") from exc


APP = QApplication.instance() or QApplication(sys.argv)

VIDEO = b"GUI_HISTORY_UNDO_VIDEO_0.6.1"
SUB = b"GUI_HISTORY_UNDO_SUB_0.6.1"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_case(root, *files):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for rel, data in files:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return root


class GuiBase(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        if ORIGINAL_DATA is None:
            os.environ.pop("SERIESRENAMER_DATA", None)
        else:
            os.environ["SERIESRENAMER_DATA"] = ORIGINAL_DATA
        shutil.rmtree(TEST_DATA_ROOT, ignore_errors=True)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_gui_history_"))
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

        self.assertTrue(
            self.win.data_dir.is_relative_to(TEST_DATA_ROOT)
            or self.win.data_dir.resolve() == TEST_DATA_ROOT.resolve(),
            f"A teszt nem izolált data mappát használ: {self.win.data_dir}",
        )

    def tearDown(self):
        for name, method in self.message_box_methods.items():
            setattr(QMessageBox, name, method)
        self.win.close()
        self.win.deleteLater()
        APP.processEvents()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def add(self, *paths):
        self.win.add_paths([Path(path) for path in paths])
        APP.processEvents()

    def set_copy_mode(self, output):
        self.win.output_mode = "Másolás kimeneti mappába és átnevezés"
        self.win.output_dir = str(output)
        self.win.output_mode_combo.setCurrentText(
            "Másolás kimeneti mappába és átnevezés"
        )
        self.win.output_edit.setText(str(output))
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


class TestGuiHistoryUndo(GuiBase):
    def test_copy_operation_is_undone_through_history(self):
        source_dir = make_case(
            self.tmp / "source",
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
        )
        video = source_dir / "Show.S01E01.mkv"
        subtitle = source_dir / "Show.S01E01.hu.srt"
        video_digest = sha256(video)
        subtitle_digest = sha256(subtitle)
        output_dir = self.tmp / "output"

        self.set_copy_mode(output_dir)
        self.add(video, subtitle)
        self.win.analyze()

        selected = [item for item in self.win.items if item.status == "OK"]
        self.assertEqual(len(selected), 2, "A videó + HU felirat pár legyen feldolgozható.")
        for item in selected:
            item.selected = True

        self.confirm_dialogs()
        self.win.rename()
        APP.processEvents()

        target_video = output_dir / "Show.S01E01.mkv"
        target_subtitle = output_dir / "Show.S01E01.srt"
        self.assertTrue(target_video.is_file())
        self.assertTrue(target_subtitle.is_file())
        self.assertEqual(sha256(video), video_digest)
        self.assertEqual(sha256(subtitle), subtitle_digest)

        self.assertEqual(len(self.win.history), 1)
        record = self.win.history[0]
        self.assertEqual(record["operation"], "Másolás és átnevezés")
        self.assertEqual(record["status"], "Sikeres")
        self.assertEqual(len(record["changes"]), 2)

        history_path = TEST_DATA_ROOT / "history.json"
        self.assertTrue(history_path.is_file())
        persisted = json.loads(history_path.read_text(encoding="utf-8"))
        self.assertEqual(len(persisted), 1)
        self.assertEqual(persisted[0]["status"], "Sikeres")

        self.win.history_select_all()
        self.assertEqual(self.win._selected_history_indices(), [0])
        self.win.undo_selected()
        APP.processEvents()

        self.assertFalse(target_video.exists())
        self.assertFalse(target_subtitle.exists())
        self.assertEqual(sha256(video), video_digest)
        self.assertEqual(sha256(subtitle), subtitle_digest)
        self.assertEqual(self.win.history[0]["status"], "Visszavonva")

        persisted = json.loads(history_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted[0]["status"], "Visszavonva")


if __name__ == "__main__":
    unittest.main(verbosity=2)
