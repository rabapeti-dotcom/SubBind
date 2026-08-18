"""
Valós release-szerű filmfájlnevek – film sablon ({CIM}) regresszió.

Filmeknél nincs kötelező SxxExx; a motor évszámot és release tokent kezel.
"""
import unittest

from _common import BaseTest, parse, render_film


class TestValosFilmnevek(BaseTest):
    def test_oppenheimer_year_kept(self):
        name = "Oppenheimer.2023.1080p.BluRay.x265.mkv"
        self.assert_renders(name, "Oppenheimer.2023.mkv", template="film")
        item = parse(self.path_for(name))
        self.assertIsNone(item.season)
        self.assertIsNone(item.episode)
        self.assertNotEqual(item.confidence, "high")

    def test_dune_part_two_year_in_title(self):
        """
        A WEB-DL token ponttal szétválhat (WEB + DL), ezért a címben maradhat.
        Ez a jelenlegi motor viselkedése – nem automatikus javítási cél.
        """
        name = "Dune.Part.Two.2024.2160p.WEB-DL.mkv"
        item = parse(self.path_for(name))
        self.assertEqual(item.title, "Dune.Part.Two.2024.WEB.DL")
        self.assertEqual(render_film(item), "Dune.Part.Two.2024.WEB.DL.mkv")

    def test_simple_film_year_web_dl_splits_in_title(self):
        """
        A WEB-DL token ponttal szétválhat (WEB + DL), ezért a címben maradhat.
        Jelenlegi viselkedés: A.Film.2024.WEB.DL.mkv
        """
        name = "A.Film.2024.1080p.WEB-DL.mkv"
        item = parse(self.path_for(name))
        self.assertIsNone(item.season)
        self.assertEqual(item.title, "A.Film.2024.WEB.DL")
        self.assertEqual(render_film(item), "A.Film.2024.WEB.DL.mkv")

    def test_film_no_episode_in_output(self):
        name = "Inception.2010.720p.BRRip.x264.mkv"
        out = self.assert_renders(name, "Inception.2010.mkv", template="film")
        self.assertNotRegex(out, r"S\d{2}E\d{2}", "Film kimenet nem tartalmazhat epizódkódot")


if __name__ == "__main__":
    unittest.main(verbosity=2)
