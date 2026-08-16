from pathlib import Path
import os
import sys
import shutil
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from PySide6.QtWidgets import QApplication
from main import MainWindow

APP = QApplication.instance() or QApplication(sys.argv)
VIDEO = b"GUI10_DIAG_TEST_VIDEO"

class TestGui10Diagnostics(unittest.TestCase):
    """
    GUI-10 diagnosztikai teszt.

    SZÁNDÉKOSAN NEM HÍVJA MEG A win.rename() METÓDUST.
    A cél az, hogy megállapítsuk, meddig jut el a program biztonságosan:
      D1 fájl létrehozás
      D2 MainWindow
      D3 add_paths
      D4 analyze
      D5 másolási mód + célmappa
      D6 célútvonal / státusz ellenőrzés
      D7 Qt eseményhurok
      D8 valódi Python shutil.copy2 kontrollmásolat
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_gui10_diag_"))
        self.source = self.tmp / "Show.S01E01.mkv"
        self.output = self.tmp / "output_not_created_yet"
        self.source.write_bytes(VIDEO)

        self.win = None

    def tearDown(self):
        if self.win is not None:
            try:
                self.win.close()
                self.win.deleteLater()
                APP.processEvents()
            except Exception:
                pass
        shutil.rmtree(self.tmp, ignore_errors=True)

    def checkpoint(self, name):
        print(f"DIAG-PASS: {name}", flush=True)

    def test_gui10_until_copy_boundary(self):
        self.checkpoint("D1 forrásfájl létrehozva")
        self.assertTrue(self.source.exists())
        self.assertEqual(self.source.read_bytes(), VIDEO)

        self.win = MainWindow()
        self.win.show()
        APP.processEvents()
        self.checkpoint("D2 MainWindow elindult")

        self.win.add_paths([self.source])
        APP.processEvents()
        self.assertEqual(len(self.win.items), 1)
        self.checkpoint("D3 add_paths rendben")

        self.win.analyze()
        APP.processEvents()
        self.assertEqual(len(self.win.items), 1)
        self.assertTrue(self.win.items[0].new_name)
        self.checkpoint(
            f"D4 analyze rendben — new_name={self.win.items[0].new_name!r}"
        )

        # A GUI belső állapotát állítjuk be, valódi fájlválasztó nélkül.
        self.win.output_mode = "Másolás kimeneti mappába és átnevezés"
        self.win.output_dir = str(self.output)

        if hasattr(self.win, "output_mode_combo"):
            self.win.output_mode_combo.setCurrentText(
                "Másolás kimeneti mappába és átnevezés"
            )
        if hasattr(self.win, "output_dir_edit"):
            self.win.output_dir_edit.setText(str(self.output))

        APP.processEvents()
        self.checkpoint(
            f"D5 másolási mód beállítva — output={self.output}"
        )

        # A kimeneti mappa itt még szándékosan nem létezik.
        self.assertFalse(self.output.exists())

        # Csak a GUI előzetes kimeneti ellenőrzését vizsgáljuk.
        if hasattr(self.win, "_output_path_error"):
            err = self.win._output_path_error(self.win.items)
            self.checkpoint(f"D6 _output_path_error visszatért: {err!r}")
            self.assertFalse(err, f"Előzetes kimeneti hiba: {err}")

        # Qt életciklus ellenőrzés.
        APP.processEvents()
        self.checkpoint("D7 Qt eseményhurok rendben")

        # Kontrollteszt: ugyanebben a tesztkörnyezetben az OS-szintű másolás
        # működik. Ezzel elkülönítjük a Qt/GUI és az egyszerű fájlmásolás kérdését.
        self.output.mkdir(parents=True, exist_ok=True)
        control_target = self.output / self.source.name
        shutil.copy2(self.source, control_target)
        self.assertTrue(control_target.exists())
        self.assertEqual(control_target.read_bytes(), VIDEO)
        self.checkpoint("D8 kontroll copy2 rendben")

        # A főprogram rename() nincs meghívva.
        self.assertTrue(self.source.exists())
        self.assertEqual(self.source.read_bytes(), VIDEO)
        self.checkpoint("D9 forrás továbbra is érintetlen")

if __name__ == "__main__":
    unittest.main(verbosity=2)
