"""
F4.2: apply_item_target_names — {CIM} parse-olt címből; nyelv nem keveri a sorozatokat.
"""
from pathlib import Path
import sys
import shutil
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from renamer_engine import (
    parse_item,
    render_template,
    apply_item_target_names,
    apply_pair_group_status,
    NamingContext,
)

VIDEO = b"F42_TEST_VIDEO"
SUB = b"F42_TEST_SUB"
SERIES = "{CIM}.{SZEZON}{EPIZOD}"
SERIES_CTX = NamingContext(mode="Sorozat", template=SERIES, normalize=True)


def make_case(root, *names):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in names:
        p = root / name
        p.write_bytes(VIDEO if p.suffix.lower() == ".mkv" else SUB)
        paths.append(p)
    return [parse_item(p) for p in paths]


def by_name(items, fragment):
    return next(i for i in items if fragment.lower() in Path(i.path).name.lower())


class TestF42NamingCycle(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_f42_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_same_episode_different_series_keep_own_cim(self):
        items = make_case(
            self.tmp,
            "Invasion.S01E01.mkv",
            "Invasion.S01E01.hu.srt",
            "Murderbot.S01E01.mkv",
            "Murderbot.S01E01.en.srt",
        )
        apply_item_target_names(items, SERIES_CTX)
        self.assertEqual(by_name(items, "Invasion.S01E01.mkv").new_name, "Invasion.S01E01.mkv")
        self.assertEqual(by_name(items, "Invasion.S01E01.hu.srt").new_name, "Invasion.S01E01.srt")
        self.assertEqual(by_name(items, "Murderbot.S01E01.mkv").new_name, "Murderbot.S01E01.mkv")
        self.assertEqual(by_name(items, "Murderbot.S01E01.en.srt").new_name, "Murderbot.S01E01.en.srt")
        inv_g = by_name(items, "Invasion.S01E01.mkv").group
        mur_g = by_name(items, "Murderbot.S01E01.mkv").group
        self.assertNotEqual(inv_g, mur_g)
        self.assertTrue(inv_g.startswith("invasion|S01E01"))
        self.assertTrue(mur_g.startswith("murderbot|S01E01"))

    def test_subtitle_language_does_not_change_video_cim(self):
        items = make_case(
            self.tmp,
            "Show.S01E01.mkv",
            "Show.S01E01.es.srt",
        )
        apply_item_target_names(items, SERIES_CTX)
        self.assertEqual(by_name(items, ".mkv").new_name, "Show.S01E01.mkv")
        self.assertEqual(by_name(items, ".es.srt").new_name, "Show.S01E01.es.srt")
        self.assertEqual(by_name(items, ".mkv").group, by_name(items, ".es.srt").group)

    def test_film_each_recognized_language_is_valid_pair_name(self):
        ctx = NamingContext(mode="Film", template="{CIM}", normalize=True)
        expected = {
            "Film.es.srt": "Film.es.srt",
            "Film.en.srt": "Film.en.srt",
            "Film.de.srt": "Film.de.srt",
            "Film.fr.srt": "Film.fr.srt",
            "Film.hu.srt": "Film.srt",
        }
        for name, want in expected.items():
            subdir = self.tmp / name.replace(".", "_")
            items = make_case(subdir, "Film.mkv", name)
            apply_item_target_names(items, ctx)
            self.assertEqual(by_name(items, "Film.mkv").new_name, "Film.mkv", name)
            self.assertEqual(by_name(items, name).new_name, want, name)
            self.assertEqual(by_name(items, "Film.mkv").group, by_name(items, name).group)

    def test_manual_title_overrides_cim_but_not_parsed_group(self):
        items = make_case(
            self.tmp,
            "Invasion.S01E01.mkv",
            "Murderbot.S01E01.mkv",
        )
        groups_before = {Path(i.path).name: i.group for i in items}
        apply_item_target_names(
            items,
            NamingContext(
                mode="Sorozat",
                template=SERIES,
                title_manual=True,
                global_title="Acme",
            ),
        )
        self.assertEqual(by_name(items, "Invasion").new_name, "Acme.S01E01.mkv")
        self.assertEqual(by_name(items, "Murderbot").new_name, "Acme.S01E01.mkv")
        self.assertEqual(by_name(items, "Invasion").group, groups_before["Invasion.S01E01.mkv"])
        self.assertEqual(by_name(items, "Murderbot").group, groups_before["Murderbot.S01E01.mkv"])
        self.assertNotEqual(
            by_name(items, "Invasion").group,
            by_name(items, "Murderbot").group,
        )

    def test_mixed_mode_ignores_global_title(self):
        items = make_case(
            self.tmp,
            "Invasion.S01E01.mkv",
            "Murderbot.S01E01.mkv",
        )
        apply_item_target_names(
            items,
            NamingContext(
                mode="Automatikus / Vegyes",
                template=SERIES,
                title_manual=True,
                global_title="Acme",
            ),
        )
        self.assertEqual(by_name(items, "Invasion").new_name, "Invasion.S01E01.mkv")
        self.assertEqual(by_name(items, "Murderbot").new_name, "Murderbot.S01E01.mkv")

    def test_nyelv_placeholder_uses_any_lang_equally(self):
        template = "{CIM}.{SZEZON}{EPIZOD}.{NYELV}"
        for name, lang, want in (
            ("Show.S01E01.hu.srt", "hu", "Show.S01E01.hu.srt"),
            ("Show.S01E01.en.srt", "en", "Show.S01E01.en.srt"),
            ("Show.S01E01.de.srt", "de", "Show.S01E01.de.srt"),
        ):
            item = make_case(self.tmp / lang, name)[0]
            self.assertEqual(item.lang, lang)
            self.assertEqual(render_template(template, item, item.title), want)

    def test_unsupported_kind_cleared_before_pairing(self):
        items = make_case(self.tmp, "Show.S01E01.mkv", "Show.S01E01.hu.srt")
        nfo = self.tmp / "note.nfo"
        nfo.write_bytes(b"nfo")
        extra = parse_item(nfo)
        items.append(extra)
        apply_item_target_names(items, SERIES_CTX)
        self.assertEqual(extra.status, "Nem támogatott")
        self.assertFalse(extra.selected)
        self.assertFalse(extra.new_name)
        apply_pair_group_status(items)
        self.assertEqual(by_name(items, ".mkv").status, "OK")
        self.assertEqual(extra.status, "Nem támogatott")


if __name__ == "__main__":
    unittest.main(verbosity=2)
