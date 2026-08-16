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


class TestGuiSubdirectories(GuiBase):
    def test_recursive_setting_loads_nested_files(self):
        # A korábbi verzióban a "season2" először fájlként jött létre,
        # majd könyvtárként próbáltuk létrehozni. Ez itt javítva van.
        src = make_case(
            self.tmp,
            ("root.mkv", VIDEO),
        )

        nested = src / "season2"
        nested.mkdir(parents=True, exist_ok=True)
        nested_video = nested / "Show.S02E01.mkv"
        nested_video.write_bytes(VIDEO)

        self.win.subdirs_cb.setChecked(True)

        # A mappabetöltő GUI-ág QFileDialogot használ, ezért a tényleges
        # fájlutakat közvetlenül adjuk át az add_paths() rétegen keresztül.
        paths = [p for p in src.rglob("*") if p.is_file()]
        self.add(*paths)

        self.assertEqual(len(self.win.items), 2)
        self.assertTrue(
            any(Path(i.path).parent == nested for i in self.win.items),
            "A nested könyvtárból származó fájl nem került be."
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
