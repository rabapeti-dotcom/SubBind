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

    def confirm_dialogs(self):
        # A rename() több modális QMessageBox ágat használ.
        # Offscreen tesztben egyik sem állíthatja meg a tesztfolyamatot.
        QMessageBox.question = staticmethod(
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes
        )
        QMessageBox.information = staticmethod(
            lambda *args, **kwargs: QMessageBox.StandardButton.Ok
        )
        QMessageBox.warning = staticmethod(
            lambda *args, **kwargs: QMessageBox.StandardButton.Ok
        )


class TestGuiCopy(GuiBase):
    def test_copy_mode_creates_output_and_preserves_source(self):
        # Fontos: a főprogram az elem státuszát "Felirat nélkül"-re állítja,
        # ha nincs ugyanahhoz a csoporthoz tartozó felirat.
        # Ezért a valódi másolási tesztnek párosított HU feliratot is kell
        # létrehoznia.
        make_case(
            self.tmp,
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
        )

        source = self.tmp / "Show.S01E01.mkv"
        subtitle = self.tmp / "Show.S01E01.hu.srt"
        before = source.read_bytes()
        before_sub = subtitle.read_bytes()

        out = self.tmp / "new_output"

        self.set_copy_mode(out)
        self.add(source, subtitle)
        self.win.analyze()

        # A rename() csak selected=True és status=="OK" elemeket dolgoz fel.
        selectable = [
            item for item in self.win.items
            if item.status == "OK"
        ]
        self.assertTrue(
            selectable,
            "Az analyze() után nincs OK státuszú elem. "
            "A tesztadatoknak párosított videó + HU feliratot kell adniuk."
        )

        for item in selectable:
            item.selected = True

        self.confirm_dialogs()

        self.win.rename()
        APP.processEvents()

        target = out / "Show.S01E01.mkv"

        self.assertTrue(out.exists(), f"Kimeneti mappa nem jött létre: {out}")
        self.assertTrue(
            target.exists(),
            f"Célfájl nem jött létre: {target}"
        )
        self.assertEqual(
            source.read_bytes(),
            before,
            "A forrásvideó megváltozott."
        )
        self.assertEqual(
            subtitle.read_bytes(),
            before_sub,
            "A forrásfelirat megváltozott."
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
