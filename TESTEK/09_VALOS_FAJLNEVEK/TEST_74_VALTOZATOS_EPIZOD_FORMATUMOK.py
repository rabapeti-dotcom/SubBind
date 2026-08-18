"""
Változatos epizódkód-formák – a motor tényleges viselkedése.

Nem minden forma támogatott. A nem támogatott esetek dokumentálva vannak,
a motor nem módosul automatikusan.
"""
import unittest

from _common import BaseTest, parse, render_series


class TestTamogatottFormatumok(BaseTest):
    def test_s02e04_standard(self):
        name = "Show.Name.S02E04.1080p.mkv"
        self.assert_renders(name, "Show.Name.S02E04.mkv")
        item = parse(self.path_for(name))
        self.assertEqual(item.confidence, "high")

    def test_s2e4_single_digit(self):
        """Egyjegyű S/E – felismerve, kimenet zero-padded."""
        name = "Show.S2E4.1080p.mkv"
        self.assert_renders(name, "Show.S02E04.mkv")
        item = parse(self.path_for(name))
        self.assertEqual((item.season, item.episode), (2, 4))
        self.assertEqual(item.confidence, "high")

    def test_1x01_format(self):
        name = "Show.1x01.720p.HDTV.x264.mkv"
        self.assert_renders(name, "Show.S01E01.mkv")
        item = parse(self.path_for(name))
        self.assertEqual((item.season, item.episode), (1, 1))
        self.assertEqual(item.confidence, "high")

    def test_2x04_format(self):
        name = "Show.2x04.1080p.mkv"
        self.assert_renders(name, "Show.S02E04.mkv")
        item = parse(self.path_for(name))
        self.assertEqual((item.season, item.episode), (2, 4))
        self.assertEqual(item.confidence, "high")

    def test_s02_e04_with_separator(self):
        """S02.E04 – az epizód felismerhető, de a cím tokenekben marad a S02.E04 rész."""
        name = "Show.S02.E04.1080p.mkv"
        item = parse(self.path_for(name))
        self.assertEqual((item.season, item.episode), (2, 4))
        self.assertEqual(item.confidence, "high")
        # A render a _clean_render_title miatt mégis helyes kimenetet ad.
        self.assertEqual(render_series(item), "Show.S02E04.mkv")


class TestNemTamogatottFormatumok(BaseTest):
    def test_bare_e05_not_high_confidence(self):
        """Show.E05 – nincs megbízható évad/epizód felismerés (confidence != high)."""
        name = "Show.E05.1080p.mkv"
        item = parse(self.path_for(name))
        self.assertIsNone(item.season)
        self.assertIsNone(item.episode)
        self.assertNotEqual(item.confidence, "high")

    def test_bare_e05_render_keeps_title(self):
        """Epizód nélkül a sablon nem ad SxxExx-et – a cím marad."""
        name = "Show.E05.1080p.mkv"
        self.assert_renders(name, "Show.E05.mkv")

    def test_episode_only_number_without_season(self):
        """E05 token önmagában nem SxxExx minta – nem támogatott sorozatformátum."""
        name = "Series.Name.E05.WEB-DL.mkv"
        item = parse(self.path_for(name))
        self.assertIsNone(item.season)
        self.assertIsNone(item.episode)
        self.assertNotEqual(item.confidence, "high")
        # A WEB-DL szétválhat WEB + DL tokenekre a címben.
        self.assertEqual(item.title, "Series.Name.E05.WEB.DL")


if __name__ == "__main__":
    unittest.main(verbosity=2)
