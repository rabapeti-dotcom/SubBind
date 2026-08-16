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

from PySide6.QtWidgets import QApplication, QMessageBox

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


class GuiBase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_gui_"))
        self.win = MainWindow()
        self.win.show()
        APP.processEvents()

    def tearDown(self):
        self.win.close()
        self.win.deleteLater()
        APP.processEvents()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def add(self, *paths):
        self.win.add_paths([Path(p) for p in paths])
        APP.processEvents()

    def set_copy_mode(self, output):
        self.win.output_mode = "Másolás kimeneti mappába és átnevezés"
        self.win.output_dir = str(output)
        if hasattr(self.win, "output_mode_combo"):
            self.win.output_mode_combo.setCurrentText(
                "Másolás kimeneti mappába és átnevezés"
            )
        if hasattr(self.win, "output_dir_edit"):
            self.win.output_dir_edit.setText(str(output))
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


class TestGuiNewOutput(GuiBase):
    def test_nonexistent_output_directory_is_created_by_copy_operation(self):
        # A filmteszt szándékosan csak a kimeneti mappa létrehozását vizsgálja.
        # Az elemzéshez azonban a jelenlegi alkalmazáslogika szerint egy
        # párosított HU feliratot adunk, hogy a rename() feldolgozható OK
        # státuszú csoportot kapjon.
        src = make_case(
            self.tmp,
            ("Movie.2024.mkv", VIDEO),
            ("Movie.2024.hu.srt", SUB),
        )
        video = src / "Movie.2024.mkv"
        subtitle = src / "Movie.2024.hu.srt"

        out = self.tmp / "does_not_exist_yet" / "nested"

        self.set_copy_mode(out)
        self.win.mode_combo.setCurrentText("Film")
        self.add(video, subtitle)
        self.win.analyze()

        selectable = [
            item for item in self.win.items
            if item.status == "OK"
        ]
        self.assertTrue(
            selectable,
            "Az analyze() után nincs OK státuszú elem."
        )
        for item in selectable:
            item.selected = True

        self.confirm_dialogs()
        self.win.rename()
        APP.processEvents()

        self.assertTrue(out.is_dir(), f"Kimeneti mappa nem jött létre: {out}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
