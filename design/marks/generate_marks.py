#!/usr/bin/env python3
"""Ink and Bone mark pipeline.

Single source of truth for every project mark and its full export matrix.
Geometry lives in MARKS below, drawn on a 96x96 grid, stroke 7, round caps,
true arcs. Each mark has three variants: master, s24, s16 (optically
simplified). Everything else (SVG, PDF, PNG, JPEG, iconsets, icns, ico,
appiconsets, watch assets, menu bar templates, favicons, banners, social
previews, wordmark lockups, contact sheets) is generated from those
definitions. Nothing is hand-placed.

Run from the repository root: bash design/brand/run-mark-pipeline.sh [target ...]

The default build is public-only. A private overlay is loaded only when an
explicit path and --include-private are both supplied. Retired private marks
also require --include-retired. See --help; there is no implicit overlay load.
Deps: cairosvg, pillow, fonttools, icnsutil
On macOS, .icns can also be rebuilt natively:
  iconutil -c icns out/<p>/macos/AppIcon.iconset -o AppIcon.icns
"""

import argparse
import hashlib
import io
import json
import math
import os
import random
import re
import shutil
import sys
import tempfile
import uuid

import cairosvg
from PIL import Image
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
BRAND_DIR = os.path.normpath(os.path.join(HERE, "..", "brand"))
TOKEN_PATH = os.path.join(BRAND_DIR, "brand-tokens.json")
FONT_DIR = os.path.join(BRAND_DIR, "font")
GRAIN_SEED = 96
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class TokenConfigError(ValueError):
    pass


def token_value(data, dotted, expected=None):
    value = data
    walked = []
    for part in dotted.split("."):
        walked.append(part)
        if not isinstance(value, dict) or part not in value:
            raise TokenConfigError("%s: missing token %s" %
                                   (TOKEN_PATH, ".".join(walked)))
        value = value[part]
    if expected is not None and not isinstance(value, expected):
        names = (" or ".join(kind.__name__ for kind in expected)
                 if isinstance(expected, tuple) else expected.__name__)
        raise TokenConfigError("%s: token %s must be %s, got %s" %
                               (TOKEN_PATH, dotted, names,
                                type(value).__name__))
    return value


def token_hex(data, dotted):
    value = token_value(data, dotted, str)
    if not HEX_RE.fullmatch(value):
        raise TokenConfigError("%s: token %s must be a six-digit #RRGGBB colour" %
                               (TOKEN_PATH, dotted))
    return value.upper()


def load_brand_policy():
    try:
        with open(TOKEN_PATH, encoding="utf-8") as token_file:
            data = json.load(token_file)
    except OSError as exc:
        raise TokenConfigError("cannot read canonical tokens %s: %s" %
                               (TOKEN_PATH, exc)) from exc
    except json.JSONDecodeError as exc:
        raise TokenConfigError("invalid JSON in canonical tokens %s: %s" %
                               (TOKEN_PATH, exc)) from exc

    palette = {}
    for theme in ("dark", "light"):
        palette[theme] = {
            "page": token_hex(data, "color.%s.surface.page.hex" % theme),
            "card": token_hex(data, "color.%s.surface.card.hex" % theme),
            "edge": token_hex(data, "color.%s.surface.edge.hex" % theme),
            "edgeStrong": token_hex(data, "color.%s.surface.edgeStrong.hex" % theme),
            "stateIndicator": token_hex(
                data, "color.%s.surface.stateIndicator.hex" % theme),
            "ink": token_hex(data, "color.%s.text.primary.hex" % theme),
            "quiet": token_hex(data, "color.%s.text.quiet.hex" % theme),
        }
        for category in ("copper", "brass", "mist"):
            palette[theme][category] = token_hex(
                data, "color.%s.category.%s.hex" % (theme, category))

    grain_policy = token_value(data, "pattern.grain", dict)
    grain = {
        "dark": token_value(data, "pattern.grain.opacityDark", (int, float)),
        "light": token_value(data, "pattern.grain.opacityLight", (int, float)),
    }
    for theme in ("dark", "light"):
        utility_opacity = token_value(
            data, "color.%s.utility.grain.opacity" % theme, (int, float))
        if float(utility_opacity) != float(grain[theme]):
            raise TokenConfigError(
                "%s: pattern.grain opacity and color.%s.utility.grain.opacity disagree" %
                (TOKEN_PATH, theme))
        if not 0 <= float(grain[theme]) <= 1:
            raise TokenConfigError("%s: grain opacity for %s must be between 0 and 1" %
                                   (TOKEN_PATH, theme))

    display = token_value(data, "font.display", dict)
    ui = token_value(data, "font.ui", dict)
    wordmark = token_value(data, "logo.wordmark", dict)
    for metric in ("unitsPerEm", "xHeight", "ascender", "descender"):
        token_value(data, "font.display.%s" % metric, (int, float))
    files = token_value(data, "font.display.files", list)
    ttf_files = [name for name in files if isinstance(name, str) and name.endswith(".ttf")]
    if len(ttf_files) != 1:
        raise TokenConfigError("%s: font.display.files must name exactly one TTF" % TOKEN_PATH)
    weights = token_value(data, "font.ui.weights", list)
    if not weights or any(not isinstance(weight, int) for weight in weights):
        raise TokenConfigError("%s: font.ui.weights must be a non-empty integer list" %
                               TOKEN_PATH)
    ui_files_raw = token_value(data, "font.ui.files", dict)
    ui_files = {}
    for weight in weights:
        candidates = ui_files_raw.get(str(weight))
        if not isinstance(candidates, list):
            raise TokenConfigError("%s: font.ui.files.%s must be a list" %
                                   (TOKEN_PATH, weight))
        ttf_candidates = [name for name in candidates
                          if isinstance(name, str) and name.endswith(".ttf")]
        if len(ttf_candidates) != 1:
            raise TokenConfigError(
                "%s: font.ui.files.%s must name exactly one TTF" %
                (TOKEN_PATH, weight))
        ui_files[weight] = os.path.join(FONT_DIR, ttf_candidates[0])
    tracking = token_value(data, "logo.wordmark.tracking", str)
    tracking_match = re.match(r"\+?([0-9]*\.?[0-9]+)em(?:\b|\s)", tracking.strip())
    if not tracking_match:
        raise TokenConfigError("%s: logo.wordmark.tracking must start with +0.02em" %
                               TOKEN_PATH)
    xheight_policy = token_value(data, "logo.wordmark.minRenderedXHeight", dict)
    for field in ("screenStandardPx", "screenAbsoluteControlledPx", "printStandardMm"):
        value = token_value(data, "logo.wordmark.minRenderedXHeight.%s" % field,
                            (int, float))
        if value <= 0:
            raise TokenConfigError("%s: logo.wordmark.minRenderedXHeight.%s must be positive" %
                                   (TOKEN_PATH, field))

    return {
        "raw": data,
        "palette": palette,
        "grain": {theme: float(value) for theme, value in grain.items()},
        "grainPolicy": grain_policy,
        "display": display,
        "ui": ui,
        "uiFiles": ui_files,
        "wordmark": wordmark,
        "xHeightPolicy": xheight_policy,
        "displayTtf": os.path.join(FONT_DIR, ttf_files[0]),
        "wordmarkTracking": float(tracking_match.group(1)),
    }


try:
    BRAND = load_brand_policy()
except TokenConfigError as exc:
    raise SystemExit("brand token configuration error: %s" % exc)

PAL = BRAND["palette"]
GRAIN = BRAND["grain"]
FONT_PATH = BRAND["displayTtf"]
DISPLAY_TRACKING = BRAND["wordmarkTracking"]
UI_FONT_FILES = BRAND["uiFiles"]

# element helpers -----------------------------------------------------------

def R(x, y, w, h, rx, role="ink", mode="fill", sw=0, rot=None):
    return {"t": "rect", "x": x, "y": y, "w": w, "h": h, "rx": rx,
            "role": role, "mode": mode, "sw": sw, "rot": rot}

def C(cx, cy, r, role="ink", mode="fill", sw=0):
    return {"t": "circle", "cx": cx, "cy": cy, "r": r,
            "role": role, "mode": mode, "sw": sw}

def P(d, role="ink", mode="stroke", sw=7, fill_too=False, rot=None):
    return {"t": "path", "d": d, "role": role, "mode": mode, "sw": sw,
            "fill_too": fill_too, "rot": rot}

def G(inner, transform, role="ink", sw=7):
    return {"t": "group", "inner": inner, "transform": transform,
            "role": role, "sw": sw}

MARKS = {
    "ledge": {
        "id": "ibp-01", "aliases": [],
        "cat": "copper", "private": False,
        "story": "an idea lands on the step, one more chance on the floor, "
                 "caught before the gutter",
        "master": [R(14, 38, 36, 44, 7), R(14, 64, 68, 18, 7),
                   C(46, 28, 10, role="acc")],
        "s24": [R(10, 36, 38, 48, 8), R(10, 62, 76, 22, 8),
                C(46, 23, 13, role="acc")],
        "s16": [R(8, 34, 40, 52, 9), R(8, 60, 80, 26, 9),
                C(46, 19, 15, role="acc")],
    },
    "content-digest-app": {
        "id": "ibp-02", "aliases": [],
        "cat": "copper", "private": False,
        "story": "three lines in, one line carried out",
        "master": [P("M14 28 40 28M14 48 50 48M14 68 40 68"),
                   P("M62 48 84 48", role="acc")],
        "s24": [P("M12 26 40 26M12 48 50 48M12 70 40 70", sw=10),
                P("M62 48 86 48", role="acc", sw=10)],
        "s16": [P("M10 24 38 24M10 48 48 48M10 72 38 72", sw=13),
                P("M60 48 84 48", role="acc", sw=13)],
    },
    "helios": {
        "id": "ibp-03", "aliases": [],
        "cat": "brass", "private": False,
        "story": "many sources into one hub, one steady line out",
        "master": [C(52, 48, 11, mode="stroke", sw=7),
                   P("M12 20 36.8 37.4M10 48 33.5 48M12 76 36.8 58.6"),
                   P("M70.5 48 86 48", role="acc")],
        "s24": [C(50, 48, 12, mode="stroke", sw=10),
                P("M12 22 32.7 36.1M10 48 29 48M12 74 32.7 59.9", sw=10),
                P("M71 48 88 48", role="acc", sw=10)],
        "s16": [C(46, 48, 13, mode="stroke", sw=13),
                P("M10 18 27.2 32.3M10 48 26 48M10 78 27.2 63.7", sw=13),
                P("M68.5 48 84 48", role="acc", sw=13)],
    },
    "zest": {
        "id": "ibp-04", "aliases": [],
        "cat": "brass", "private": False,
        "story": "a cell with charge in it",
        "master": [P("M40 12 56 12"), R(30, 22, 36, 60, 10, mode="stroke", sw=7),
                   P("M36 52 60 36 60 68 Z", role="acc", sw=4, fill_too=True)],
        "s24": [P("M40 13 56 13", sw=10), R(28, 24, 40, 58, 11, mode="stroke", sw=10),
                P("M36 52 58 38 58 66 Z", role="acc", sw=4, fill_too=True)],
        "s16": [P("M40 14 56 14", sw=13), R(26, 26, 44, 56, 12, mode="stroke", sw=13),
                P("M36 54 56 42 56 66 Z", role="acc", sw=5, fill_too=True)],
    },
    "switchdeck": {
        "id": "ibp-05", "aliases": [],
        "cat": "mist", "private": False,
        "story": "a fanned deck, the active card in front",
        "master": [R(26, 48, 44, 28, 7, mode="stroke", sw=7, rot=(-30, 26, 76)),
                   R(26, 48, 44, 28, 7, mode="stroke", sw=7, rot=(-15, 26, 76)),
                   R(26, 48, 44, 28, 7, role="acc")],
        "s24": [R(24, 50, 48, 30, 8, mode="stroke", sw=10, rot=(-30, 24, 80)),
                R(24, 50, 48, 30, 8, mode="stroke", sw=10, rot=(-15, 24, 80)),
                R(24, 50, 48, 30, 8, role="acc")],
        "s16": [R(20, 36, 54, 38, 8, mode="stroke", sw=12,
                  rot=(-16, 20, 74)),
                R(26, 46, 54, 36, 8, role="acc", mode="stroke", sw=12)],
    },
    "claude-tokens": {
        "id": "ibp-06", "aliases": ["uebersicht-claude-tokens"],
        "cat": "mist", "private": False, "display": "claude-tokens",
        "story": "stacks of coins, one loose on top",
        "master": ([R(14, y, 22, 7, 3.5, role="acc") for y in (65, 75)] +
                   [R(38, y, 22, 7, 3.5, role="acc") for y in (45, 55, 65, 75)] +
                   [R(62, y, 22, 7, 3.5, role="acc") for y in (25, 35, 45, 55, 65, 75)] +
                   [R(62, 10, 22, 7, 3.5, rot=(-12, 73, 13.5))]),
        "s24": ([R(8, y, 26, 10, 5, role="acc") for y in (72, 58)] +
                [R(38, y, 26, 10, 5, role="acc") for y in (72, 58, 44)] +
                [R(68, y, 26, 10, 5, role="acc") for y in (72, 58, 44, 30)] +
                [R(68, 12, 26, 10, 5, rot=(-14, 81, 17))]),
        "s16": ([R(8, 70, 26, 12, 6, role="acc")] +
                [R(38, y, 26, 12, 6, role="acc") for y in (70, 54)] +
                [R(66, y, 24, 12, 6, role="acc") for y in (70, 54, 38)] +
                [R(66, 16, 24, 12, 6, rot=(-16, 78, 22))]),
    },
}

# registry validation and private overlay -----------------------------------
# MARKS is the public-safe registry. Some entries belong to private repos, but
# their artwork is deliberately public. Personal/private artwork is different:
# it may enter only through an explicitly named, gitignored overlay at runtime.

PUBLIC_MARKS = dict(MARKS)
MARK_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
RESERVED_TARGETS = {"avatar", "qa"}
MARK_KEYS = {"id", "aliases", "cat", "private", "story", "master", "s24", "s16",
             "display", "no_wordmark", "retired", "private_overlay"}


def validate_element(project, variant, index, element):
    where = "%s.%s[%s]" % (project, variant, index)
    if not isinstance(element, dict):
        raise ValueError("%s must be an element dictionary" % where)
    if element.get("t") not in {"rect", "circle", "path", "group"}:
        raise ValueError("%s has unknown element type %r" % (where, element.get("t")))
    if element.get("role", "ink") not in {"ink", "acc"}:
        raise ValueError("%s has invalid colour role %r" % (where, element.get("role")))
    if element.get("mode", "stroke") not in {"fill", "stroke"}:
        raise ValueError("%s has invalid mode %r" % (where, element.get("mode")))


def validate_registry(registry, *, overlay=False, mixed=False):
    if not isinstance(registry, dict) or not registry:
        raise ValueError("mark registry must be a non-empty dictionary")
    ids = {}
    canonical_names = set(registry)
    aliases = {}
    for name, mark in registry.items():
        if not isinstance(name, str) or not MARK_NAME_RE.fullmatch(name):
            raise ValueError("invalid mark name %r" % name)
        if name in RESERVED_TARGETS:
            raise ValueError("mark name %r collides with a reserved target" % name)
        if not isinstance(mark, dict):
            raise ValueError("mark %r must be a dictionary" % name)
        unexpected = set(mark) - MARK_KEYS
        if unexpected:
            raise ValueError("mark %r has unexpected keys: %s" %
                             (name, ", ".join(sorted(unexpected))))
        missing = {"id", "aliases", "cat", "private", "story",
                   "master", "s24", "s16"} - set(mark)
        if missing:
            raise ValueError("mark %r is missing: %s" % (name, ", ".join(sorted(missing))))
        if mark["cat"] not in {"ink", "copper", "brass", "mist"}:
            raise ValueError("mark %r has invalid category %r" % (name, mark["cat"]))
        if not isinstance(mark["private"], bool):
            raise ValueError("mark %r private must be boolean" % name)
        if not isinstance(mark["id"], str) or not MARK_NAME_RE.fullmatch(mark["id"]):
            raise ValueError("mark %r id must be a stable lowercase identifier" % name)
        if mark["id"] in ids:
            raise ValueError("mark IDs collide: %r and %r both use %r" %
                             (ids[mark["id"]], name, mark["id"]))
        ids[mark["id"]] = name
        if not isinstance(mark["aliases"], list) or any(
                not isinstance(alias, str) or not MARK_NAME_RE.fullmatch(alias)
                for alias in mark["aliases"]):
            raise ValueError("mark %r aliases must be lowercase project-name strings" % name)
        for alias in mark["aliases"]:
            if alias in RESERVED_TARGETS:
                raise ValueError("mark %r alias %r collides with a reserved target" %
                                 (name, alias))
            if alias in canonical_names and alias != name:
                raise ValueError("mark %r alias %r collides with canonical mark %r" %
                                 (name, alias, alias))
            if alias in aliases and aliases[alias] != name:
                raise ValueError("mark alias %r is shared by %r and %r" %
                                 (alias, aliases[alias], name))
            aliases[alias] = name
        if not isinstance(mark["story"], str) or not mark["story"].strip():
            raise ValueError("mark %r needs a non-empty story" % name)
        if "display" in mark and not isinstance(mark["display"], str):
            raise ValueError("mark %r display must be a string" % name)
        if "no_wordmark" in mark and not isinstance(mark["no_wordmark"], bool):
            raise ValueError("mark %r no_wordmark must be boolean" % name)
        if "retired" in mark and not isinstance(mark["retired"], bool):
            raise ValueError("mark %r retired must be boolean" % name)
        is_overlay_entry = overlay or (mixed and mark.get("private_overlay"))
        if is_overlay_entry:
            if mark.get("private") is not True:
                raise ValueError("private overlay mark %r must declare private: True" % name)
            if "retired" not in mark:
                raise ValueError("private overlay mark %r must explicitly declare retired" % name)
        elif mark.get("private_overlay"):
            raise ValueError("public registry mark %r cannot set private_overlay" % name)
        elif mark["private"]:
            raise ValueError("public registry mark %r cannot declare private: True; "
                             "move it to an explicit overlay" % name)
        for variant in ("master", "s24", "s16"):
            elements = mark[variant]
            if not isinstance(elements, list) or not elements:
                raise ValueError("mark %r variant %s must be a non-empty list" %
                                 (name, variant))
            for index, element in enumerate(elements):
                validate_element(name, variant, index, element)


def legacy_private_metadata(name, mark):
    """Fail-closed defaults for an older local overlay, without exposing it."""
    entry = dict(mark)
    migrated = False
    if "id" not in entry:
        suffix = hashlib.sha256(("private-project:" + name).encode()).hexdigest()[:12]
        entry["id"] = "private-" + suffix
        migrated = True
    if "aliases" not in entry:
        entry["aliases"] = [name]
        migrated = True
    if "retired" not in entry:
        entry["retired"] = True
        migrated = True
    return entry, migrated


def load_private_overlays(paths):
    """Load explicitly named private overlays after CLI guards are checked."""
    merged = dict(PUBLIC_MARKS)
    any_legacy = False
    for supplied_path in paths:
        path = os.path.abspath(supplied_path)
        if not os.path.isfile(path):
            raise ValueError("private overlay does not exist: %s" % path)
        safe_builtins = {"dict": dict, "list": list, "range": range, "tuple": tuple}
        namespace = {"R": R, "C": C, "P": P, "G": G,
                     "__builtins__": safe_builtins}
        with open(path, encoding="utf-8") as overlay_file:
            code = compile(overlay_file.read(), path, "exec")
        exec(code, namespace)
        raw_overlay = namespace.get("PRIVATE_MARKS")
        if not isinstance(raw_overlay, dict) or not raw_overlay:
            raise ValueError("private overlay %s must define a non-empty PRIVATE_MARKS dict" %
                             path)
        overlay = {}
        for name, mark in raw_overlay.items():
            if not isinstance(mark, dict):
                raise ValueError("private overlay %s contains a non-dictionary mark" % path)
            entry, migrated = legacy_private_metadata(name, mark)
            any_legacy = any_legacy or migrated
            overlay[name] = entry
        validate_registry(overlay, overlay=True)
        collisions = set(merged) & set(overlay)
        if collisions:
            raise ValueError("private overlay collision after explicit load: %s" %
                             ", ".join(sorted(collisions)))
        for name, mark in overlay.items():
            entry = dict(mark)
            entry["private_overlay"] = True
            merged[name] = entry
        validate_registry(merged, mixed=True)
    if any_legacy:
        print("warning: a private overlay used guarded legacy metadata defaults; "
              "migrate it to explicit id, aliases, and retired fields", file=sys.stderr)
    return merged


def alias_map(registry):
    result = {}
    for canonical, mark in registry.items():
        result[canonical] = canonical
        for alias in mark["aliases"]:
            result[alias] = canonical
    return result


validate_registry(PUBLIC_MARKS)

# svg emit ------------------------------------------------------------------

def colour(role, theme, mono=None):
    if mono:
        return mono
    p = PAL[theme]
    return p["ink"] if role == "ink" else p[role]

def el_svg(e, theme, cat, mono=None):
    role = e.get("role", "ink")
    col = colour("ink" if role == "ink" else cat, theme, mono)
    if e["t"] == "group":
        return ('<g fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round" '
                'stroke-linejoin="round" transform="%s"><path d="%s"/></g>'
                % (col, e["sw"], e["transform"], e["inner"]))
    if e["t"] == "circle":
        if e["mode"] == "stroke":
            return ('<circle cx="%s" cy="%s" r="%s" fill="none" stroke="%s" '
                    'stroke-width="%s"/>' % (e["cx"], e["cy"], e["r"], col, e["sw"]))
        return '<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % (e["cx"], e["cy"], e["r"], col)
    if e["t"] == "rect":
        rot = ' transform="rotate(%s %s %s)"' % e["rot"] if e.get("rot") else ""
        if e["mode"] == "stroke":
            return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="none" '
                    'stroke="%s" stroke-width="%s" stroke-linejoin="round"%s/>'
                    % (e["x"], e["y"], e["w"], e["h"], e["rx"], col, e["sw"], rot))
        return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"%s/>'
                % (e["x"], e["y"], e["w"], e["h"], e["rx"], col, rot))
    if e["t"] == "path":
        rot = ' transform="rotate(%s %s %s)"' % e["rot"] if e.get("rot") else ""
        if e.get("fill_too"):
            return ('<path d="%s" fill="%s" stroke="%s" stroke-width="%s" '
                    'stroke-linejoin="round"%s/>' % (e["d"], col, col, e["sw"], rot))
        return ('<path d="%s" fill="none" stroke="%s" stroke-width="%s" '
                'stroke-linecap="round" stroke-linejoin="round"%s/>'
                % (e["d"], col, e["sw"], rot))
    raise ValueError(e["t"])

def mark_svg(project, variant, theme, ground=None, mono=None, size=None):
    m = MARKS[project]
    body = "".join(el_svg(e, theme, m["cat"], mono) for e in m[variant])
    bg = '<rect width="96" height="96" fill="%s"/>' % ground if ground else ""
    wh = ' width="%s" height="%s"' % (size, size) if size else ""
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96"%s>%s%s</svg>'
            % (wh, bg, body))

def variant_for(px):
    if px >= 48:
        return "master"
    if px >= 20:
        return "s24"
    return "s16"

def favicon_svg(project):
    m = MARKS[project]
    dark = "".join(el_svg(e, "dark", m["cat"]) for e in m["s16"])
    light = "".join(el_svg(e, "light", m["cat"]) for e in m["s16"])
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96">'
            '<style>.d{display:none}@media(prefers-color-scheme:dark)'
            '{.l{display:none}.d{display:inline}}</style>'
            '<g class="l">%s</g><g class="d">%s</g></svg>' % (light, dark))

# raster --------------------------------------------------------------------

def svg_to_png(svg, px_w, px_h=None):
    px_h = px_h or px_w
    return cairosvg.svg2png(bytestring=svg.encode(), output_width=px_w,
                            output_height=px_h)

def png_bytes_to_img(b):
    return Image.open(io.BytesIO(b)).convert("RGBA")

def save_png(svg, path, px_w, px_h=None):
    with open(path, "wb") as f:
        f.write(svg_to_png(svg, px_w, px_h))


class DeterministicPDFSurface(cairosvg.surface.PDFSurface):
    """CairoSVG PDF surface with stable metadata for reproducible exports."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        fixed_date = "2000-01-01T00:00:00Z"
        self.cairo.set_metadata(
            cairosvg.surface.cairo.PDF_METADATA_CREATE_DATE, fixed_date)
        self.cairo.set_metadata(
            cairosvg.surface.cairo.PDF_METADATA_MOD_DATE, fixed_date)


def svg_to_pdf(svg, path):
    DeterministicPDFSurface.convert(bytestring=svg.encode(), write_to=path)

def stable_seed(key):
    digest = hashlib.sha256(("ink-and-bone:%s:%s" % (GRAIN_SEED, key)).encode()).digest()
    return int.from_bytes(digest[:4], "big") or 1


def grain_overlay(size_wh, opacity, seed_key):
    """Full-surface deterministic grain; no repeated tile and no global RNG."""
    w, h = size_wh
    state = stable_seed(seed_key)
    pixels = bytearray(w * h)
    for index in range(len(pixels)):
        # xorshift32 is explicit, stable across Python/Pillow versions, and fast.
        state ^= (state << 13) & 0xFFFFFFFF
        state ^= state >> 17
        state ^= (state << 5) & 0xFFFFFFFF
        pixels[index] = (state >> 24) & 0xFF
    g = Image.frombytes("L", (w, h), bytes(pixels))
    a = g.point(lambda v: int(abs(v - 128) * 2 * opacity))
    rgb = g.point(lambda v: 255 if v > 128 else 0)
    return Image.merge("RGBA", (rgb, rgb, rgb, a))

# wordmarks -----------------------------------------------------------------

_font = None

def font():
    global _font
    if _font is None:
        _font = TTFont(FONT_PATH)
    return _font

def text_paths(text, em=100, tracking=None):
    f = font()
    cmap = f.getBestCmap()
    glyphs = f.getGlyphSet()
    upem = f["head"].unitsPerEm
    s = em / upem
    tracking = DISPLAY_TRACKING if tracking is None else tracking
    x = 0.0
    out = []
    for ch in text.lower():
        gname = cmap.get(ord(ch))
        if gname is None:
            raise ValueError("Karpal Geometric is missing glyph %r (U+%04X) in %r" %
                             (ch, ord(ch), text))
        pen = SVGPathPen(glyphs)
        glyphs[gname].draw(pen)
        d = pen.getCommands()
        if d:
            out.append('<g transform="translate(%.2f,0) scale(%.6f,-%.6f)">'
                       '<path d="%s"/></g>' % (x, s, s, d))
        x += glyphs[gname].width * s + tracking * em
    return out, x

def wordmark_svg(project, theme, layout, ground=None):
    m = MARKS[project]
    ink = PAL[theme]["ink"]
    paths, tw = text_paths(m.get("display", project))
    em = 100
    units = float(BRAND["display"]["unitsPerEm"])
    asc = float(BRAND["display"]["ascender"]) * em / units
    desc = abs(float(BRAND["display"]["descender"])) * em / units
    mark_h = 120
    mark = "".join(el_svg(e, theme, m["cat"]) for e in m["master"])
    pad = 40
    if layout == "horizontal":
        W = pad + mark_h + 40 + tw + pad
        H = pad + max(mark_h, asc + desc) + pad
        mk_y = (H - mark_h) / 2
        base = H / 2 + asc / 2 - 6
        body = ('<g transform="translate(%s,%s) scale(%.4f)">%s</g>'
                '<g fill="%s" transform="translate(%s,%.1f)">%s</g>'
                % (pad, mk_y, mark_h / 96.0, mark, ink,
                   pad + mark_h + 40, base, "".join(paths)))
    else:
        W = max(mark_h, tw) + 2 * pad
        H = pad + mark_h + 36 + asc + desc + pad
        body = ('<g transform="translate(%s,%s) scale(%.4f)">%s</g>'
                '<g fill="%s" transform="translate(%s,%.1f)">%s</g>'
                % ((W - mark_h) / 2, pad, mark_h / 96.0, mark, ink,
                   (W - tw) / 2, pad + mark_h + 36 + asc, "".join(paths)))
    bg = '<rect width="%s" height="%s" fill="%s"/>' % (W, H, ground) if ground else ""
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.0f %.0f">%s%s</svg>'
            % (W, H, bg, body)), W, H

_ui_fonts = {}

def ui_font(weight):
    allowed = set(BRAND["ui"]["weights"])
    if weight not in allowed:
        raise ValueError("Montserrat weight %s is not declared in font.ui.weights" % weight)
    if weight not in UI_FONT_FILES:
        raise ValueError("no generator font-file mapping for Montserrat weight %s" % weight)
    path = UI_FONT_FILES[weight]
    if weight not in _ui_fonts:
        if not os.path.isfile(path):
            raise FileNotFoundError("declared Montserrat %s file is missing: %s" %
                                    (weight, path))
        _ui_fonts[weight] = TTFont(path)
    return _ui_fonts[weight]

def ui_text_paths(text, weight=400, em=100, tracking=0.0):
    """Montserrat outlines, same shape as text_paths. font.ui in brand-tokens."""
    f = ui_font(weight)
    cmap = f.getBestCmap()
    glyphs = f.getGlyphSet()
    upem = f["head"].unitsPerEm
    s = em / upem
    x = 0.0
    out = []
    for ch in text:
        gname = cmap.get(ord(ch))
        if gname is None:
            raise ValueError("Montserrat %s is missing glyph %r (U+%04X) in %r" %
                             (weight, ch, ord(ch), text))
        pen = SVGPathPen(glyphs)
        glyphs[gname].draw(pen)
        d = pen.getCommands()
        if d:
            out.append('<g transform="translate(%.2f,0) scale(%.6f,-%.6f)">'
                       '<path d="%s"/></g>' % (x, s, s, d))
        x += glyphs[gname].width * s + tracking * em
    return out, x

# github avatar -------------------------------------------------------------
# The profile avatar is a composite, not a 96-grid mark, so it lives here
# rather than in MARKS. Layout is the v3 plate: contribution field behind a
# terminal card holding the print, the shanky.md wordmark and three lines of
# copy. The card is what keeps grain out from under sub-14px type, which
# brand-tokens forbids.

AVATAR = {
    "grid_display": "shanky.md",
    "copy": ("status: probably on a laptop",
             "one commit at a time",
             "#vibecoding at its best"),
    "export": 460,          # GitHub serves 460 on the profile page
    "grid": {"x0": -14, "y0": -14, "cols": 24, "rows": 24, "cell": 14,
             "pitch": 18, "seed": 31},
    "grid_opacity": {"dark": 0.42, "light": 0.50},
}

AVATAR_HOSTS = {"white": "#FFFFFF", "github-dark": "#0D1117"}


def hex_rgb(value):
    return tuple(int(value[index:index + 2], 16) for index in (1, 3, 5))


def mix_hex(first, second, amount):
    a, b = hex_rgb(first), hex_rgb(second)
    values = [round(a[index] + (b[index] - a[index]) * amount) for index in range(3)]
    return "#%02X%02X%02X" % tuple(values)


def relative_luminance(value):
    channels = []
    for channel in hex_rgb(value):
        component = channel / 255.0
        channels.append(component / 12.92 if component <= 0.04045
                        else ((component + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast_ratio(first, second):
    lighter, darker = sorted((relative_luminance(first), relative_luminance(second)),
                             reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def avatar_ramp(theme):
    """Copper density steps derived from canonical page/category tokens."""
    page, copper = PAL[theme]["page"], PAL[theme]["copper"]
    return {"empty": mix_hex(page, copper, 0.10),
            "levels": [mix_hex(page, copper, amount)
                       for amount in (0.30, 0.52, 0.74, 1.0)]}


def avatar_grid(theme):
    """GitHub-style density field, weighted so the recent side is busier"""
    g = AVATAR["grid"]
    ramp = avatar_ramp(theme)
    rnd = random.Random(g["seed"])
    out = []
    for c in range(g["cols"]):
        recency = c / max(g["cols"] - 1, 1)
        for r in range(g["rows"]):
            if rnd.random() > 0.46 + 0.32 * recency:
                fill = ramp["empty"]
            else:
                w = [0.40 - 0.20 * recency, 0.31,
                     0.19 + 0.09 * recency, 0.10 + 0.11 * recency]
                fill = rnd.choices(ramp["levels"], weights=w)[0]
            out.append('<rect x="%.1f" y="%.1f" width="%s" height="%s" rx="%.1f" '
                       'fill="%s"/>' % (g["x0"] + c * g["pitch"], g["y0"] + r * g["pitch"],
                                        g["cell"], g["cell"], g["cell"] * 0.18, fill))
    return '<g opacity="%s">%s</g>' % (AVATAR["grid_opacity"][theme], "".join(out))


def avatar_print(theme, sw=7.5):
    """the 3D print: head, eyes, neck stubs, plinth, shanky.md wordmark"""
    p = PAL[theme]
    size, top, cx = 72, 122, 200
    ew, eh = size * 0.145, size * 0.215
    ey, off = top + size * 0.40, size * 0.165
    paths, tw = text_paths(AVATAR["grid_display"], em=100)
    target = 98.0
    s = target / tw
    box_w = target + 36
    ptop, ph = 202, 31
    xheight = (float(BRAND["display"]["xHeight"]) *
               100 / float(BRAND["display"]["unitsPerEm"]))
    base = ptop + ph / 2 + xheight * s / 2
    return "".join([
        '<g fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round">'
        '<rect x="%.1f" y="%s" width="%s" height="%s" rx="%.1f"/>'
        '<rect x="%.1f" y="%s" width="%.1f" height="%s" rx="9"/></g>'
        % (p["ink"], sw, cx - size / 2, top, size, size, size * 0.135,
           cx - box_w / 2, ptop, box_w, ph),
        '<g fill="%s"><rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f"/>'
        '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%.1f"/></g>'
        % (p["ink"], cx - off - ew, ey, ew, eh, ew * 0.28,
           cx + off, ey, ew, eh, ew * 0.28),
        '<g fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round">'
        '<path d="M %s,194 L %s,202 M %s,194 L %s,202"/></g>'
        % (p["ink"], sw, cx - 12, cx - 12, cx + 12, cx + 12),
        '<g fill="%s" transform="translate(%.2f,%.2f) scale(%.6f)">%s</g>'
        % (p["ink"], cx - target / 2, base, s, "".join(paths)),
    ])


def avatar_copy(theme):
    """the three lines, Montserrat per font.ui, plus the laptop glyph"""
    p = PAL[theme]
    l1, l2, l3 = AVATAR["copy"]
    out = []

    gw, gap, em = 18.0, 7.0, 11.0
    paths, tw = ui_text_paths(l1, 400, em=em, tracking=0.04)
    total = gw + 5 + gap + tw
    x0 = 200 - total / 2
    gh = gw * 0.62
    out.append('<g fill="none" stroke="%s" stroke-width="1.9" stroke-linecap="round" '
               'stroke-linejoin="round"><rect x="%.1f" y="%.1f" width="%.1f" '
               'height="%.1f" rx="2"/><path d="M %.1f,259 L %.1f,259"/></g>'
               % (p["quiet"], x0, 259 - gh, gw, gh * 0.72, x0 - 2.5, x0 + gw + 2.5))
    out.append('<g fill="%s" transform="translate(%.2f,258)">%s</g>'
               % (p["quiet"], x0 + gw + 5 + gap, "".join(paths)))

    for text, weight, em, tr, col, baseline in (
            (l2, 500, 15.0, 0.02, p["ink"], 284),
            (l3, 400, 10.5, 0.04, p["copper"], 307)):
        paths, tw = ui_text_paths(text, weight, em=em, tracking=tr)
        out.append('<g fill="%s" transform="translate(%.2f,%s)">%s</g>'
                   % (col, 200 - tw / 2, baseline, "".join(paths)))
    return "".join(out)


def avatar_mascot(theme, variant):
    """Optically simplified public mascot for 80, 40 and 20 px exports."""
    p = PAL[theme]
    if variant == "compact":
        head = (102, 68, 196, 184, 30, 20)
        eyes = (34, 51, 41, 14)
        plinth = (74, 277, 252, 62, 18, 18)
        neck_y = (252, 277)
    else:
        head = (104, 74, 192, 178, 30, 28)
        eyes = (36, 52, 42, 14)
        plinth = (82, 272, 236, 66, 18, 0)
        neck_y = (252, 272)
    hx, hy, hw, hh, hr, sw = head
    ew, eh, eoff, er = eyes
    px, py, pw, ph, pr, psw = plinth
    eye_y = hy + 65
    body = [
        '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" '
        'stroke="%s" stroke-width="%s"/>' %
        (hx, hy, hw, hh, hr, p["card"], p["ink"], sw),
        '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"/>' %
        (200 - eoff - ew, eye_y, ew, eh, er, p["ink"]),
        '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"/>' %
        (200 + eoff, eye_y, ew, eh, er, p["ink"]),
        '<path d="M160 %sV%s M240 %sV%s" fill="none" stroke="%s" '
        'stroke-width="%s" stroke-linecap="round"/>' %
        (neck_y[0], neck_y[1], neck_y[0], neck_y[1], p["ink"], sw),
    ]
    if psw:
        body.append('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" '
                    'fill="%s" stroke="%s" stroke-width="%s"/>' %
                    (px, py, pw, ph, pr, p["card"], p["ink"], psw))
    else:
        body.append('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" '
                    'fill="%s"/>' % (px, py, pw, ph, pr, p["ink"]))
    return "".join(body)


def avatar_variant(px):
    if px >= 200:
        return "full"
    if px >= 80:
        return "compact"
    return "micro"


def avatar_rim(px):
    """Two one-device-pixel bands; one survives either GitHub host ground."""
    band = max(1.0, 400.0 / px)
    outer = PAL["dark"]["ink"]
    inner = PAL["light"]["stateIndicator"]
    return ('<circle cx="200" cy="200" r="%.3f" fill="none" stroke="%s" '
            'stroke-width="%.3f"/><circle cx="200" cy="200" r="%.3f" '
            'fill="none" stroke="%s" stroke-width="%.3f"/>' %
            (200 - band / 2, outer, band, 200 - band * 1.5, inner, band))


def avatar_svg(theme, px=None, with_ground=True):
    p = PAL[theme]
    px = px or AVATAR["export"]
    variant = avatar_variant(px)
    ground = ""
    if with_ground:
        ground = '<rect width="400" height="400" fill="%s"/>' % p["page"]
        if variant == "full":
            ground += ('<rect width="400" height="400" filter="url(#gr)" '
                       'opacity="%s"/>' % GRAIN[theme])
    if variant == "full":
        body = "".join([
            avatar_grid(theme),
            '<rect x="58" y="72" width="284" height="252" rx="12" fill="%s" '
            'stroke="%s" stroke-width="2"/>' % (p["card"], p["edgeStrong"]),
            "".join('<circle cx="%s" cy="92" r="4" fill="%s"/>' %
                    (x, p["edgeStrong"]) for x in (78, 94, 110)),
            '<path d="M 58,108 L 342,108" fill="none" stroke="%s" '
            'stroke-width="1.5"/>' % p["edge"],
            avatar_print(theme),
            avatar_copy(theme),
        ])
    else:
        body = avatar_mascot(theme, variant)
    body += avatar_rim(px)
    grain_def = grain_filter_svg(stable_seed("avatar:%s" % theme)) \
        if with_ground and variant == "full" else ""
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" '
            'width="%s" height="%s"><defs>'
            '<clipPath id="disc"><circle cx="200" cy="200" r="200"/></clipPath>%s</defs>'
            '<g clip-path="url(#disc)">%s%s</g></svg>'
            % (px, px, grain_def, ground, body))


def avatar_png(theme, px):
    """Ground, optional grain, then foreground; clipped to the avatar disc."""
    from PIL import ImageDraw
    p = PAL[theme]
    variant = avatar_variant(px)
    disc = Image.new("L", (px, px), 0)
    ImageDraw.Draw(disc).ellipse([0, 0, px - 1, px - 1], fill=255)
    page = Image.new("RGBA", (px, px), hex_rgb(p["page"]) + (255,))
    if variant == "full":
        page.alpha_composite(grain_overlay((px, px), GRAIN[theme],
                                           "avatar:%s" % theme))
    out = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    out.paste(page, (0, 0), disc)
    out.alpha_composite(png_bytes_to_img(
        svg_to_png(avatar_svg(theme, px, with_ground=False), px)))
    return out


def avatar_qa(adir):
    from PIL import ImageDraw
    sizes = (460, 80, 40, 20)
    columns = (("light", "white"), ("light", "github-dark"),
               ("dark", "white"), ("dark", "github-dark"))
    margin, label_w, col_w, header = 20, 94, 490, 76
    row_heights = {460: 500, 80: 120, 40: 90, 20: 70}
    width = label_w + len(columns) * col_w + margin
    height = header + sum(row_heights.values()) + margin
    sheet = Image.new("RGB", (width, height), (32, 30, 27))
    draw = ImageDraw.Draw(sheet)
    draw.text((20, 12), "avatar optical QA - assets x GitHub host grounds",
              fill=(243, 241, 235))
    for column, (asset_theme, host_name) in enumerate(columns):
        x = label_w + column * col_w
        draw.text((x + 12, 44), "%s asset / %s" % (asset_theme, host_name),
                  fill=(243, 241, 235))
    y = header
    for size in sizes:
        row_h = row_heights[size]
        draw.text((20, y + row_h // 2 - 7), "%s px" % size, fill=(207, 223, 232))
        for column, (asset_theme, host_name) in enumerate(columns):
            x = label_w + column * col_w
            host = AVATAR_HOSTS[host_name]
            draw.rectangle((x + 4, y + 4, x + col_w - 4, y + row_h - 4),
                           fill=hex_rgb(host))
            avatar = Image.open(os.path.join(
                adir, "avatar-%s-%s.png" % (asset_theme, size))).convert("RGBA")
            ax = x + (col_w - size) // 2
            ay = y + (row_h - size) // 2
            sheet.paste(avatar, (ax, ay), avatar)
        y += row_h
    sheet.save(os.path.join(adir, "avatar-optical-qa.png"))

    outer, inner = PAL["dark"]["ink"], PAL["light"]["stateIndicator"]
    metrics = {
        "hostGrounds": AVATAR_HOSTS,
        "threshold": 3.0,
        "rim": {"outer": outer, "inner": inner,
                "outerContrast": {name: round(contrast_ratio(outer, colour), 3)
                                  for name, colour in AVATAR_HOSTS.items()},
                "innerContrast": {name: round(contrast_ratio(inner, colour), 3)
                                  for name, colour in AVATAR_HOSTS.items()}},
        "variants": {str(size): avatar_variant(size) for size in sizes},
    }
    if metrics["rim"]["outerContrast"]["github-dark"] < 3 or \
            metrics["rim"]["innerContrast"]["white"] < 3:
        raise ValueError("avatar rim does not clear 3:1 on both GitHub host grounds")
    with open(os.path.join(adir, "avatar-optical-qa.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
        f.write("\n")


def build_avatar(out_root=OUT):
    adir = os.path.join(out_root, "github", "avatar")
    os.makedirs(adir, exist_ok=True)
    for theme in ("dark", "light"):
        svg = avatar_svg(theme, AVATAR["export"])
        with open(os.path.join(adir, "avatar-%s.svg" % theme), "w",
                  encoding="utf-8") as f:
            f.write(svg)
        for px in (460, 400, 200, 80, 40, 20):
            img = avatar_png(theme, px)
            img.save(os.path.join(adir, "avatar-%s-%s.png" % (theme, px)))
    avatar_qa(adir)
    with open(os.path.join(adir, "README.md"), "w", encoding="utf-8") as f:
        f.write("# GitHub profile avatar\n\n"
                "Generated. Do not hand-edit. Rebuild with:\n\n"
                "    bash design/brand/run-mark-pipeline.sh avatar\n\n"
                "The 460, 400 and 200px files use the full plate. The 80, 40 and\n"
                "20px files use optically simplified mascot art with no field,\n"
                "copy or grain. Every size has a host-independent two-band rim.\n"
                "Review avatar-optical-qa.png at 1x before changing the live file.\n\n"
                "Upload avatar-light-460.png at github.com/settings/profile.\n"
                "LIGHT is the live variant, Shanky's recorded call in\n"
                "BRAND-SURFACES.md; do not upload the dark file unless he says\n"
                "otherwise. The upload is manual and GitHub caches avatars hard\n"
                "on its CDN, so verify in a private window, not a normal reload.\n\n"
                "Note: the contribution field is copper. brand-tokens says the\n"
                "profile repo stays ink; carrying copper here is a deliberate\n"
                "owner decision recorded in BRAND-SURFACES.md, not a drift.\n")
    print("  built avatar -> %s" % os.path.relpath(adir, HERE))
    return adir

# banners and social --------------------------------------------------------

def grain_filter_svg(seed):
    policy = BRAND["grainPolicy"]
    return ('<filter id="gr" x="0" y="0" width="100%%" height="100%%" '
            'filterUnits="objectBoundingBox"><feTurbulence type="fractalNoise" '
            'baseFrequency="%s" numOctaves="%s" seed="%s"/>'
            '<feColorMatrix type="saturate" values="%s"/></filter>' %
            (policy["baseFrequency"], policy["numOctaves"], seed, policy["saturate"]))


def banner_svg(project, theme, W=1400, H=400, with_ground=True):
    m = MARKS[project]
    p = PAL[theme]
    rail = p["ink"] if m["cat"] == "ink" else p[m["cat"]]
    mark = "".join(el_svg(e, theme, m["cat"]) for e in m["master"])
    paths, tw = text_paths(m.get("display", project))
    scale_txt = min(1.1, (W - 360 - 60) / tw) if tw else 1.1
    mark_h = 200
    body = []
    if with_ground:
        body.extend([
            '<rect width="%s" height="%s" fill="%s"/>' % (W, H, p["page"]),
            '<defs>%s</defs>' % grain_filter_svg(stable_seed(
                "banner:%s:%s" % (project, theme))),
            '<rect width="%s" height="%s" filter="url(#gr)" opacity="%s"/>'
            % (W, H, GRAIN[theme]),
        ])
    asc = float(BRAND["display"]["ascender"]) * 100 / float(
        BRAND["display"]["unitsPerEm"])
    body.extend([
        '<rect width="8" height="%s" fill="%s"/>' % (H, rail),
        '<g transform="translate(90,%s) scale(%.4f)">%s</g>'
        % ((H - mark_h) / 2, mark_h / 96.0, mark),
        '<g fill="%s" transform="translate(360,%.1f) scale(%s)">%s</g>'
        % (p["ink"], H / 2 + asc * scale_txt / 2, scale_txt, "".join(paths)),
    ])
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s">%s</svg>'
            % (W, H, "".join(body)))

def social_svg(project, W=1280, H=640, with_ground=True):
    m = MARKS[project]
    p = PAL["dark"]
    rail = p["ink"] if m["cat"] == "ink" else p[m["cat"]]
    mark = "".join(el_svg(e, "dark", m["cat"]) for e in m["master"])
    paths, tw = text_paths(m.get("display", project))
    ts = min(1.0, (W - 140) / tw) if tw else 1.0
    mark_h = 280
    body = []
    if with_ground:
        body.extend([
            '<rect width="%s" height="%s" fill="%s"/>' % (W, H, p["page"]),
            '<defs>%s</defs>' % grain_filter_svg(stable_seed("social:%s" % project)),
            '<rect width="%s" height="%s" filter="url(#gr)" opacity="%s"/>'
            % (W, H, GRAIN["dark"]),
        ])
    body.extend([
        '<rect y="%s" width="%s" height="8" fill="%s"/>' % (H - 8, W, rail),
        '<g transform="translate(%s,110) scale(%.4f)">%s</g>'
        % ((W - mark_h) / 2, mark_h / 96.0, mark),
        '<g fill="%s" transform="translate(%s,505) scale(%.4f)">%s</g>'
        % (p["ink"], (W - tw * ts) / 2, ts, "".join(paths)),
    ])
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s">%s</svg>'
            % (W, H, "".join(body)))

def render_with_grain(foreground_svg, path, W, H, theme, seed_key):
    """Raster parity: canonical ground, grain, then untouched foreground."""
    img = Image.new("RGBA", (W, H), hex_rgb(PAL[theme]["page"]) + (255,))
    img.alpha_composite(grain_overlay((W, H), GRAIN[theme], seed_key))
    img.alpha_composite(png_bytes_to_img(svg_to_png(foreground_svg, W, H)))
    img.convert("RGB").save(path)

# icon tiles ----------------------------------------------------------------

def tile_svg(project, px, radius_pct=0.225, scale=0.62, square=False):
    variant = variant_for(int(px * scale))
    m = MARKS[project]
    mark = "".join(el_svg(e, "dark", m["cat"]) for e in m[variant])
    r = 0 if square else 96 * radius_pct
    inner = 96 * scale
    off = (96 - inner) / 2
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96">'
            '<rect width="96" height="96" rx="%s" fill="%s"/>'
            '<g transform="translate(%s,%s) scale(%.4f)">%s</g></svg>'
            % (r, PAL["dark"]["page"], off, off, inner / 96.0, mark))


def pwa_icon_svg(project, px, maskable=False):
    """Return an opaque PWA tile; maskable art stays inside the 80% safe circle."""
    scale = 0.54 if maskable else 0.62
    return tile_svg(project, px, scale=scale, square=True)

IOS_ICONS = [
    ("iphone", 20, [2, 3]), ("iphone", 29, [2, 3]), ("iphone", 40, [2, 3]),
    ("iphone", 60, [2, 3]), ("ipad", 20, [1, 2]), ("ipad", 29, [1, 2]),
    ("ipad", 40, [1, 2]), ("ipad", 76, [1, 2]), ("ipad", 83.5, [2]),
    ("ios-marketing", 1024, [1]),
]
WATCH_ICONS = [
    ("watch", 24, [2], "notificationCenter", "38mm"),
    ("watch", 27.5, [2], "notificationCenter", "42mm"),
    ("watch", 33, [2], "notificationCenter", "45mm"),
    ("watch", 29, [2, 3], "companionSettings", None),
    ("watch", 40, [2], "appLauncher", "38mm"),
    ("watch", 44, [2], "appLauncher", "40mm"),
    ("watch", 46, [2], "appLauncher", "41mm"),
    ("watch", 50, [2], "appLauncher", "44mm"),
    ("watch", 51, [2], "appLauncher", "45mm"),
    ("watch", 54, [2], "appLauncher", "49mm"),
    ("watch", 86, [2], "quickLook", "38mm"),
    ("watch", 98, [2], "quickLook", "42mm"),
    ("watch", 108, [2], "quickLook", "44mm"),
    ("watch", 117, [2], "quickLook", "45mm"),
    ("watch", 129, [2], "quickLook", "49mm"),
    ("watch-marketing", 1024, [1], None, None),
]

def write_appiconset(project, folder, entries, watch=False):
    os.makedirs(folder, exist_ok=True)
    images = []
    for entry in entries:
        idiom, pt, scales = entry[0], entry[1], entry[2]
        role, subtype = (entry[3], entry[4]) if watch else (None, None)
        for sc in scales:
            px = int(round(pt * sc))
            name = "icon-%s@%sx.png" % (str(pt).replace(".0", ""), sc)
            square = idiom in ("ios-marketing", "watch-marketing")
            svg = tile_svg(project, px, square=square)
            img = png_bytes_to_img(svg_to_png(svg, px))
            if square:
                img = img.convert("RGB")
            img.save(os.path.join(folder, name))
            rec = {"idiom": idiom, "size": "%sx%s" % (pt, pt),
                   "scale": "%sx" % sc, "filename": name}
            if role:
                rec["role"] = role
            if subtype:
                rec["subtype"] = subtype
            images.append(rec)
    with open(os.path.join(folder, "Contents.json"), "w") as f:
        json.dump({"images": images,
                   "info": {"version": 1, "author": "generate_marks.py"}}, f, indent=2)

def mono_mark_png(project, px, color=(0, 0, 0, 255), pad_pct=0.08):
    inner = int(px * (1 - 2 * pad_pct))
    svg = mark_svg(project, variant_for(inner), "dark", mono="#000000")
    img = png_bytes_to_img(svg_to_png(svg, inner))
    r, g, b, a = img.split()
    solid = Image.new("RGBA", img.size, color)
    solid.putalpha(a)
    out = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    out.paste(solid, ((px - inner) // 2, (px - inner) // 2), solid)
    return out

# contact sheet -------------------------------------------------------------

def contact_sheet(project, pdir):
    from PIL import ImageDraw
    disp = MARKS[project].get("display", project)
    cell, pad = 220, 24
    cols = 4
    items = [(p, l) for p, l in [
        (os.path.join(pdir, "png", "mark-512-page.png"), "master dark"),
        (os.path.join(pdir, "png", "mark-512-paper.png"), "master light"),
        (os.path.join(pdir, "macos", "AppIcon.iconset", "icon_512x512.png"), "app icon"),
        (os.path.join(pdir, "web", "social-preview-1280x640.png"), "social"),
        (os.path.join(pdir, "web", "banner-dark-1400x400.png"), "banner dark"),
        (os.path.join(pdir, "web", "banner-light-1400x400.png"), "banner light"),
        (os.path.join(pdir, "wordmark", "wordmark-horizontal-dark.png"), "wordmark"),
        (os.path.join(pdir, "png", "mark-16.png"), "16 px actual"),
    ] if os.path.exists(p)]
    rows = math.ceil(len(items) / cols)
    W = cols * cell + (cols + 1) * pad
    H = rows * cell + rows * 30 + (rows + 1) * pad + 40
    sheet = Image.new("RGB", (W, H), (23, 22, 20))
    d = ImageDraw.Draw(sheet)
    for i, (path, label) in enumerate(items):
        cx = pad + (i % cols) * (cell + pad)
        cy = pad + (i // cols) * (cell + pad + 30)
        im = Image.open(path).convert("RGBA")
        if label == "16 px actual":
            canvas = Image.new("RGBA", (cell, cell), (11, 12, 13, 255))
            big = im.resize((160, 160), Image.NEAREST)
            canvas.paste(big, ((cell - 160) // 2, 10), big)
            canvas.paste(im, ((cell - 16) // 2, 186), im)
            im = canvas
        else:
            im.thumbnail((cell, cell))
            canvas = Image.new("RGBA", (cell, cell), (32, 30, 27, 255))
            canvas.paste(im, ((cell - im.width) // 2, (cell - im.height) // 2), im)
            im = canvas
        sheet.paste(im.convert("RGB"), (cx, cy))
        d.text((cx + 4, cy + cell + 6), label, fill=(143, 140, 133))
    d.text((pad, H - 34), disp + "  .  ink and bone", fill=(243, 241, 235))
    out = os.path.join(pdir, "contact-sheet-%s.png" % disp)
    sheet.save(out)
    old = os.path.join(pdir, "contact-sheet.png")
    if os.path.exists(old):
        try:
            os.remove(old)
        except OSError:
            sheet.save(old)
    return out


def alpha_metrics(image):
    alpha = image.convert("RGBA").getchannel("A")
    w, h = alpha.size
    values = alpha.load()
    edge = {
        "left": max(values[0, y] for y in range(h)),
        "right": max(values[w - 1, y] for y in range(h)),
        "top": max(values[x, 0] for x in range(w)),
        "bottom": max(values[x, h - 1] for x in range(w)),
    }
    strong = alpha.point(lambda value: 255 if value >= 128 else 0)
    bbox = strong.getbbox()
    margins = None
    if bbox:
        margins = {"left": bbox[0], "top": bbox[1],
                   "right": w - bbox[2], "bottom": h - bbox[3]}
    return {
        "edgeAlphaMax": {side: round(value / 255, 3) for side, value in edge.items()},
        "threshold128Bounds": list(bbox) if bbox else None,
        "threshold128Margins": margins,
        "pass": max(edge.values()) < 128 and
                (margins is None or min(margins.values()) >= 1),
    }


def small_mark_image(project, px, treatment):
    if treatment == "dark":
        svg = mark_svg(project, variant_for(px), "dark")
    elif treatment == "light":
        svg = mark_svg(project, variant_for(px), "light")
    elif treatment == "mono":
        svg = mark_svg(project, variant_for(px), "light", mono="#000000")
    else:
        raise ValueError("unknown small-mark treatment %r" % treatment)
    return png_bytes_to_img(svg_to_png(svg, px))


def build_small_mark_qa(qdir):
    from PIL import ImageDraw
    projects = list(PUBLIC_MARKS)
    treatments = ((16, "dark"), (16, "light"), (16, "mono"),
                  (24, "dark"), (24, "light"), (24, "mono"))
    label_w, cell_w, row_h, header = 210, 176, 92, 52
    sheet = Image.new("RGB", (label_w + cell_w * len(treatments),
                              header + row_h * len(projects)), (32, 30, 27))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 18), "small-mark family QA", fill=hex_rgb(PAL["dark"]["ink"]))
    for column, (px, treatment) in enumerate(treatments):
        draw.text((label_w + column * cell_w + 10, 18),
                  "%spx %s" % (px, treatment), fill=hex_rgb(PAL["dark"]["quiet"]))
    report = {"alphaThreshold": 128, "minimumStrongAlphaMarginPx": 1,
              "projects": {}}
    failures = []
    for row, project in enumerate(projects):
        y = header + row * row_h
        mark = MARKS[project]
        draw.text((16, y + 36), "%s  [%s]" % (project, mark["id"]),
                  fill=hex_rgb(PAL["dark"]["ink"]))
        report["projects"][project] = {"id": mark["id"], "sizes": {}}
        for column, (px, treatment) in enumerate(treatments):
            x = label_w + column * cell_w
            ground = (PAL["dark"]["page"] if treatment == "dark" else
                      PAL["light"]["page"] if treatment == "light" else "#FFFFFF")
            draw.rectangle((x, y, x + cell_w - 1, y + row_h - 1),
                           fill=hex_rgb(ground))
            image = small_mark_image(project, px, treatment)
            actual_x, actual_y = x + 14, y + (row_h - px) // 2
            sheet.paste(image, (actual_x, actual_y), image)
            zoom = 3 if px == 24 else 4
            enlarged = image.resize((px * zoom, px * zoom), Image.Resampling.NEAREST)
            sheet.paste(enlarged,
                        (x + 62, y + (row_h - enlarged.height) // 2), enlarged)
            metrics = alpha_metrics(image)
            report["projects"][project]["sizes"].setdefault(str(px), {})[
                treatment] = metrics
            if not metrics["pass"]:
                failures.append("%s %spx %s" % (project, px, treatment))
    sheet.save(os.path.join(qdir, "small-marks-16-24-qa.png"))
    with open(os.path.join(qdir, "small-marks-16-24-qa.json"), "w",
              encoding="utf-8") as report_file:
        json.dump(report, report_file, indent=2)
        report_file.write("\n")
    if failures:
        raise ValueError("small-mark safe-area gate failed (alpha >= 128 at edge or "
                         "under 1px margin): %s" % ", ".join(failures))


def build_wordmark_minimum_qa(qdir):
    from PIL import ImageDraw
    projects = [name for name, mark in PUBLIC_MARKS.items()
                if not mark.get("no_wordmark")]
    policy = BRAND["xHeightPolicy"]
    standard = float(policy["screenStandardPx"])
    controlled = float(policy["screenAbsoluteControlledPx"])
    source_xheight = (float(BRAND["display"]["xHeight"]) * 100 /
                      float(BRAND["display"]["unitsPerEm"]))
    columns = (("dark", "page"), ("dark", "card"),
               ("light", "page"), ("light", "card"))
    label_w, cell_w, row_h, header = 210, 380, 76, 76
    sheet = Image.new("RGB", (label_w + cell_w * len(columns),
                              header + row_h * len(projects)), (32, 30, 27))
    draw = ImageDraw.Draw(sheet)
    draw.text((16, 12), "wordmark minimum QA - %.0fpx rendered x-height" % standard,
              fill=hex_rgb(PAL["dark"]["ink"]))
    for column, (theme, surface) in enumerate(columns):
        draw.text((label_w + column * cell_w + 10, 44), "%s %s" % (theme, surface),
                  fill=hex_rgb(PAL["dark"]["quiet"]))
    records = []
    for row, project in enumerate(projects):
        source_svg, width, height = wordmark_svg(project, "dark", "horizontal")
        del source_svg
        scale = standard / source_xheight
        standard_width = math.ceil(width * scale)
        controlled_width = math.ceil(width * controlled / source_xheight)
        rendered_height = max(1, math.ceil(height * scale))
        record = {
            "id": MARKS[project]["id"],
            "lockup": project,
            "sourceRenderedWidthPx": round(width, 3),
            "sourceRenderedXHeightPx": round(source_xheight, 3),
            "standardMinimumWidthPx": standard_width,
            "controlledMinimumWidthPx": controlled_width,
        }
        records.append(record)
        y = header + row * row_h
        draw.text((16, y + 30), "%s  %spx" % (project, standard_width),
                  fill=hex_rgb(PAL["dark"]["ink"]))
        for column, (theme, surface) in enumerate(columns):
            x = label_w + column * cell_w
            ground = PAL[theme][surface]
            draw.rectangle((x, y, x + cell_w - 1, y + row_h - 1),
                           fill=hex_rgb(ground))
            svg, _, _ = wordmark_svg(project, theme, "horizontal")
            image = png_bytes_to_img(svg_to_png(svg, standard_width, rendered_height))
            sheet.paste(image, (x + 12, y + (row_h - rendered_height) // 2), image)
    target_name = ("wordmark-minimums-%spx-xheight.png" %
                   (int(standard) if standard.is_integer() else standard))
    sheet.save(os.path.join(qdir, target_name))
    metadata = {
        "policySource": os.path.relpath(TOKEN_PATH, HERE),
        "screenStandardPx": standard,
        "screenAbsoluteControlledPx": controlled,
        "printStandardMm": float(policy["printStandardMm"]),
        "records": records,
    }
    with open(os.path.join(qdir, "wordmark-minimums.json"), "w",
              encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, indent=2)
        metadata_file.write("\n")


def build_public_manifest(qdir):
    records = []
    for slug, mark in PUBLIC_MARKS.items():
        records.append({"id": mark["id"], "slug": slug,
                        "aliases": mark["aliases"],
                        "display": mark.get("display", slug),
                        "category": mark["cat"]})
    with open(os.path.join(qdir, "public-projects.json"), "w",
              encoding="utf-8") as manifest_file:
        json.dump({"projects": records}, manifest_file, indent=2)
        manifest_file.write("\n")


def build_qa(out_root=OUT):
    qdir = os.path.join(out_root, "qa")
    os.makedirs(qdir, exist_ok=True)
    build_small_mark_qa(qdir)
    build_wordmark_minimum_qa(qdir)
    build_public_manifest(qdir)
    print("  built public QA -> %s" % os.path.relpath(qdir, HERE))
    return qdir

# main build ----------------------------------------------------------------

PNG_SIZES = [1024, 512, 256, 128, 64, 48, 32, 24, 16]

def build(project, out_root=OUT):
    m = MARKS[project]
    pdir = os.path.join(out_root, "private" if m.get("private_overlay") else "",
                        project)
    for sub in ("svg", "pdf", "png", "jpeg", "wordmark", "macos", "ios",
                "watchos", "web", "appstore"):
        os.makedirs(os.path.join(pdir, sub), exist_ok=True)

    sv = os.path.join(pdir, "svg")
    files = {
        "mark.svg": mark_svg(project, "master", "dark"),
        "mark-light.svg": mark_svg(project, "master", "light"),
        "mark-24.svg": mark_svg(project, "s24", "dark", size=24),
        "mark-24-light.svg": mark_svg(project, "s24", "light", size=24),
        "mark-16.svg": mark_svg(project, "s16", "dark", size=16),
        "mark-16-light.svg": mark_svg(project, "s16", "light", size=16),
        "mark-mono.svg": mark_svg(project, "master", "dark", mono="#000000"),
    }
    for name, svg in files.items():
        with open(os.path.join(sv, name), "w", encoding="utf-8") as f:
            f.write(svg)

    svg_to_pdf(files["mark-light.svg"], os.path.join(pdir, "pdf", "mark.pdf"))
    svg_to_pdf(files["mark.svg"], os.path.join(pdir, "pdf", "mark-dark.pdf"))

    for px in PNG_SIZES:
        v = variant_for(px)
        save_png(mark_svg(project, v, "dark"),
                 os.path.join(pdir, "png", "mark-%s.png" % px), px)
        save_png(mark_svg(project, v, "light"),
                 os.path.join(pdir, "png", "mark-light-%s.png" % px), px)
        save_png(mark_svg(project, v, "dark", ground=PAL["dark"]["page"]),
                 os.path.join(pdir, "png", "mark-%s-page.png" % px), px)
        save_png(mark_svg(project, v, "light", ground=PAL["light"]["page"]),
                 os.path.join(pdir, "png", "mark-%s-paper.png" % px), px)
    gate_failures = []
    for px in (16, 24):
        for theme, filename in (("dark", "mark-%s.png" % px),
                                ("light", "mark-light-%s.png" % px)):
            metrics = alpha_metrics(Image.open(os.path.join(pdir, "png", filename)))
            if not metrics["pass"]:
                gate_failures.append("%spx %s %s" %
                                     (px, theme, metrics["edgeAlphaMax"]))
    if gate_failures:
        raise ValueError("%s small-mark safe-area gate failed: %s" %
                         (project, "; ".join(gate_failures)))
    for px in (1024, 512):
        for gname, theme in (("page", "dark"), ("paper", "light")):
            img = png_bytes_to_img(svg_to_png(
                mark_svg(project, "master", theme, ground=PAL[theme]["page"]), px))
            img.convert("RGB").save(
                os.path.join(pdir, "jpeg", "mark-%s-%s.jpg" % (px, gname)), quality=92)

    if not m.get("no_wordmark"):
        for layout in ("horizontal", "stacked"):
            for theme in ("dark", "light"):
                svg, W, H = wordmark_svg(project, theme, layout)
                base = os.path.join(pdir, "wordmark",
                                    "wordmark-%s-%s" % (layout, theme))
                with open(base + ".svg", "w", encoding="utf-8") as f:
                    f.write(svg)
                svg_to_pdf(svg, base + ".pdf")
                save_png(svg, base + ".png", int(W * 2), int(H * 2))

    iconset = os.path.join(pdir, "macos", "AppIcon.iconset")
    os.makedirs(iconset, exist_ok=True)
    for pt in (16, 32, 128, 256, 512):
        for sc in (1, 2):
            px = pt * sc
            suffix = "" if sc == 1 else "@2x"
            save_png(tile_svg(project, px),
                     os.path.join(iconset, "icon_%sx%s%s.png" % (pt, pt, suffix)), px)
    try:
        import icnsutil
        icns = icnsutil.IcnsFile()
        for fn in sorted(os.listdir(iconset)):
            icns.add_media(file=os.path.join(iconset, fn))
        icns.write(os.path.join(pdir, "macos", "AppIcon.icns"))
    except Exception as ex:
        raise RuntimeError("%s ICNS generation failed; no partial target will be "
                           "installed: %s" % (project, ex)) from ex

    for sc, px in ((1, 22), (2, 44), (3, 66)):
        suffix = "" if sc == 1 else "@%sx" % sc
        mono_mark_png(project, px).save(
            os.path.join(pdir, "macos", "%s-template%s.png" % (project, suffix)))

    write_appiconset(project, os.path.join(pdir, "ios", "AppIcon.appiconset"), IOS_ICONS)
    save_png(tile_svg(project, 180), os.path.join(pdir, "ios", "apple-touch-icon.png"), 180)
    write_appiconset(project, os.path.join(pdir, "watchos", "AppIcon.appiconset"),
                     WATCH_ICONS, watch=True)
    comp = os.path.join(pdir, "watchos", "complications")
    os.makedirs(comp, exist_ok=True)
    for name, px in (("circular@2x", 72), ("extra-large@2x", 224),
                     ("graphic-corner@2x", 80), ("graphic-circular@2x", 94)):
        mono_mark_png(project, px, color=(255, 255, 255, 255)).save(
            os.path.join(comp, "complication-%s.png" % name))

    web = os.path.join(pdir, "web")
    with open(os.path.join(web, "favicon.svg"), "w", encoding="utf-8") as f:
        f.write(favicon_svg(project))
    icons = [png_bytes_to_img(svg_to_png(mark_svg(project, variant_for(px), "dark"), px))
             for px in (48, 32, 16)]
    icons[0].save(os.path.join(web, "favicon.ico"), sizes=[(48, 48), (32, 32), (16, 16)],
                  append_images=icons[1:])
    for px in (192, 512):
        save_png(pwa_icon_svg(project, px),
                 os.path.join(web, "icon-%s.png" % px), px)
    save_png(pwa_icon_svg(project, 512, maskable=True),
             os.path.join(web, "icon-512-maskable.png"), 512)
    if not m.get("no_wordmark"):
        for theme in ("dark", "light"):
            bsvg = banner_svg(project, theme)
            with open(os.path.join(web, "banner-%s-1400x400.svg" % theme), "w",
                      encoding="utf-8") as f:
                f.write(bsvg)
            render_with_grain(
                banner_svg(project, theme, with_ground=False),
                os.path.join(web, "banner-%s-1400x400.png" % theme),
                1400, 400, theme, "banner:%s:%s" % (project, theme))
        ssvg = social_svg(project)
        with open(os.path.join(web, "social-preview-1280x640.svg"), "w",
                  encoding="utf-8") as f:
            f.write(ssvg)
        render_with_grain(
            social_svg(project, with_ground=False),
            os.path.join(web, "social-preview-1280x640.png"),
            1280, 640, "dark", "social:%s" % project)

    img = png_bytes_to_img(svg_to_png(tile_svg(project, 1024, square=True), 1024))
    img.convert("RGB").save(os.path.join(pdir, "appstore", "AppStore-1024.png"))

    sheet = contact_sheet(project, pdir)
    print("  built %s -> %s" % (project, os.path.relpath(pdir, HERE)))
    return sheet


def validate_font_files():
    if not os.path.isfile(FONT_PATH):
        raise FileNotFoundError("canonical display TTF is missing: %s" % FONT_PATH)
    display_font = font()
    actual_upem = display_font["head"].unitsPerEm
    expected_upem = int(BRAND["display"]["unitsPerEm"])
    if actual_upem != expected_upem:
        raise ValueError("display font unitsPerEm %s disagrees with token %s" %
                         (actual_upem, expected_upem))
    actual_xheight = getattr(display_font["OS/2"], "sxHeight", 0)
    expected_xheight = int(BRAND["display"]["xHeight"])
    if actual_xheight and actual_xheight != expected_xheight:
        raise ValueError("display font x-height %s disagrees with token %s" %
                         (actual_xheight, expected_xheight))
    for weight in BRAND["ui"]["weights"]:
        ui_font(weight)


def target_destination(target):
    if target == "avatar":
        return os.path.join(OUT, "github", "avatar")
    if target == "qa":
        return os.path.join(OUT, "qa")
    mark = MARKS[target]
    return os.path.join(OUT, "private" if mark.get("private_overlay") else "", target)


def transactional_commit_dir(staged, destination, extra_files=()):
    """Install one complete target, restoring prior output on any commit error."""
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    transaction_id = uuid.uuid4().hex
    prepared = []
    for source, dest in extra_files:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix=".generated-", dir=os.path.dirname(dest))
        os.close(fd)
        shutil.copy2(source, temp_path)
        prepared.append((temp_path, dest, None))
    directory_backup = None
    installed_directory = False
    installed_files = []
    try:
        if os.path.exists(destination):
            directory_backup = destination + ".backup-" + transaction_id
            os.replace(destination, directory_backup)
        os.replace(staged, destination)
        installed_directory = True
        for temp_path, dest, _ in prepared:
            backup = None
            if os.path.exists(dest):
                backup = dest + ".backup-" + transaction_id
                os.replace(dest, backup)
            try:
                os.replace(temp_path, dest)
            except Exception:
                if backup:
                    os.replace(backup, dest)
                raise
            installed_files.append((dest, backup))
    except Exception:
        for dest, backup in reversed(installed_files):
            if os.path.exists(dest):
                os.remove(dest)
            if backup and os.path.exists(backup):
                os.replace(backup, dest)
        if installed_directory and os.path.exists(destination):
            shutil.rmtree(destination)
        if directory_backup and os.path.exists(directory_backup):
            os.replace(directory_backup, destination)
        raise
    else:
        if directory_backup and os.path.exists(directory_backup):
            shutil.rmtree(directory_backup)
        for _, backup in installed_files:
            if backup and os.path.exists(backup):
                os.remove(backup)
    finally:
        for temp_path, _, _ in prepared:
            if os.path.exists(temp_path):
                os.remove(temp_path)


def build_transaction(target):
    with tempfile.TemporaryDirectory(prefix=".generate-marks-", dir=HERE) as temp_dir:
        stage_root = os.path.join(temp_dir, "out")
        if target == "avatar":
            staged = build_avatar(stage_root)
            github_dir = os.path.join(BRAND_DIR, "..", "github")
            extras = []
            for theme in ("dark", "light"):
                extras.extend([
                    (os.path.join(staged, "avatar-%s.svg" % theme),
                     os.path.join(github_dir, "avatar-%s.svg" % theme)),
                    (os.path.join(staged, "avatar-%s-460.png" % theme),
                     os.path.join(github_dir, "avatar-%s-460.png" % theme)),
                ])
        elif target == "qa":
            staged = build_qa(stage_root)
            extras = []
        else:
            build(target, stage_root)
            staged = os.path.join(stage_root,
                                  "private" if MARKS[target].get("private_overlay") else "",
                                  target)
            extras = []
        transactional_commit_dir(staged, target_destination(target), extras)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Generate Ink and Bone public marks transactionally.")
    parser.add_argument("targets", nargs="*",
                        help="canonical project slug, declared alias, avatar, or qa")
    parser.add_argument("--private-overlay", action="append", default=[], metavar="PATH",
                        help="explicit private registry; repeat for multiple overlays")
    parser.add_argument("--include-private", action="store_true",
                        help="allow explicitly supplied private overlays")
    parser.add_argument("--include-retired", action="store_true",
                        help="allow retired entries from explicit private overlays")
    parser.add_argument("--list-targets", action="store_true",
                        help="list targets visible under the supplied guards and exit")
    parser.add_argument("--validate-only", action="store_true",
                        help="validate tokens, fonts, registries, aliases and guards; do not build")
    args = parser.parse_args(argv)
    if args.private_overlay and not args.include_private:
        parser.error("--private-overlay requires --include-private")
    if args.include_private and not args.private_overlay:
        parser.error("--include-private requires at least one --private-overlay PATH")
    if args.include_retired and not args.include_private:
        parser.error("--include-retired requires --include-private and an explicit overlay")
    return parser, args


def main(argv=None):
    global MARKS
    parser, args = parse_args(argv)
    try:
        MARKS = (load_private_overlays(args.private_overlay)
                 if args.include_private else dict(PUBLIC_MARKS))
        validate_registry(MARKS, mixed=args.include_private)
        validate_font_files()
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    aliases = alias_map(MARKS)
    available_private = [name for name, mark in MARKS.items()
                         if mark.get("private_overlay") and
                         (args.include_retired or not mark.get("retired"))]
    if args.list_targets:
        for name in PUBLIC_MARKS:
            print(name)
        print("avatar")
        print("qa")
        for name in available_private:
            print(name)
        return 0

    if args.targets:
        targets = []
        for supplied in args.targets:
            if supplied in RESERVED_TARGETS:
                canonical = supplied
            elif supplied in aliases:
                canonical = aliases[supplied]
            else:
                parser.error("unknown target %r" % supplied)
            if canonical in MARKS and MARKS[canonical].get("retired") and \
                    not args.include_retired:
                parser.error("retired private target %r requires --include-retired" % supplied)
            if canonical not in targets:
                targets.append(canonical)
    else:
        targets = list(PUBLIC_MARKS) + ["avatar", "qa"] + available_private

    if args.validate_only:
        print("validated canonical tokens, fonts, %s public marks%s" %
              (len(PUBLIC_MARKS),
               " and %s guarded private marks" % len(available_private)
               if args.include_private else ""))
        return 0
    os.makedirs(OUT, exist_ok=True)
    for target in targets:
        build_transaction(target)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
