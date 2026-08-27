"""
M4: feliratvariáns célnevek, {EXT}/{KITERJ}, nem támogatott típus, ütközés.
"""
from pathlib import Path
import os
import sys
import shutil
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["SERIESRENAMER_DATA"] = tempfile.mkdtemp(prefix="sr_m4_data_")

from PySide6.QtWidgets import QApplication

from renamer_engine import (
    parse_item,
    render_template,
    disambiguate_subtitle_target_names,
)
from main import MainWindow

APP = QApplication.instance() or QApplication(sys.argv)

VIDEO = b"M4_TEST_VIDEO_0.6.1"
SUB = b"M4_TEST_SUB_0.6.1"
SERIES = "{CIM}.{SZEZON}{EPIZOD}"


def make_case(root, *files):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for rel, data in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return root


class TestM4Engine(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_m4_eng_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def parse_name(self, name, data=VIDEO):
        path = make_case(self.tmp, (name, data)) / name
        return parse_item(path)

    def test_hu_subtitle_keeps_plain_target_name(self):
        item = self.parse_name("Show.S01E01.hu.srt", SUB)
        self.assertEqual(item.lang, "hu")
        self.assertFalse(item.variant)
        out = render_template(SERIES, item, item.title)
        self.assertEqual(out, "Show.S01E01.srt")

    def test_isolated_hu_forced_keeps_compat_name(self):
        """L2.4 B stratégia: HU forced nem preferred plain, kap .hu.forced."""
        item = self.parse_name("Show.S01E01.hu.forced.srt", SUB)
        self.assertEqual(item.variant, "forced")
        out = render_template(SERIES, item, item.title)
        self.assertEqual(out, "Show.S01E01.hu.forced.srt")

    def test_hu_and_hu_forced_get_distinct_names(self):
        hu = self.parse_name("Show.S01E01.hu.srt", SUB)
        forced = self.parse_name("Show.S01E01.hu.forced.srt", SUB)
        hu.new_name = render_template(SERIES, hu, hu.title)
        forced.new_name = render_template(SERIES, forced, forced.title)
        self.assertEqual(hu.new_name, "Show.S01E01.srt")
        self.assertEqual(forced.new_name, "Show.S01E01.hu.forced.srt")
        self.assertNotEqual(hu.new_name, forced.new_name)
        disambiguate_subtitle_target_names([hu, forced])
        self.assertEqual(hu.new_name, "Show.S01E01.srt")
        self.assertEqual(forced.new_name, "Show.S01E01.hu.forced.srt")

    def test_ext_placeholder_does_not_double_extension(self):
        item = self.parse_name("Show.S01E01.mkv")
        out = render_template("{CIM}.{SZEZON}{EPIZOD}.{EXT}", item, item.title)
        self.assertEqual(out, "Show.S01E01.mkv")
        self.assertFalse(out.lower().endswith(".mkv.mkv"))

    def test_kiterj_placeholder_does_not_double_extension(self):
        item = self.parse_name("Show.S01E01.mkv")
        out = render_template("{CIM}.{SZEZON}{EPIZOD}.{KITERJ}", item, item.title)
        self.assertEqual(out, "Show.S01E01.mkv")
        self.assertEqual(out.count(".mkv"), 1)

    def test_default_template_still_appends_extension_once(self):
        item = self.parse_name("Show.S01E01.mkv")
        out = render_template(SERIES, item, item.title)
        self.assertEqual(out, "Show.S01E01.mkv")

    def test_unsupported_extension_is_not_subtitle(self):
        item = self.parse_name("Show.S01E01.txt", b"not-media")
        self.assertEqual(item.kind, "other")
        self.assertNotEqual(item.kind, "sub")
        self.assertNotEqual(item.kind, "video")


class TestM4Analyze(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_m4_gui_"))
        self.win = MainWindow()
        APP.processEvents()

    def tearDown(self):
        self.win.close()
        self.win.deleteLater()
        APP.processEvents()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def add(self, *paths):
        self.win.add_paths([Path(p) for p in paths])
        APP.processEvents()

    def by_name(self, fragment):
        return next(
            i for i in self.win.items
            if fragment.lower() in Path(i.path).name.lower()
        )

    def test_analyze_splits_hu_and_forced_targets(self):
        src = make_case(
            self.tmp,
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
            ("Show.S01E01.hu.forced.srt", SUB),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(
            src / "Show.S01E01.mkv",
            src / "Show.S01E01.hu.srt",
            src / "Show.S01E01.hu.forced.srt",
        )
        self.win.analyze()
        video = self.by_name("Show.S01E01.mkv")
        hu = self.by_name("Show.S01E01.hu.srt")
        forced = self.by_name("forced")
        self.assertEqual(video.new_name, "Show.S01E01.mkv")
        self.assertEqual(hu.new_name, "Show.S01E01.srt")
        self.assertEqual(forced.new_name, "Show.S01E01.hu.forced.srt")
        self.assertNotEqual(hu.new_name, forced.new_name)
        self.assertEqual(video.status, "OK")
        self.assertEqual(hu.status, "OK")
        self.assertEqual(forced.status, "OK")

    def test_unsupported_file_has_clear_status(self):
        src = make_case(
            self.tmp,
            ("Show.S01E01.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
            ("Show.S01E01.nfo", b"nfo"),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(
            src / "Show.S01E01.mkv",
            src / "Show.S01E01.hu.srt",
            src / "Show.S01E01.nfo",
        )
        self.win.analyze()
        extra = self.by_name(".nfo")
        video = self.by_name(".mkv")
        sub = self.by_name(".srt")
        self.assertEqual(extra.status, "Nem támogatott")
        self.assertFalse(extra.selected)
        self.assertFalse(extra.new_name)
        self.assertEqual(video.status, "OK")
        self.assertEqual(sub.status, "OK")

    def test_two_videos_same_target_are_conflicts(self):
        src = make_case(
            self.tmp,
            ("Show.S01E01.1080p.mkv", VIDEO),
            ("Show.S01E01.720p.mkv", VIDEO),
            ("Show.S01E01.hu.srt", SUB),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.win.output_mode = "Helyben átnevezés"
        if hasattr(self.win, "output_mode_combo"):
            self.win.output_mode_combo.setCurrentText("Helyben átnevezés")
        self.win.conflicts_cb.setChecked(True)
        self.add(
            src / "Show.S01E01.1080p.mkv",
            src / "Show.S01E01.720p.mkv",
            src / "Show.S01E01.hu.srt",
        )
        self.win.analyze()
        v1 = self.by_name("1080p")
        v2 = self.by_name("720p")
        self.assertEqual(v1.new_name, v2.new_name)
        self.assertEqual(v1.status, "Névütközés")
        self.assertEqual(v2.status, "Névütközés")

    def test_m11_complete_pair_not_poisoned(self):
        src = make_case(
            self.tmp,
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
        self.assertNotEqual(self.by_name("Other.Show").status, "OK")

    def test_m2_two_series_keep_own_titles(self):
        src = make_case(
            self.tmp,
            ("Invasion.S01E01.WEBRip.x264.mkv", VIDEO),
            ("Invasion.S01E01.WEBRip.x264-ION10.hun.srt", SUB),
            ("Murderbot.S01E01.480p.ATVP.WEB-DL.AAC2.0.H264-B9R.mkv", VIDEO),
            ("Murderbot.S01E01.FreeCommerce.ATVP.WEB-DL.hu.srt", SUB),
        )
        self.win.mode_combo.setCurrentText("Sorozat")
        self.add(
            src / "Invasion.S01E01.WEBRip.x264.mkv",
            src / "Invasion.S01E01.WEBRip.x264-ION10.hun.srt",
            src / "Murderbot.S01E01.480p.ATVP.WEB-DL.AAC2.0.H264-B9R.mkv",
            src / "Murderbot.S01E01.FreeCommerce.ATVP.WEB-DL.hu.srt",
        )
        self.win.analyze()
        self.assertEqual(self.by_name("Invasion.S01E01.WEBRip.x264.mkv").new_name, "Invasion.S01E01.mkv")
        self.assertEqual(self.by_name("ION10").new_name, "Invasion.S01E01.srt")
        self.assertEqual(self.by_name("Murderbot.S01E01.480p").new_name, "Murderbot.S01E01.mkv")
        self.assertEqual(self.by_name("FreeCommerce").new_name, "Murderbot.S01E01.srt")
        self.assertEqual(self.by_name("Invasion.S01E01.WEBRip.x264.mkv").status, "OK")
        self.assertEqual(self.by_name("Murderbot.S01E01.480p").status, "OK")


if __name__ == "__main__":
    unittest.main(verbosity=2)
