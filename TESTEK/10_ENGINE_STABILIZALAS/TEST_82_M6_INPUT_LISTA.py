"""
M6: fájl/mappa hozzáadás, duplikáció, méret, DND, nagy lista idők, M2/M1.1/M4/M5 regresszió.
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

from main import MainWindow, format_size_bytes, file_identity_key
from renamer_engine import parse_item

APP = QApplication.instance() or QApplication(sys.argv)

VIDEO = b"M6_TEST_VIDEO_0.6.1"
SUB = b"M6_TEST_SUB_0.6.1"


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


class TestM6InputLista(unittest.TestCase):
    def setUp(self):
        self.original_data = os.environ.get("SERIESRENAMER_DATA")
        self.data_dir = Path(tempfile.mkdtemp(prefix="sr_m6_data_"))
        self.out_dir = Path(tempfile.mkdtemp(prefix="sr_m6_out_"))
        os.environ["SERIESRENAMER_DATA"] = str(self.data_dir)
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_m6_"))
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
        self.win.output_dir = str(self.out_dir)
        self.win.show()
        APP.processEvents()

    def tearDown(self):
        for name, method in self.message_box_methods.items():
            setattr(QMessageBox, name, method)
        self.win.close()
        self.win.deleteLater()
        APP.processEvents()
        if self.original_data is None:
            os.environ.pop("SERIESRENAMER_DATA", None)
        else:
            os.environ["SERIESRENAMER_DATA"] = self.original_data
        shutil.rmtree(self.tmp, ignore_errors=True)
        shutil.rmtree(self.data_dir, ignore_errors=True)
        shutil.rmtree(self.out_dir, ignore_errors=True)

    def add(self, *paths):
        self.win.add_paths([Path(p) for p in paths])
        APP.processEvents()

    def by_name(self, fragment):
        return next(
            i for i in self.win.items
            if fragment.lower() in Path(i.path).name.lower()
        )

    def test_01_add_one_file(self):
        src = make_case(self.tmp / "one", ("Show.S01E01.mkv", VIDEO))
        p = src / "Show.S01E01.mkv"
        self.add(p)
        self.assertEqual(len(self.win.items), 1)
        self.assertEqual(Path(self.win.items[0].path).name, "Show.S01E01.mkv")

    def test_02_add_multiple_files(self):
        src = make_case(
            self.tmp / "multi",
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
        )
        self.add(src / "Show.S01E01.mkv", src / "Show.S01E01.hu.srt")
        self.assertEqual(len(self.win.items), 2)

    def test_03_add_folder(self):
        src = make_case(
            self.tmp / "folder",
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
            ("readme.txt", b"x"),
        )
        self.win.subdirs_cb.setChecked(False)
        self.win._ingest_user_paths([src])
        APP.processEvents()
        names = {Path(i.path).name for i in self.win.items}
        self.assertEqual(names, {"Show.S01E01.mkv", "Show.S01E01.hu.srt"})
        self.assertNotIn("readme.txt", names)

    def test_04_add_multiple_folders(self):
        a = make_case(self.tmp / "a", ("Show.S01E01.mkv", VIDEO))
        b = make_case(self.tmp / "b", ("Show.S01E02.mkv", VIDEO))
        self.win._ingest_user_paths([a, b])
        APP.processEvents()
        self.assertEqual(len(self.win.items), 2)

    def test_05_subdirectory(self):
        src = make_case(self.tmp / "root", ("root.mkv", VIDEO))
        nested = src / "season2"
        nested.mkdir()
        (nested / "Show.S02E01.mkv").write_bytes(VIDEO)
        self.win.subdirs_cb.setChecked(True)
        self.win._ingest_user_paths([src])
        APP.processEvents()
        self.assertEqual(len(self.win.items), 2)
        self.assertTrue(any(Path(i.path).parent == nested for i in self.win.items))

    def test_06_duplicate_file(self):
        src = make_case(self.tmp / "dupf", ("Show.S01E01.mkv", VIDEO))
        p = src / "Show.S01E01.mkv"
        self.add(p, p)
        self.assertEqual(len(self.win.items), 1)
        self.add(p)
        self.assertEqual(len(self.win.items), 1)

    def test_07_duplicate_folder(self):
        src = make_case(self.tmp / "dupd", ("Show.S01E01.mkv", VIDEO))
        self.win._ingest_user_paths([src, src])
        APP.processEvents()
        self.assertEqual(len(self.win.items), 1)
        self.win._ingest_user_paths([src])
        APP.processEvents()
        self.assertEqual(len(self.win.items), 1)

    def test_08_unsupported_file(self):
        src = make_case(self.tmp / "other", ("notes.txt", b"hello"))
        self.add(src / "notes.txt")
        item = self.win.items[0]
        self.assertEqual(item.kind, "other")
        self.assertEqual(item.status, "Nem támogatott")
        self.assertFalse(item.selected)

    def test_09_mixed_supported_unsupported(self):
        src = make_case(
            self.tmp / "mix",
            ("Show.S01E01.mkv", VIDEO),
            ("notes.txt", b"hello"),
        )
        self.add(src / "Show.S01E01.mkv", src / "notes.txt")
        self.assertEqual(len(self.win.items), 2)
        video = self.by_name(".mkv")
        other = self.by_name(".txt")
        self.assertEqual(video.kind, "video")
        self.assertEqual(other.kind, "other")
        self.assertFalse(other.selected)
        self.assertNotEqual(other.status, "OK")

    def test_10_drag_drop_file(self):
        src = make_case(self.tmp / "dndf", ("Show.S01E01.mkv", VIDEO))
        event = _Drop([src / "Show.S01E01.mkv"])
        self.win.dragEnterEvent(event)
        self.win.dropEvent(event)
        APP.processEvents()
        self.assertTrue(event.accepted)
        self.assertEqual(len(self.win.items), 1)

    def test_11_drag_drop_folder(self):
        src = make_case(self.tmp / "dndd", ("Show.S01E01.mkv", VIDEO))
        event = _Drop([src])
        self.win.dropEvent(event)
        APP.processEvents()
        self.assertEqual(len(self.win.items), 1)

    def test_12_file_size(self):
        payload = b"x" * 2048
        src = make_case(self.tmp / "size", ("Show.S01E01.mkv", payload))
        p = src / "Show.S01E01.mkv"
        self.add(p)
        item = self.win.items[0]
        self.assertEqual(item.size_bytes, 2048)
        self.assertEqual(format_size_bytes(item.size_bytes), "2.0 KB")
        first = item.size_bytes
        self.win.refresh()
        self.assertEqual(item.size_bytes, first)
        self.assertEqual(format_size_bytes(500), "500 B")
        self.assertTrue(format_size_bytes(1024 ** 3).endswith("GB"))

    def test_13_long_filename(self):
        long_name = ("Very.Long.Show.Name." * 8) + "S01E01.mkv"
        src = make_case(self.tmp / "long", (long_name, VIDEO))
        self.add(src / long_name)
        self.assertEqual(Path(self.win.items[0].path).name, long_name)
        cell = self.win.table.item(0, 1)
        self.assertIsNotNone(cell)
        self.assertIn(long_name, cell.toolTip())

    def test_14_source_path_available(self):
        src = make_case(self.tmp / "srcpath", ("Show.S01E01.mkv", VIDEO))
        p = src / "Show.S01E01.mkv"
        self.add(p)
        item = self.win.items[0]
        source = str(self.win._source_path(item))
        self.assertEqual(file_identity_key(source), file_identity_key(p))
        cell = self.win.table.item(0, 1)
        self.assertIn(p.name, cell.toolTip())
        self.assertTrue(
            str(p) in cell.toolTip() or str(p.resolve()) in cell.toolTip()
        )
        self.win._table_double_clicked(0, 1)
        self.assertIn(str(p.name), self.win.status_label.text())

    def _make_n_videos(self, n, folder):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        paths = []
        for i in range(n):
            season = (i // 20) + 1
            episode = (i % 20) + 1
            name = f"Bulk.S{season:02d}E{episode:02d}.{i:04d}.mkv"
            p = folder / name
            p.write_bytes(VIDEO)
            paths.append(p)
        return paths

    def _measure(self, n):
        paths = self._make_n_videos(n, self.tmp / f"perf_{n}")
        orig_refresh = self.win.refresh
        self.win.refresh = lambda *a, **k: None
        t0 = time.perf_counter()
        self.win.add_paths(paths)
        add_s = time.perf_counter() - t0
        self.win.refresh = orig_refresh
        t1 = time.perf_counter()
        self.win.analyze()
        analyze_s = time.perf_counter() - t1
        t2 = time.perf_counter()
        self.win.refresh(reanalyze=False)
        refresh_s = time.perf_counter() - t2
        APP.processEvents()
        print(
            f"M6 TIME n={n} add={add_s:.4f}s analyze={analyze_s:.4f}s "
            f"refresh={refresh_s:.4f}s"
        )
        self.assertEqual(len(self.win.items), n)
        self.assertLess(add_s, 10.0)
        self.assertLess(analyze_s, 10.0)
        self.assertLess(refresh_s, 10.0)
        return add_s, analyze_s, refresh_s

    def test_15_list_100_files(self):
        self._measure(100)

    def test_16_list_500_files(self):
        self._measure(500)

    def test_17_m5_selection_preserved_on_add(self):
        src = make_case(
            self.tmp / "m5",
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
            ("Show.S01E02.mkv", VIDEO),
        )
        self.add(src / "Show.S01E01.mkv", src / "Show.S01E01.hu.srt")
        v1 = self.by_name("S01E01.mkv")
        v1.selected = False
        self.win.refresh(reanalyze=False)
        self.add(src / "Show.S01E02.mkv")
        v1_again = self.by_name("S01E01.mkv")
        self.assertFalse(v1_again.selected)
        self.assertEqual(len(self.win.items), 3)

    def test_18_m2_regression(self):
        src = make_case(
            self.tmp / "m2",
            ("Invasion.S01E01.WEBRip.x264-ION10.hu.srt", SUB),
            ("Murderbot.S01E01.480p.WEB-DL.mkv", VIDEO),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(
            src / "Invasion.S01E01.WEBRip.x264-ION10.hu.srt",
            src / "Murderbot.S01E01.480p.WEB-DL.mkv",
        )
        self.win.analyze()
        self.assertEqual(self.by_name("Murderbot").new_name, "Murderbot.S01E01.mkv")
        self.assertNotEqual(self.by_name("Murderbot").new_name, "Invasion.ION10.hu.S01E01.mkv")

    def test_19_m1_1_regression(self):
        src = make_case(
            self.tmp / "m11",
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
            ("Other.Show.S01E01.hu.srt", SUB),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(
            src / "Show.S01E01.mkv",
            src / "Show.S01E01.hu.srt",
            src / "Other.Show.S01E01.hu.srt",
        )
        self.win.analyze()
        self.assertEqual(self.by_name("Show.S01E01.mkv").status, "OK")
        self.assertEqual(self.by_name("Show.S01E01.hu.srt").status, "OK")
        self.assertNotEqual(self.by_name("Show.S01E01.mkv").status, "Nem egyező pár")

    def test_20_m4_regression(self):
        src = make_case(self.tmp / "m4", ("Show.S01E01.txt", b"not-media"))
        item = parse_item(src / "Show.S01E01.txt")
        self.assertEqual(item.kind, "other")
        self.add(src / "Show.S01E01.txt")
        gui = self.win.items[0]
        self.assertEqual(gui.kind, "other")
        self.assertFalse(gui.selected)
        self.assertEqual(gui.status, "Nem támogatott")


if __name__ == "__main__":
    unittest.main(verbosity=2)
