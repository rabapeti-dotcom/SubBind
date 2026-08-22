"""
F4.1: apply_pair_group_status — group kulcs nyelvfüggetlen; sima HU szabály változatlan.
"""
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

from renamer_engine import parse_item, apply_pair_group_status

VIDEO = b"F41_TEST_VIDEO"
SUB = b"F41_TEST_SUB"


def make_case(root, *names):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in names:
        p = root / name
        p.write_bytes(VIDEO if p.suffix.lower() == ".mkv" else SUB)
        paths.append(p)
    return paths


def parsed(paths):
    items = [parse_item(p) for p in paths]
    for item in items:
        if item.kind in ("video", "sub"):
            item.status = "OK"
            item.note = ""
    return items


def by_name(items, fragment):
    return next(i for i in items if fragment.lower() in Path(i.path).name.lower())


class TestF41PairGroupStatus(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_f41_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_subtitle_languages_share_one_group(self):
        items = parsed(make_case(
            self.tmp,
            "Murderbot.S01E01.mkv",
            "Murderbot.S01E01.hu.srt",
            "Murderbot.S01E01.en.srt",
            "Murderbot.S01E01.de.srt",
        ))
        groups = {i.group for i in items}
        self.assertEqual(len(groups), 1)
        self.assertTrue(list(groups)[0].startswith("murderbot|S01E01"))
        self.assertEqual(by_name(items, ".hu.srt").lang, "hu")
        self.assertEqual(by_name(items, ".en.srt").lang, "en")
        self.assertEqual(by_name(items, ".de.srt").lang, "de")

    def test_1_video_plus_hu_is_complete_pair(self):
        items = parsed(make_case(
            self.tmp,
            "Show.S01E01.mkv",
            "Show.S01E01.hu.srt",
        ))
        apply_pair_group_status(items)
        self.assertEqual(by_name(items, ".mkv").status, "OK")
        self.assertEqual(by_name(items, ".hu.srt").status, "OK")
        self.assertNotEqual(by_name(items, ".mkv").note, "Nincs sima HU felirat")

    def test_2_video_plus_en_is_complete_pair(self):
        items = parsed(make_case(
            self.tmp,
            "Show.S01E01.mkv",
            "Show.S01E01.en.srt",
        ))
        apply_pair_group_status(items)
        video = by_name(items, ".mkv")
        sub = by_name(items, ".en.srt")
        self.assertEqual(video.status, "OK")
        self.assertEqual(sub.status, "OK")
        self.assertNotEqual(video.status, "Nem egyező pár")
        self.assertNotEqual(sub.status, "Videó nélkül")
        self.assertEqual(video.note, "Nincs sima HU felirat")

    def test_3_video_hu_and_en_same_complete_group(self):
        items = parsed(make_case(
            self.tmp,
            "Show.S01E01.mkv",
            "Show.S01E01.hu.srt",
            "Show.S01E01.en.srt",
        ))
        apply_pair_group_status(items)
        for item in items:
            self.assertEqual(item.status, "OK")
            self.assertNotEqual(item.status, "Nem egyező pár")
        self.assertNotEqual(by_name(items, ".mkv").note, "Nincs sima HU felirat")

    def test_4_video_hu_de_fr_same_complete_group(self):
        items = parsed(make_case(
            self.tmp,
            "Show.S01E01.mkv",
            "Show.S01E01.hu.srt",
            "Show.S01E01.de.srt",
            "Show.S01E01.fr.srt",
        ))
        apply_pair_group_status(items)
        for item in items:
            self.assertEqual(item.status, "OK")
            self.assertNotEqual(item.status, "Nem egyező pár")

    def test_5_two_languages_without_video_are_not_mismatch(self):
        items = parsed(make_case(
            self.tmp,
            "Show.S01E01.en.srt",
            "Show.S01E01.de.srt",
        ))
        apply_pair_group_status(items)
        for item in items:
            self.assertEqual(item.status, "Videó nélkül")
            self.assertNotEqual(item.status, "Nem egyező pár")

    def test_6_different_titles_same_episode_still_mismatch(self):
        items = parsed(make_case(
            self.tmp,
            "Show.S01E01.mkv",
            "Other.S01E01.en.srt",
        ))
        apply_pair_group_status(items)
        self.assertEqual(by_name(items, "Show.S01E01.mkv").status, "Nem egyező pár")
        self.assertEqual(by_name(items, "Other.S01E01.en.srt").status, "Nem egyező pár")

    def test_7_multiple_plain_hu_unchanged(self):
        items = parsed(make_case(
            self.tmp,
            "Show.S01E01.mkv",
            "Show.S01E01.hu.srt",
            "Show.S01E01.hun.srt",
        ))
        apply_pair_group_status(items)
        for item in items:
            self.assertEqual(item.status, "Ellenőrzést igényel")
            self.assertEqual(item.note, "Több sima HU felirat ugyanahhoz a címhez")

    def test_8_hu_forced_variant_not_second_plain_hu(self):
        items = parsed(make_case(
            self.tmp,
            "Show.S01E01.mkv",
            "Show.S01E01.hu.srt",
            "Show.S01E01.hu.forced.srt",
        ))
        apply_pair_group_status(items)
        video = by_name(items, ".mkv")
        plain = by_name(items, "Show.S01E01.hu.srt")
        forced = by_name(items, "forced")
        self.assertEqual(forced.variant, "forced")
        self.assertEqual(video.status, "OK")
        self.assertEqual(plain.status, "OK")
        self.assertEqual(forced.status, "OK")
        self.assertNotEqual(video.note, "Több sima HU felirat ugyanahhoz a címhez")


if __name__ == "__main__":
    unittest.main(verbosity=2)
