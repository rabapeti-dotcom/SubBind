"""
Valós release-szerű sorozatfájlnevek – parse és render regresszió.
"""
import unittest

from _common import BaseTest, parse, render_series


class TestValosSorozatnevek(BaseTest):
    def test_show_name_s02e04_web_dl(self):
        name = "Show.Name.S02E04.1080p.WEB-DL.mkv"
        self.assert_renders(name, "Show.Name.S02E04.mkv")
        item = parse(self.path_for(name))
        self.assertEqual(item.season, 2)
        self.assertEqual(item.episode, 4)
        self.assertEqual(item.confidence, "high")
        self.assertEqual(item.title, "Show.Name")

    def test_neon_frontier_release_pack(self):
        name = "Neon.Frontier.S02E04.1080p.mkv"
        self.assert_renders(name, "Neon.Frontier.S02E04.mkv")
        item = parse(self.path_for(name))
        self.assertEqual(item.title, "Neon.Frontier")

    def test_breaking_bad_uhd_pack(self):
        name = "Breaking.Bad.S05E16.2160p.HDR.DV.WEB-DL.x265.mkv"
        self.assert_renders(name, "Breaking.Bad.S05E16.mkv")
        item = parse(self.path_for(name))
        self.assertEqual((item.season, item.episode), (5, 16))

    def test_mandalorian_bluray_group_tag(self):
        name = "The.Mandalorian.S01E01.1080p.BluRay.x264-GROUP.mkv"
        self.assert_renders(name, "The.Mandalorian.S01E01.mkv")
        item = parse(self.path_for(name))
        self.assertEqual(item.title, "The.Mandalorian")

    def test_readme_style_release_name(self):
        """A README példájához hasonló, tipikus release-csomag."""
        name = "film.cime.s01e01.web-dl.aac2.0.h.264-tdi.mkv"
        self.assert_renders(name, "film.cime.S01E01.mkv")
        item = parse(self.path_for(name))
        self.assertEqual((item.season, item.episode), (1, 1))
        self.assertEqual(item.title, "film.cime")

    def test_space_separated_episode_in_filename(self):
        """Szóközös fájlnév – a GUI tesztekhez hasonló valós elnevezés."""
        name = "Neon Frontier S02E04 1080p.mkv"
        item = parse(self.path_for(name))
        self.assertEqual((item.season, item.episode), (2, 4))
        self.assertEqual(item.confidence, "high")
        self.assertEqual(render_series(item), "Neon.Frontier.S02E04.mkv")


if __name__ == "__main__":
    unittest.main(verbosity=2)
