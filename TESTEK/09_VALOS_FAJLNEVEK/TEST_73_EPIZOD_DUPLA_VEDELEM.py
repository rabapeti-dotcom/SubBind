"""
Dupla epizódkód regresszió – explicit védelem (_clean_render_title).
"""
import re
import unittest

from _common import BaseTest, parse, render_series, SERIES_TEMPLATE, render_template


class TestEpizodDuplaVedelem(BaseTest):
    def test_show_name_s02e04_no_double_episode(self):
        """Kötelező regresszió: a dupla S02E04 kimenet tiltott."""
        name = "Show.Name.S02E04.1080p.WEB-DL.mkv"
        expected = "Show.Name.S02E04.mkv"
        forbidden = "Show.Name.S02E04.1080p.S02E04.mkv"

        item = parse(self.path_for(name))
        out = render_series(item)
        self.assertEqual(out, expected)
        self.assertNotEqual(out, forbidden)
        self.assertEqual(out.count("S02E04"), 1)

    def test_neon_frontier_no_double_episode(self):
        name = "Neon.Frontier.S02E04.1080p.mkv"
        out = self.assert_renders(name, "Neon.Frontier.S02E04.mkv")
        self.assertNotRegex(out, re.compile(r"S02E04.*S02E04", re.I))

    def test_polluted_title_argument_still_safe(self):
        """A GUI analyze() néha epizódkódot tartalmazó címet ad át – dupla epizód tiltott."""
        name = "Show.Name.S02E04.1080p.WEB-DL.mkv"
        item = parse(self.path_for(name))
        safe_titles = [
            "Show.Name.S02E04.1080p",
            "Show.Name.S02E04",
        ]
        for polluted in safe_titles:
            with self.subTest(polluted=polluted):
                out = render_template(SERIES_TEMPLATE, item, polluted)
                self.assertEqual(out, "Show.Name.S02E04.mkv")
                self.assertEqual(out.count("S02E04"), 1)

    def test_polluted_title_with_web_dl_splits_tokens(self):
        """
        Szennyezett cím WEB-DL tokenekkel: a dupla epizódkód továbbra is tiltott.
        A WEB/DL tokenek pontos alakja nem rögzített követelmény.
        """
        name = "Show.Name.S02E04.1080p.WEB-DL.mkv"
        item = parse(self.path_for(name))
        out = render_template(SERIES_TEMPLATE, item, "Show.Name.S02E04.1080p.WEB-DL")
        self.assertTrue(out.endswith(".mkv"))
        self.assertEqual(out.count("S02E04"), 1)
        self.assertNotEqual(out, "Show.Name.S02E04.1080p.S02E04.mkv")
        self.assertNotRegex(out, re.compile(r"S02E04.*S02E04", re.I))

    def test_1x01_format_no_double_episode(self):
        name = "Show.1x01.720p.HDTV.x264.mkv"
        out = self.assert_renders(name, "Show.S01E01.mkv")
        self.assertNotRegex(out, re.compile(r"S01E01.*S01E01", re.I))


if __name__ == "__main__":
    unittest.main(verbosity=2)
