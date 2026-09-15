"""GUI: részlegesen sikeres előzmény failed file/reason megjelenítése."""
from pathlib import Path
import copy
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
TEST_DATA_ROOT = Path(tempfile.mkdtemp(prefix="sr_gui_hist_failed_"))
os.environ["SERIESRENAMER_DATA"] = str(TEST_DATA_ROOT)

from PySide6.QtWidgets import QApplication, QMessageBox

try:
    from main import MainWindow
except Exception as exc:
    raise RuntimeError(f"MainWindow nem tölthető be: {SRC / 'main.py'}") from exc

from i18n import t


APP = QApplication.instance() or QApplication(sys.argv)

FAILED_FILE = str(Path("C:/src/Show.S01E02.mkv"))
FAILED_REASON = "A célfájl már létezik – a program nem írta felül"


def partial_record():
    return {
        "time": "2026-04-01T12:00:00",
        "operation": "Másolás és átnevezés",
        "title": "Show",
        "destination": str(Path("C:/out")),
        "changes": [
            {
                "old": str(Path("C:/src/Show.S01E01.mkv")),
                "new": str(Path("C:/out/Show.S01E01.mkv")),
                "action": "copy",
                "size": 10,
                "mtime_ns": 1,
            },
            {
                "old": str(Path("C:/src/Show.S01E01.hu.srt")),
                "new": str(Path("C:/out/Show.S01E01.srt")),
                "action": "copy",
                "size": 4,
                "mtime_ns": 1,
            },
        ],
        "failed": [
            {"file": FAILED_FILE, "reason": FAILED_REASON},
        ],
        "status": "Részben elkészült",
    }


def success_record():
    return {
        "time": "2026-04-01T12:01:00",
        "operation": "Másolás és átnevezés",
        "title": "Show",
        "destination": str(Path("C:/out")),
        "changes": [
            {
                "old": str(Path("C:/src/Show.S01E01.mkv")),
                "new": str(Path("C:/out/Show.S01E01.mkv")),
                "action": "copy",
                "size": 10,
                "mtime_ns": 1,
            },
        ],
        "failed": [],
        "status": "Sikeres",
    }


class TestGuiHistoryFailed(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        if ORIGINAL_DATA is None:
            os.environ.pop("SERIESRENAMER_DATA", None)
        else:
            os.environ["SERIESRENAMER_DATA"] = ORIGINAL_DATA
        shutil.rmtree(TEST_DATA_ROOT, ignore_errors=True)

    def setUp(self):
        self.message_box_methods = {
            "question": QMessageBox.question,
            "information": QMessageBox.information,
            "warning": QMessageBox.warning,
            "critical": QMessageBox.critical,
        }
        self.seen_info = []

        def capture_information(*args, **kwargs):
            title = args[1] if len(args) > 1 else kwargs.get("title", "")
            text = args[2] if len(args) > 2 else kwargs.get("text", "")
            self.seen_info.append((title, text))
            return QMessageBox.StandardButton.Ok

        QMessageBox.information = staticmethod(capture_information)
        self.win = MainWindow()
        self.win.show_welcome = False
        self.win.history = []
        self.win.history_selected_keys.clear()
        self.win.save_history()
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

    def _show_history(self, records):
        self.win.history = records
        self.win.history_selected_keys.clear()
        self.win.update_history_view()
        APP.processEvents()

    def test_partial_record_shows_summary_and_failed_details(self):
        record = partial_record()
        snapshot = copy.deepcopy(record)
        self._show_history([record])

        self.assertTrue(hasattr(self.win, "hist_failed_btn"))
        files_cell = self.win.hist.item(0, 5)
        self.assertIsNotNone(files_cell)
        self.assertIn("2 kész / 1 kimaradt", files_cell.text())
        self.assertIn("Részben elkészült", files_cell.text())
        self.assertEqual(files_cell.toolTip(), t("hist.failed_tip"))

        self.win.history_select_all()
        APP.processEvents()
        self.win.hist_failed_btn.click()
        APP.processEvents()

        self.assertEqual(len(self.seen_info), 1)
        title, text = self.seen_info[0]
        self.assertEqual(title, t("hist.failed_title"))
        self.assertIn(FAILED_FILE, text)
        self.assertIn(FAILED_REASON, text)
        self.assertEqual(self.win.history[0], snapshot)
        self.assertEqual(self.win.history[0]["status"], "Részben elkészült")
        self.assertEqual(len(self.win.history[0]["changes"]), 2)
        self.assertEqual(len(self.win.history[0]["failed"]), 1)

    def test_successful_record_has_no_failed_list(self):
        self._show_history([success_record()])
        files_cell = self.win.hist.item(0, 5)
        self.assertEqual(files_cell.text(), "1 kész — Sikeres")
        self.assertEqual(files_cell.toolTip(), "")

        self.win.history_select_all()
        APP.processEvents()
        self.win.show_selected_history_failures()
        APP.processEvents()

        self.assertEqual(len(self.seen_info), 1)
        title, text = self.seen_info[0]
        self.assertEqual(title, t("hist.failed_title"))
        self.assertEqual(text, t("hist.failed_none"))

    def test_details_require_exactly_one_selection(self):
        self._show_history([partial_record(), success_record()])
        self.win.show_selected_history_failures()
        APP.processEvents()
        self.assertEqual(self.seen_info[-1][1], t("hist.failed_need_one"))

        self.win.history_select_all()
        APP.processEvents()
        self.win.show_selected_history_failures()
        APP.processEvents()
        self.assertEqual(self.seen_info[-1][1], t("hist.failed_need_one"))
        self.assertEqual(len(self.win.history), 2)
        self.assertEqual(self.win.history[0]["status"], "Részben elkészült")
        self.assertEqual(self.win.history[1]["status"], "Sikeres")


if __name__ == "__main__":
    unittest.main(verbosity=2)
