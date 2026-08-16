
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


class TestGuiExtraSubtitle(GuiBase):
    def test_unrelated_subtitle_does_not_join_video_group(self):
        src = make_case(self.tmp,
                        ("Show.S01E01.mkv", VIDEO),
                        ("Show.S01E01.hu.srt", SUB),
                        ("Other.Show.S01E01.hu.srt", SUB))
        self.add(*(src / n for n in
                   ("Show.S01E01.mkv", "Show.S01E01.hu.srt",
                    "Other.Show.S01E01.hu.srt")))
        self.win.analyze()
        video = next(i for i in self.win.items if i.kind == "video")
        good = next(i for i in self.win.items
                    if i.kind == "sub" and "Show.S01E01.hu" in Path(i.path).name)
        other = next(i for i in self.win.items
                     if i.kind == "sub" and "Other.Show" in Path(i.path).name)
        self.assertEqual(video.group, good.group)
        self.assertNotEqual(video.group, other.group)
if __name__ == "__main__":
    unittest.main(verbosity=2)
