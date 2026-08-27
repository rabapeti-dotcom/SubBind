"""
R3.4: mappastruktúra-évad gyenge hint — csak ha a fájlnévben nincs SxxExx / NxN.
"""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from renamer_engine import (
    parse_item,
    parse_parent_folder_season,
    apply_item_target_names,
    NamingContext,
)

VIDEO = b"TEST_VIDEO_CONTENT_0.6.1"
SUB = b"TEST_SUBTITLE_CONTENT_0.6.1"
SERIES_CTX = NamingContext(
    mode="Sorozat",
    template="{CIM}.{SZEZON}{EPIZOD}",
    normalize=True,
)


def parse(path):
    return parse_item(Path(path))


class TestFolderSeasonPatterns(unittest.TestCase):
    def test_strong_folder_names(self):
        self.assertEqual(parse_parent_folder_season("Season 01"), 1)
        self.assertEqual(parse_parent_folder_season("Season 02"), 2)
        self.assertEqual(parse_parent_folder_season("Season 10"), 10)
        self.assertEqual(parse_parent_folder_season("Season 1"), 1)
        self.assertEqual(parse_parent_folder_season("S01"), 1)
        self.assertEqual(parse_parent_folder_season("S02"), 2)
        self.assertEqual(parse_parent_folder_season("S10"), 10)
        self.assertEqual(parse_parent_folder_season("s01"), 1)
        self.assertEqual(parse_parent_folder_season("season 01"), 1)

    def test_rejected_folder_names(self):
        self.assertIsNone(parse_parent_folder_season("01"))
        self.assertIsNone(parse_parent_folder_season("1"))
        self.assertIsNone(parse_parent_folder_season("Season"))
        self.assertIsNone(parse_parent_folder_season("Season 01 Complete"))
        self.assertIsNone(parse_parent_folder_season("Downloads"))
        self.assertIsNone(parse_parent_folder_season("S01E01"))
        self.assertIsNone(parse_parent_folder_season("Évad 1"))
        self.assertIsNone(parse_parent_folder_season(""))


class TestFolderSeasonHint(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_r34_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _file(self, *parts, data=VIDEO):
        p = self.tmp.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return p

    def test_season_01_plus_e01(self):
        p = self._file("Season 01", "Show.E01.mkv")
        item = parse(p)
        self.assertEqual((item.season, item.episode), (1, 1))
        self.assertEqual(item.confidence, "high")
        self.assertEqual(item.title, "Show")

    def test_s02_plus_e03(self):
        p = self._file("S02", "Show.E03.mkv")
        item = parse(p)
        self.assertEqual((item.season, item.episode), (2, 3))
        self.assertEqual(item.confidence, "high")

    def test_season_10_plus_e10(self):
        p = self._file("Season 10", "Show.E10.mkv")
        item = parse(p)
        self.assertEqual((item.season, item.episode), (10, 10))

    def test_s10_plus_e01_subtitle(self):
        p = self._file("S10", "Show.E01.hu.srt", data=SUB)
        item = parse(p)
        self.assertEqual((item.season, item.episode), (10, 1))
        self.assertEqual(item.kind, "sub")

    def test_filename_sxxexx_wins_over_folder(self):
        p = self._file("Season 01", "Show.S02E01.mkv")
        item = parse(p)
        self.assertEqual((item.season, item.episode), (2, 1))
        self.assertEqual(item.confidence, "high")

    def test_filename_nxn_wins_over_folder(self):
        p = self._file("Season 05", "Show.1x02.mkv")
        item = parse(p)
        self.assertEqual((item.season, item.episode), (1, 2))

    def test_e01_without_season_folder_stays_unknown(self):
        p = self._file("Downloads", "Show.E01.mkv")
        item = parse(p)
        self.assertIsNone(item.season)
        self.assertIsNone(item.episode)
        self.assertNotEqual(item.confidence, "high")

    def test_season_folder_without_episode_stays_unknown(self):
        p = self._file("Season 01", "Show.mkv")
        item = parse(p)
        self.assertIsNone(item.season)
        self.assertIsNone(item.episode)
        self.assertNotEqual(item.confidence, "high")

    def test_grandparent_season_is_ignored(self):
        p = self._file("Season 01", "Extra", "Show.E01.mkv")
        item = parse(p)
        self.assertIsNone(item.season)
        self.assertIsNone(item.episode)
        self.assertNotEqual(item.confidence, "high")

    def test_ambiguous_folder_complete_ignored(self):
        p = self._file("Season 01 Complete", "Show.E01.mkv")
        item = parse(p)
        self.assertIsNone(item.season)
        self.assertIsNone(item.episode)

    def test_apply_names_from_folder_hint(self):
        p = self._file("Season 01", "Show.E01.mkv")
        items = [parse(p)]
        apply_item_target_names(items, SERIES_CTX)
        self.assertEqual(items[0].status, "OK")
        self.assertEqual(items[0].new_name, "Show.S01E01.mkv")

    def test_apply_names_filename_not_overridden(self):
        p = self._file("Season 01", "Show.S02E04.mkv")
        items = [parse(p)]
        apply_item_target_names(items, SERIES_CTX)
        self.assertEqual(items[0].new_name, "Show.S02E04.mkv")


if __name__ == "__main__":
    unittest.main(verbosity=2)
