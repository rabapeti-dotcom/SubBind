"""Guide állapot és Rename gomb: csak akkor „kész”, ha a művelet indítható."""
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
TEST_DATA_ROOT = Path(tempfile.mkdtemp(prefix="sr_gui26_data_"))
os.environ["SERIESRENAMER_DATA"] = str(TEST_DATA_ROOT)

from PySide6.QtWidgets import QApplication, QMessageBox

from i18n import t
from main import MainWindow

APP = QApplication.instance() or QApplication(sys.argv)

VIDEO = b"GUI26_VIDEO_0.6.1"
SUB = b"GUI26_SUB_0.6.1"


def make_pair(root, *names):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in names:
        path = root / name
        path.write_bytes(VIDEO if path.suffix.lower() == ".mkv" else SUB)
        paths.append(path)
    return paths


class TestGui26GuideRenameGate(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        if ORIGINAL_DATA is None:
            os.environ.pop("SERIESRENAMER_DATA", None)
        else:
            os.environ["SERIESRENAMER_DATA"] = ORIGINAL_DATA
        shutil.rmtree(TEST_DATA_ROOT, ignore_errors=True)

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_gui26_"))
        self.out = Path(tempfile.mkdtemp(prefix="sr_gui26_out_"))
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
        shutil.rmtree(self.tmp, ignore_errors=True)
        shutil.rmtree(self.out, ignore_errors=True)

    def load_ok_pair(self):
        paths = make_pair(
            self.tmp,
            "Show.S01E01.mkv",
            "Show.S01E01.hu.srt",
        )
        self.win.add_paths(paths)
        self.win.analyze()
        for item in self.win.items:
            if item.status == "OK":
                item.selected = True
        self.win.update_action_state()
        APP.processEvents()

    def set_copy_mode(self, output=""):
        self.win.output_mode = "Másolás kimeneti mappába és átnevezés"
        self.win.output_dir = str(output)
        self.win.output_mode_combo.setCurrentText(
            "Másolás kimeneti mappába és átnevezés"
        )
        self.win.output_edit.setText(str(output))
        self.win.update_action_state()
        APP.processEvents()

    def set_inplace_mode(self):
        self.win.output_mode = "Helyben átnevezés"
        self.win.output_dir = ""
        self.win.output_mode_combo.setCurrentText("Helyben átnevezés")
        self.win.output_edit.setText("")
        self.win.update_action_state()
        APP.processEvents()

    def banner_text(self):
        return self.win.guide_banner.text()

    def test_copy_without_output_dir_is_not_ready(self):
        self.set_copy_mode("")
        self.load_ok_pair()
        self.assertTrue(self.win._has_processable_ok())
        self.assertFalse(self.win._rename_output_ok())
        self.assertNotEqual(self.win._guided_state(), "ready")
        self.assertFalse(self.win.rename_btn.isEnabled())
        self.assertNotIn(t("guide.ready"), self.banner_text())

    def test_copy_with_output_dir_is_ready(self):
        self.set_copy_mode(self.out)
        self.load_ok_pair()
        self.assertTrue(self.win._rename_output_ok())
        self.assertEqual(self.win._guided_state(), "ready")
        self.assertTrue(self.win.rename_btn.isEnabled())
        self.assertIn(t("guide.ready"), self.banner_text())

    def test_inplace_without_output_dir_stays_ready(self):
        self.set_inplace_mode()
        self.load_ok_pair()
        self.assertTrue(self.win._rename_output_ok())
        self.assertEqual(self.win._guided_state(), "ready")
        self.assertTrue(self.win.rename_btn.isEnabled())
        self.assertIn(t("guide.ready"), self.banner_text())

    def test_copy_rename_still_succeeds_when_output_dir_is_set(self):
        self.set_copy_mode(self.out)
        self.load_ok_pair()
        QMessageBox.question = staticmethod(
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes
        )
        QMessageBox.information = staticmethod(
            lambda *args, **kwargs: QMessageBox.StandardButton.Ok
        )
        self.win._confirm_rename = lambda *args, **kwargs: True
        self.win.rename()
        APP.processEvents()
        self.assertTrue((self.out / "Show.S01E01.mkv").is_file())
        self.assertTrue((self.out / "Show.S01E01.srt").is_file())
        self.assertEqual(self.win.history[-1]["status"], "Sikeres")


if __name__ == "__main__":
    unittest.main(verbosity=2)
