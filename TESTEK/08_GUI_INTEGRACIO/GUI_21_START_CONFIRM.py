"""R3.2: átnevezés előtti megerősítő ablak."""
from pathlib import Path
import os
import sys
import shutil
import tempfile
import unittest
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialog

from main import MainWindow, StartConfirmDialog, format_confirm_preview_text
from i18n import t

APP = QApplication.instance() or QApplication(sys.argv)


class TestStartConfirmDialog(unittest.TestCase):
    def setUp(self):
        self.original_data = os.environ.get("SERIESRENAMER_DATA")
        self.data_dir = Path(tempfile.mkdtemp(prefix="sr_gui21_data_"))
        os.environ["SERIESRENAMER_DATA"] = str(self.data_dir)
        self.win = MainWindow()
        self.win.show_welcome = False

    def tearDown(self):
        self.win.close()
        self.win.deleteLater()
        APP.processEvents()
        if self.original_data is None:
            os.environ.pop("SERIESRENAMER_DATA", None)
        else:
            os.environ["SERIESRENAMER_DATA"] = self.original_data
        shutil.rmtree(self.data_dir, ignore_errors=True)

    def test_copy_dialog_shows_counts_and_keep_originals(self):
        video = SimpleNamespace(kind="video")
        sub = SimpleNamespace(kind="sub")
        changes = [
            (video, Path("Show.S01E01.mkv"), Path("Show.S01E01.mkv")),
            (sub, Path("Show.S01E01.hu.srt"), Path("Show.S01E01.srt")),
        ]
        dialog = StartConfirmDialog(self.win, changes, True, Path(r"D:\Sorozatok"))
        self.assertEqual(dialog.counts_label.text().splitlines()[0], t("confirm.files", n=2))
        self.assertIn("1", dialog.counts_label.text())
        self.assertEqual(dialog.note_label.text(), t("confirm.keep"))
        text = dialog.preview.toPlainText()
        self.assertIn("Show.S01E01.mkv", text)
        self.assertIn("→", text)
        self.assertIn(t("confirm.copy_same", name="Show.S01E01.mkv"), text)
        self.assertIn(t("confirm.rename_pair", old="Show.S01E01.hu.srt", new="Show.S01E01.srt"), text)
        dialog.close()

    def test_copy_same_name_is_not_shown_as_identity_rename(self):
        item = SimpleNamespace(kind="video")
        text = format_confirm_preview_text(
            [(item, Path("Show.S01E01.mkv"), Path("D:/out/Show.S01E01.mkv"))],
            True,
        )
        self.assertEqual(text, t("confirm.copy_same", name="Show.S01E01.mkv"))
        self.assertNotIn("Show.S01E01.mkv  →  Show.S01E01.mkv", text)

    def test_rename_pair_uses_multiline_arrow(self):
        item = SimpleNamespace(kind="video")
        text = format_confirm_preview_text(
            [(item, Path("Show.S01E01.1080p.mkv"), Path("Show.S01E01.mkv"))],
            False,
        )
        self.assertEqual(
            text,
            t("confirm.rename_pair", old="Show.S01E01.1080p.mkv", new="Show.S01E01.mkv"),
        )

    def test_inplace_dialog_warns_that_names_change(self):
        item = SimpleNamespace(kind="video")
        dialog = StartConfirmDialog(
            self.win, [(item, Path("a.mkv"), Path("b.mkv"))], False, None
        )
        self.assertEqual(dialog.note_label.text(), t("confirm.change"))
        dialog.reject()
        self.assertEqual(dialog.result(), int(QDialog.DialogCode.Rejected))
        dialog.close()

    def test_ok_item_hides_plain_hu_note_in_tooltip(self):
        item = SimpleNamespace(
            kind="video",
            status="OK",
            title="Show",
            season=1,
            episode=1,
            note="Nincs sima HU felirat",
            size_bytes=10,
            path="Show.S01E01.mkv",
            copy_status="Várakozik",
        )
        self.assertEqual(self.win._visible_note(item), "")
        tip = self.win._row_tooltip(item, "Show.S01E01.mkv", r"C:\Show.S01E01.mkv")
        self.assertNotIn("Nincs sima HU felirat", tip)

    def test_review_item_keeps_note_in_tooltip(self):
        item = SimpleNamespace(
            kind="video",
            status="Felirat nélkül",
            title="Show",
            season=1,
            episode=2,
            note="Nincs ugyanahhoz a címhez tartozó videó + felirat pár",
            size_bytes=10,
            path="Show.S01E02.mkv",
            copy_status="Várakozik",
        )
        self.assertIn(
            "Nincs ugyanahhoz a címhez tartozó videó + felirat pár",
            self.win._visible_note(item),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
