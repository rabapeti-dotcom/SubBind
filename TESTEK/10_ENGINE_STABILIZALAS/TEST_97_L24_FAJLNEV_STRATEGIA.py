"""
L2.4: B fájlnév-stratégia — preferált sima felirat tiszta alapnevet kap;
minden más felirat .lang + szükség szerint .variant suffixet.
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
    apply_destination_conflicts,
    disambiguate_subtitle_target_names,
    NamingContext,
)

VIDEO = b"L24_TEST_VIDEO"
SUB = b"L24_TEST_SUB"
SERIES = "{CIM}.{SZEZON}{EPIZOD}"


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


def series_ctx(pref="hu"):
    return NamingContext(mode="Sorozat", template=SERIES, normalize=True, subtitle_pref=pref)


class TestL24FilenameStrategy(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="sr_l24_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def named(self, pref, *names):
        items = make_case(self.tmp, *names)
        apply_item_target_names(items, series_ctx(pref))
        return items

    def test_01_hu_pref_hu_normal_clean(self):
        items = self.named("hu", "Show.S01E01.mkv", "Show.S01E01.hu.srt")
        self.assertEqual(by_name(items, ".hu.srt").new_name, "Show.S01E01.srt")

    def test_02_de_pref_de_normal_clean(self):
        items = self.named("de", "Show.S01E01.mkv", "Show.S01E01.de.srt")
        self.assertEqual(by_name(items, ".de.srt").new_name, "Show.S01E01.srt")

    def test_03_en_pref_en_normal_clean(self):
        items = self.named("en", "Show.S01E01.mkv", "Show.S01E01.en.srt")
        self.assertEqual(by_name(items, ".en.srt").new_name, "Show.S01E01.srt")

    def test_04_es_pref_es_normal_clean(self):
        items = self.named("es", "Show.S01E01.mkv", "Show.S01E01.es.srt")
        self.assertEqual(by_name(items, ".es.srt").new_name, "Show.S01E01.srt")

    def test_05_de_pref_hu_gets_hu_suffix(self):
        items = self.named("de", "Show.S01E01.mkv", "Show.S01E01.hu.srt")
        self.assertEqual(by_name(items, ".hu.srt").new_name, "Show.S01E01.hu.srt")

    def test_06_de_pref_en_gets_en_suffix(self):
        items = self.named("de", "Show.S01E01.mkv", "Show.S01E01.en.srt")
        self.assertEqual(by_name(items, ".en.srt").new_name, "Show.S01E01.en.srt")

    def test_07_de_pref_fr_gets_fr_suffix(self):
        items = self.named("de", "Show.S01E01.mkv", "Show.S01E01.fr.srt")
        self.assertEqual(by_name(items, ".fr.srt").new_name, "Show.S01E01.fr.srt")

    def test_08_de_pref_de_forced_lang_and_variant(self):
        items = self.named("de", "Show.S01E01.mkv", "Show.S01E01.de.forced.srt")
        self.assertEqual(by_name(items, "forced").new_name, "Show.S01E01.de.forced.srt")

    def test_09_de_pref_de_sdh_lang_and_variant(self):
        items = self.named("de", "Show.S01E01.mkv", "Show.S01E01.de.sdh.srt")
        self.assertEqual(by_name(items, "sdh").new_name, "Show.S01E01.de.sdh.srt")

    def test_10_de_pref_de_cc_lang_and_variant(self):
        items = self.named("de", "Show.S01E01.mkv", "Show.S01E01.de.cc.srt")
        self.assertEqual(by_name(items, ".cc.srt").new_name, "Show.S01E01.de.cc.srt")

    def test_11_de_pref_de_hu_en_clean_hu_en(self):
        items = self.named(
            "de",
            "Show.S01E01.mkv",
            "Show.S01E01.de.srt",
            "Show.S01E01.hu.srt",
            "Show.S01E01.en.srt",
        )
        self.assertEqual(by_name(items, "Show.S01E01.de.srt").new_name, "Show.S01E01.srt")
        self.assertEqual(by_name(items, "Show.S01E01.hu.srt").new_name, "Show.S01E01.hu.srt")
        self.assertEqual(by_name(items, "Show.S01E01.en.srt").new_name, "Show.S01E01.en.srt")

    def test_12_de_pref_de_plus_de_forced(self):
        items = self.named(
            "de",
            "Show.S01E01.mkv",
            "Show.S01E01.de.srt",
            "Show.S01E01.de.forced.srt",
        )
        plain = by_name(items, "Show.S01E01.de.srt")
        forced = by_name(items, "forced")
        self.assertEqual(plain.new_name, "Show.S01E01.srt")
        self.assertEqual(forced.new_name, "Show.S01E01.de.forced.srt")
        disambiguate_subtitle_target_names(items)
        self.assertEqual(plain.new_name, "Show.S01E01.srt")
        self.assertEqual(forced.new_name, "Show.S01E01.de.forced.srt")

    def test_13_hu_pref_hu_plus_hu_forced(self):
        items = self.named(
            "hu",
            "Show.S01E01.mkv",
            "Show.S01E01.hu.srt",
            "Show.S01E01.hu.forced.srt",
        )
        plain = by_name(items, "Show.S01E01.hu.srt")
        forced = by_name(items, "forced")
        self.assertEqual(plain.new_name, "Show.S01E01.srt")
        self.assertEqual(forced.new_name, "Show.S01E01.hu.forced.srt")
        disambiguate_subtitle_target_names(items)
        self.assertEqual(plain.new_name, "Show.S01E01.srt")
        self.assertEqual(forced.new_name, "Show.S01E01.hu.forced.srt")

    def test_14_two_preferred_plain_no_new_suffix_review_stays(self):
        items = self.named(
            "hu",
            "Show.S01E01.mkv",
            "Show.S01E01.hu.srt",
            "Show.S01E01.hun.srt",
        )
        a = by_name(items, "Show.S01E01.hu.srt")
        b = by_name(items, "Show.S01E01.hun.srt")
        self.assertEqual(a.new_name, "Show.S01E01.srt")
        self.assertEqual(b.new_name, "Show.S01E01.srt")
        before = (a.new_name, b.new_name)
        disambiguate_subtitle_target_names(items)
        self.assertEqual((a.new_name, b.new_name), before)
        apply_pair_group_status(items, pref="hu")
        for item in items:
            self.assertEqual(item.status, "Ellenőrzést igényel")
            self.assertEqual(item.note, "Több sima HU felirat ugyanahhoz a címhez")
            if item.kind == "sub":
                self.assertEqual(item.new_name, "Show.S01E01.srt")

    def test_15_existing_target_is_conflict_no_overwrite(self):
        items = self.named("hu", "Show.S01E01.mkv", "Show.S01E01.hu.srt")
        out = self.tmp / "out"
        out.mkdir()
        dest = out / "Show.S01E01.srt"
        dest.write_bytes(b"ORIGINAL_TARGET")

        def destination_for(item):
            if not item.new_name:
                return None
            return out / Path(item.new_name).name

        def source_path(item):
            return Path(item.source_path or item.path)

        apply_destination_conflicts(items, destination_for, source_path)
        sub = by_name(items, ".hu.srt")
        self.assertEqual(sub.status, "Névütközés")
        self.assertEqual(sub.note, "A célfájl már létezik – a program nem írta felül")
        self.assertEqual(dest.read_bytes(), b"ORIGINAL_TARGET")

    def test_render_template_uses_pref_not_lang_eq_pref(self):
        """Preferált forced nem kaphat tiszta nevet: is_preferred_plain_sub, nem lang==pref."""
        item = make_case(self.tmp, "Show.S01E01.de.forced.srt")[0]
        self.assertEqual(
            render_template(SERIES, item, item.title, subtitle_pref="de"),
            "Show.S01E01.de.forced.srt",
        )
        self.assertNotEqual(
            render_template(SERIES, item, item.title, subtitle_pref="de"),
            "Show.S01E01.srt",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
