"""
M6 GUI: táblázat oszlopok, tooltip, DND, mappa, nagy lista idők.
"""
from pathlib import Path
import os
import sys
import shutil
import tempfile
import time
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QMimeData, QUrl
from PySide6.QtWidgets import QApplication, QMessageBox

from main import MainWindow, format_size_bytes

APP = QApplication.instance() or QApplication(sys.argv)

VIDEO = b"M6_GUI_VIDEO_0.6.1"
SUB = b"M6_GUI_SUB_0.6.1"


def make_case(root, *files):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for rel, data in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return root


class _Drop:
    def __init__(self, paths):
        self._mime = QMimeData()
        self._mime.setUrls([QUrl.fromLocalFile(str(p)) for p in paths])
        self.accepted = False

    def mimeData(self):
        return self._mime

    def acceptProposedAction(self):
        self.accepted = True


class TestGuiM6InputLista(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_m6_gui_"))
        self.message_box_methods = {
            "question": QMessageBox.question,
            "information": QMessageBox.information,
            "warning": QMessageBox.warning,
            "critical": QMessageBox.critical,
        }
        QMessageBox.information = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)
        QMessageBox.warning = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)
        QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
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

    def add(self, *paths):
        self.win.add_paths([Path(p) for p in paths])
        APP.processEvents()

    def test_table_has_size_column(self):
        self.assertEqual(self.win.table.columnCount(), 10)
        headers = [
            self.win.table.horizontalHeaderItem(i).text()
            for i in range(self.win.table.columnCount())
        ]
        self.assertEqual(headers[5], "Méret")
        self.assertEqual(headers[6], "Eredeti")

    def test_add_files_and_size_cell(self):
        src = make_case(
            self.tmp,
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
        )
        self.add(src / "Show.S01E01.mkv", src / "Show.S01E01.hu.srt")
        self.assertEqual(self.win.table.rowCount(), 2)
        size_cell = self.win.table.item(0, 5)
        self.assertIsNotNone(size_cell)
        self.assertTrue(size_cell.text().endswith(("B", "KB", "MB", "GB")))
        self.assertIn("B", size_cell.toolTip())

    def test_folder_and_duplicate_folder(self):
        src = make_case(self.tmp / "dir", ("Show.S01E01.mkv", VIDEO))
        self.win._ingest_user_paths([src, src])
        APP.processEvents()
        self.assertEqual(len(self.win.items), 1)
        self.assertEqual(self.win.table.rowCount(), 1)

    def test_subdirectory_and_long_name_tooltip(self):
        long_name = ("LongName." * 10) + "S01E01.mkv"
        src = make_case(self.tmp / "root", ("a.mkv", VIDEO))
        nested = src / "nested"
        nested.mkdir()
        (nested / long_name).write_bytes(VIDEO)
        self.win.subdirs_cb.setChecked(True)
        self.win._ingest_user_paths([src])
        APP.processEvents()
        self.assertEqual(len(self.win.items), 2)
        row = next(
            r for r in range(self.win.table.rowCount())
            if long_name in (self.win.table.item(r, 6).text() if self.win.table.item(r, 6) else "")
        )
        tip = self.win.table.item(row, 6).toolTip()
        self.assertIn(long_name, tip)
        self.assertIn("nested", tip.replace("\\", "/"))

    def test_drop_mixed_files(self):
        src = make_case(
            self.tmp / "mix",
            ("Show.S01E01.mkv", VIDEO),
            ("notes.txt", b"x"),
        )
        event = _Drop([src / "Show.S01E01.mkv", src / "notes.txt"])
        self.win.dropEvent(event)
        APP.processEvents()
        kinds = {i.kind for i in self.win.items}
        self.assertEqual(kinds, {"video", "other"})
        other = next(i for i in self.win.items if i.kind == "other")
        self.assertFalse(other.selected)

    def test_drop_folder(self):
        src = make_case(self.tmp / "dropdir", ("Show.S01E01.mkv", VIDEO))
        self.win.dropEvent(_Drop([src]))
        APP.processEvents()
        self.assertEqual(len(self.win.items), 1)

    def test_perf_100_and_format(self):
        folder = self.tmp / "p100"
        folder.mkdir()
        paths = []
        for i in range(100):
            p = folder / f"Bulk.S01E{(i % 20) + 1:02d}.{i:03d}.mkv"
            p.write_bytes(VIDEO)
            paths.append(p)
        orig = self.win.refresh
        self.win.refresh = lambda *a, **k: None
        t0 = time.perf_counter()
        self.win.add_paths(paths)
        add_s = time.perf_counter() - t0
        self.win.refresh = orig
        t1 = time.perf_counter()
        self.win.analyze()
        analyze_s = time.perf_counter() - t1
        t2 = time.perf_counter()
        self.win.refresh(reanalyze=False)
        refresh_s = time.perf_counter() - t2
        print(
            f"M6 GUI TIME n=100 add={add_s:.4f}s analyze={analyze_s:.4f}s "
            f"refresh={refresh_s:.4f}s"
        )
        self.assertEqual(self.win.table.rowCount(), 100)
        self.assertLess(add_s, 10.0)
        self.assertLess(analyze_s, 10.0)
        self.assertLess(refresh_s, 10.0)
        self.assertEqual(format_size_bytes(len(VIDEO)), f"{len(VIDEO)} B")


if __name__ == "__main__":
    unittest.main(verbosity=2)
