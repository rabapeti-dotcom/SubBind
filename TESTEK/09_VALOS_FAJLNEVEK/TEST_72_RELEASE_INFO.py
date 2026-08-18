"""
Release-metaadat tokenek (resolution, codec, source) – kiszűrés regresszió.
"""
import re
import unittest

from _common import BaseTest, parse, render_series, SERIES_TEMPLATE, render_template


class TestReleaseInfo(BaseTest):
    def test_resolution_and_source_removed_from_output(self):
        name = "Show.Name.S02E04.1080p.WEB-DL.mkv"
        out = self.assert_renders(name, "Show.Name.S02E04.mkv")
        self.assertNotIn("1080p", out)
        self.assertNotIn("WEB-DL", out)
        self.assertNotIn("web-dl", out.lower())

    def test_uhd_hdr_codec_tokens_stripped(self):
        name = "Series.Title.S03E08.2160p.HDR.DV.WEB-DL.x265.HEVC.mkv"
        out = self.assert_renders(name, "Series.Title.S03E08.mkv")
        for token in ("2160p", "HDR", "DV", "x265", "HEVC", "WEB-DL"):
            self.assertNotIn(token, out)

    def test_group_tag_not_in_rendered_name(self):
        name = "Another.Show.S01E02.720p.HDTV.x264-ETHEL.mkv"
        out = self.assert_renders(name, "Another.Show.S01E02.mkv")
        self.assertNotIn("ETHEL", out)
        self.assertNotIn("x264", out)
        self.assertNotIn("HDTV", out)

    def test_episode_code_not_duplicated_in_output(self):
        """A sablon SxxExx-et ad; a release-infó nem maradhat középen."""
        name = "Show.Name.S02E04.1080p.WEB-DL.mkv"
        out = self.assert_renders(name, "Show.Name.S02E04.mkv")
        self.assertEqual(out.count("S02E04"), 1)

    def test_title_with_embedded_episode_is_cleaned_before_render(self):
        """Ha a cím már tartalmaz epizódkódot, _clean_render_title eltávolítja."""
        name = "Show.Name.S02E04.1080p.WEB-DL.mkv"
        item = parse(self.path_for(name))
        polluted_title = "Show.Name.S02E04.1080p"
        out = render_template(SERIES_TEMPLATE, item, polluted_title)
        self.assertEqual(out, "Show.Name.S02E04.mkv")
        self.assertNotRegex(out, re.compile(r"S02E04.*S02E04", re.I))


if __name__ == "__main__":
    unittest.main(verbosity=2)
