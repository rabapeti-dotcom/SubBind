"""
Valós release-szerű feliratfájlnevek – nyelv, variáns, render regresszió.
"""
import unittest

from _common import BaseTest, parse, render_series, SUB


class TestValosFeliratnevek(BaseTest):
    def test_magyar_srt_short_tag(self):
        name = "Show.Name.S02E04.1080p.WEB-DL.hu.srt"
        self.assert_renders(name, "Show.Name.S02E04.srt", template="series")
        item = parse(self.path_for(name, SUB))
        self.assertEqual(item.kind, "sub")
        self.assertEqual(item.lang, "hu")

    def test_magyar_srt_hun_tag(self):
        name = "Show.Name.S02E04.1080p.WEB-DL.HUN.srt"
        self.assert_renders(name, "Show.Name.S02E04.srt")
        item = parse(self.path_for(name, SUB))
        self.assertEqual(item.lang, "hu")

    def test_idegen_nyelv_suffix(self):
        """Nem magyar feliratnál a motor .en utótagot ad (ha nincs {NYELV} a sablonban)."""
        name = "Show.Name.S02E04.1080p.WEB-DL.eng.srt"
        self.assert_renders(name, "Show.Name.S02E04.en.srt")
        item = parse(self.path_for(name, SUB))
        self.assertEqual(item.lang, "en")

    def test_nemet_felirat(self):
        name = "Show.Name.S02E04.1080p.WEB-DL.german.srt"
        self.assert_renders(name, "Show.Name.S02E04.de.srt")
        item = parse(self.path_for(name, SUB))
        self.assertEqual(item.lang, "de")

    def test_forced_variant_hu(self):
        """L2.4 B stratégia: HU forced felismerhető, és .hu.forced utótagot kap."""
        name = "Show.Name.S02E04.1080p.WEB-DL.hu.forced.srt"
        item = parse(self.path_for(name, SUB))
        self.assertEqual(item.lang, "hu")
        self.assertEqual(item.variant, "forced")
        self.assertEqual(render_series(item), "Show.Name.S02E04.hu.forced.srt")

    def test_readme_style_mismatched_subtitle_name(self):
        """README példa: hosszú release-feliratnév – a párosításhoz SxxExx kell."""
        name = "FILM.CIME.S01E01.The.Eyes.ATV.WEB-DL.hu.srt"
        item = parse(self.path_for(name, SUB))
        self.assertEqual((item.season, item.episode), (1, 1))
        self.assertEqual(item.lang, "hu")
        self.assertEqual(render_series(item), "FILM.CIME.S01E01.srt")


if __name__ == "__main__":
    unittest.main(verbosity=2)
