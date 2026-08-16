
from pathlib import Path
import os
import sys
import shutil
import tempfile
import unittest

# A tesztet a projekt TESTEK/08_GUI_INTEGRACIO könyvtárából futtatjuk.
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

    def confirm_yes(self):
        QMessageBox.question = staticmethod(
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes
        )


class TestGuiFilmPair(GuiBase):
    def test_film_mode_pairs_hu_subtitle(self):
        src = make_case(self.tmp,
                        ("Silver Harbor 2024 1080p.mkv", VIDEO),
                        ("Silver Harbor 2024 HUN.srt", SUB))
        self.win.mode_combo.setCurrentText("Film")
        self.add(src / "Silver Harbor 2024 1080p.mkv",
                 src / "Silver Harbor 2024 HUN.srt")
        self.win.analyze()
        videos = [i for i in self.win.items if i.kind == "video"]
        subs = [i for i in self.win.items if i.kind == "sub"]
        self.assertEqual(len(videos), 1)
        self.assertEqual(len(subs), 1)
        self.assertEqual(videos[0].group, subs[0].group)
        self.assertEqual(videos[0].new_name, "Silver.Harbor.2024.mkv")
        self.assertEqual(subs[0].new_name, "Silver.Harbor.2024.srt")
if __name__ == "__main__":
    unittest.main(verbosity=2)
