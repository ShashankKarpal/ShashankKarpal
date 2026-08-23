#!/usr/bin/env python3
"""Focused regression tests for the Ink and Bone generator."""

import contextlib
import io
import math
import os
import tempfile
import unittest

import generate_marks as gm


class GeneratorTests(unittest.TestCase):
    def test_public_import_is_public_only(self):
        self.assertEqual(gm.MARKS, gm.PUBLIC_MARKS)
        self.assertTrue(gm.PUBLIC_MARKS)
        self.assertTrue(all(not mark["private"] for mark in gm.PUBLIC_MARKS.values()))
        self.assertTrue(all(not mark.get("private_overlay")
                            for mark in gm.PUBLIC_MARKS.values()))

    def test_stable_ids_and_aliases_are_unique(self):
        gm.validate_registry(gm.PUBLIC_MARKS)
        aliases = gm.alias_map(gm.PUBLIC_MARKS)
        for canonical in gm.PUBLIC_MARKS:
            self.assertEqual(aliases[canonical], canonical)
        self.assertEqual(len({mark["id"] for mark in gm.PUBLIC_MARKS.values()}),
                         len(gm.PUBLIC_MARKS))

    def test_legacy_private_metadata_fails_closed(self):
        mark = dict(next(iter(gm.PUBLIC_MARKS.values())))
        mark["private"] = True
        mark.pop("id")
        mark.pop("aliases")
        migrated, changed = gm.legacy_private_metadata("local-private", mark)
        self.assertTrue(changed)
        self.assertTrue(migrated["retired"])
        self.assertEqual(migrated["aliases"], ["local-private"])
        self.assertTrue(migrated["id"].startswith("private-"))

    def test_private_cli_guards(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                gm.parse_args(["--private-overlay", "/tmp/not-loaded.py"])
            with self.assertRaises(SystemExit):
                gm.parse_args(["--include-private"])
            with self.assertRaises(SystemExit):
                gm.parse_args(["--include-retired"])

    def test_declared_fonts_load_including_600(self):
        gm.validate_font_files()
        self.assertIsNotNone(gm.ui_font(600))

    def test_missing_glyph_fails_loudly(self):
        with self.assertRaisesRegex(ValueError, "missing glyph"):
            gm.text_paths("\N{SNOWMAN}")

    def test_grain_is_deterministic_and_not_tiled(self):
        first = gm.grain_overlay((320, 64), 0.16, "unit-test")
        second = gm.grain_overlay((320, 64), 0.16, "unit-test")
        self.assertEqual(first.tobytes(), second.tobytes())
        self.assertNotEqual(first.crop((0, 0, 64, 64)).tobytes(),
                            first.crop((256, 0, 320, 64)).tobytes())

    def test_pdf_metadata_is_deterministic(self):
        project = next(iter(gm.PUBLIC_MARKS))
        svg = gm.mark_svg(project, "master", "dark")
        with tempfile.TemporaryDirectory() as root:
            first = os.path.join(root, "first.pdf")
            second = os.path.join(root, "second.pdf")
            gm.svg_to_pdf(svg, first)
            gm.svg_to_pdf(svg, second)
            with open(first, "rb") as first_file, open(second, "rb") as second_file:
                self.assertEqual(first_file.read(), second_file.read())

    def test_svg_grain_has_one_opacity_stage(self):
        svg = gm.banner_svg(next(iter(gm.PUBLIC_MARKS)), "dark")
        self.assertNotIn("feFuncA", svg)
        self.assertEqual(svg.count('filter="url(#gr)"'), 1)

    def test_raster_grain_stays_under_foreground(self):
        project = next(iter(gm.PUBLIC_MARKS))
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "banner.png")
            gm.render_with_grain(
                gm.banner_svg(project, "dark", with_ground=False),
                path, 1400, 400, "dark", "test-banner")
            image = gm.Image.open(path).convert("RGB")
            rail = (gm.PAL["dark"]["ink"] if
                    gm.MARKS[project]["cat"] == "ink" else
                    gm.PAL["dark"][gm.MARKS[project]["cat"]])
            self.assertEqual(image.getpixel((0, 200)), gm.hex_rgb(rail))

    def test_small_mark_gate(self):
        for project in gm.PUBLIC_MARKS:
            for px in (16, 24):
                for treatment in ("dark", "light", "mono"):
                    with self.subTest(project=project, px=px, treatment=treatment):
                        metrics = gm.alpha_metrics(
                            gm.small_mark_image(project, px, treatment))
                        self.assertTrue(metrics["pass"], metrics)

    def test_avatar_rim_is_self_sufficient(self):
        outer = gm.PAL["dark"]["ink"]
        inner = gm.PAL["light"]["stateIndicator"]
        self.assertGreaterEqual(
            gm.contrast_ratio(outer, gm.AVATAR_HOSTS["github-dark"]), 3)
        self.assertGreaterEqual(
            gm.contrast_ratio(inner, gm.AVATAR_HOSTS["white"]), 3)
        self.assertEqual(gm.avatar_variant(80), "compact")
        self.assertEqual(gm.avatar_variant(40), "micro")
        self.assertEqual(gm.avatar_variant(20), "micro")

    def test_maskable_pwa_art_stays_in_safe_circle(self):
        px = 512
        limit = px * 0.4
        center = (px - 1) / 2
        ground = gm.hex_rgb(gm.PAL["dark"]["page"]) + (255,)
        for project in gm.PUBLIC_MARKS:
            with self.subTest(project=project):
                image = gm.png_bytes_to_img(
                    gm.svg_to_png(gm.pwa_icon_svg(project, px, maskable=True), px)
                )
                foreground = [
                    (x, y)
                    for y in range(px)
                    for x in range(px)
                    if image.getpixel((x, y)) != ground
                ]
                self.assertTrue(foreground)
                furthest = max(
                    math.hypot(x - center, y - center) for x, y in foreground
                )
                self.assertLessEqual(furthest, limit)

    def test_transactional_directory_replace(self):
        with tempfile.TemporaryDirectory() as root:
            staged = os.path.join(root, "staged")
            destination = os.path.join(root, "destination")
            os.mkdir(staged)
            os.mkdir(destination)
            with open(os.path.join(staged, "new"), "w", encoding="utf-8") as handle:
                handle.write("new")
            with open(os.path.join(destination, "old"), "w", encoding="utf-8") as handle:
                handle.write("old")
            gm.transactional_commit_dir(staged, destination)
            self.assertEqual(os.listdir(destination), ["new"])

    def test_public_render_api_remains_available(self):
        for name in ("mark_svg", "wordmark_svg", "favicon_svg", "tile_svg", "pwa_icon_svg",
                     "mono_mark_png", "svg_to_png", "png_bytes_to_img"):
            self.assertTrue(callable(getattr(gm, name)))


if __name__ == "__main__":
    unittest.main()
