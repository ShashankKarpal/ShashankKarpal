#!/usr/bin/env python3
"""Verify Ink and Bone's canonical tokens and normative WCAG role pairs.

The release gate reads brand-tokens.json. It checks source-to-CSS parity and
the contrast pairs required by each semantic role. Colour-vision-deficiency
(CVD) output is advisory: simulation and colour-distance heuristics are not
WCAG conformance tests and never affect this program's exit status.

Run:
    python3 verify-palette.py
    python3 verify-palette.py -v
    python3 verify-palette.py --self-test
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import re
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
DEFAULT_TOKENS = HERE / "brand-tokens.json"
DEFAULT_CSS = HERE / "brand-tokens.css"
DEFAULT_GUIDE = HERE / "shanky-brand-guide.html"

MIN_TEXT = 4.5
MIN_NON_TEXT = 3.0
META_TOLERANCE = 0.015

# Severity 1.0 matrices published with Machado, Oliveira and Fernandes,
# "A Physiologically-based Model for Simulation of Color Vision Deficiency",
# IEEE TVCG 15(6), 2009, DOI 10.1109/TVCG.2009.113.
# Supplementary table:
# https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/CVD_Simulation.html
#
# The paper validates the protan/deutan model. It explicitly says its
# replacement model is not intended to handle tritanopia; the supplementary
# tritanomaly matrix is therefore reported separately and especially
# cautiously. None of these matrices is used as a release gate.
CVD_MATRICES = {
    "protan severity 1.0": (
        (0.152286, 1.052583, -0.204868),
        (0.114503, 0.786281, 0.099216),
        (-0.003882, -0.048116, 1.051998),
    ),
    "deutan severity 1.0": (
        (0.367322, 0.860646, -0.227968),
        (0.280085, 0.672501, 0.047413),
        (-0.011820, 0.042940, 0.968881),
    ),
    "tritanomaly severity 1.0 (provisional)": (
        (1.255528, -0.076749, -0.178779),
        (-0.078411, 0.930809, 0.147602),
        (0.004733, 0.691367, 0.303900),
    ),
}

CATEGORY = ("copper", "brass", "mist")
STATUS = ("good", "watch", "problem", "info", "neutral")
SURFACES = ("page", "card", "raised")

CSS_TOKEN_PATHS = {
    "page": ("surface", "page"),
    "card": ("surface", "card"),
    "raised": ("surface", "raised"),
    "edge": ("surface", "edge"),
    "edge-strong": ("surface", "edgeStrong"),
    "control-border": ("surface", "controlBorder"),
    "state-indicator": ("surface", "stateIndicator"),
    "text": ("text", "primary"),
    "text-quiet": ("text", "quiet"),
    "link": ("utility", "link"),
    "cat-copper": ("category", "copper"),
    "cat-brass": ("category", "brass"),
    "cat-mist": ("category", "mist"),
    "st-good": ("status", "good"),
    "st-watch": ("status", "watch"),
    "st-problem": ("status", "problem"),
    "st-info": ("status", "info"),
    "st-neutral": ("status", "neutral"),
    "label-on-fill": ("utility", "labelOnFill"),
    "focus": ("utility", "focus"),
}


def hex_to_srgb(value: str) -> tuple[float, float, float]:
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        raise ValueError(f"invalid six-digit hex colour: {value!r}")
    return tuple(int(value[i : i + 2], 16) / 255.0 for i in (1, 3, 5))


def srgb_to_linear(channel: float) -> float:
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(value: str) -> float:
    red, green, blue = (srgb_to_linear(c) for c in hex_to_srgb(value))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(first: str, second: str) -> float:
    one, two = relative_luminance(first), relative_luminance(second)
    return (max(one, two) + 0.05) / (min(one, two) + 0.05)


def multiply(matrix, vector):
    return tuple(sum(matrix[row][column] * vector[column] for column in range(3)) for row in range(3))


def simulate_linear(value: str, matrix) -> tuple[float, float, float]:
    """Return displayable linear-light sRGB without 8-bit quantisation."""
    linear = tuple(srgb_to_linear(c) for c in hex_to_srgb(value))
    transformed = multiply(matrix, linear)
    return tuple(max(0.0, min(1.0, channel)) for channel in transformed)


def linear_rgb_to_lab(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    red, green, blue = rgb
    x = red * 0.4124564 + green * 0.3575761 + blue * 0.1804375
    y = red * 0.2126729 + green * 0.7151522 + blue * 0.0721750
    z = red * 0.0193339 + green * 0.1191920 + blue * 0.9503041

    def pivot(component: float) -> float:
        delta = 6 / 29
        return component ** (1 / 3) if component > delta**3 else component / (3 * delta**2) + 4 / 29

    fx, fy, fz = pivot(x / 0.95047), pivot(y), pivot(z / 1.08883)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e_76(first: tuple[float, float, float], second: tuple[float, float, float]) -> float:
    lab_one, lab_two = linear_rgb_to_lab(first), linear_rgb_to_lab(second)
    return math.sqrt(sum((lab_one[i] - lab_two[i]) ** 2 for i in range(3)))


def token_hex(theme: dict, section: str, name: str) -> str:
    return theme[section][name]["hex"]


def load_tokens(path: Path) -> dict:
    with path.open(encoding="utf-8") as source:
        tokens = json.load(source)
    for theme_name in ("dark", "light"):
        if theme_name not in tokens.get("color", {}):
            raise ValueError(f"missing color.{theme_name} in {path}")
    return tokens


def check_ratio(label: str, foreground: str, background: str, minimum: float, failures: list[str]) -> float:
    measured = contrast(foreground, background)
    result = "ok" if measured + 1e-12 >= minimum else "FAIL"
    print(f"  {label:<46} {measured:6.3f}  >= {minimum:.1f}  {result}")
    if result == "FAIL":
        failures.append(f"{label}: {measured:.3f}, requires {minimum:.1f}")
    return measured


def verify_stored_ratios(theme_name: str, theme: dict, failures: list[str]) -> None:
    page = token_hex(theme, "surface", "page")
    for section in ("text", "category", "status"):
        for name, record in theme[section].items():
            if "contrastOnPage" not in record:
                continue
            actual = contrast(record["hex"], page)
            if abs(actual - float(record["contrastOnPage"])) > META_TOLERANCE:
                failures.append(
                    f"{theme_name}.{section}.{name}.contrastOnPage stores "
                    f"{record['contrastOnPage']}, computed {actual:.3f}"
                )
    for section in ("surface", "utility"):
        for name, record in theme[section].items():
            if not isinstance(record, dict) or "contrast" not in record or "hex" not in record:
                continue
            for surface_name, stored in record["contrast"].items():
                actual = contrast(record["hex"], token_hex(theme, "surface", surface_name))
                if abs(actual - float(stored)) > META_TOLERANCE:
                    failures.append(
                        f"{theme_name}.{section}.{name}.contrast.{surface_name} stores "
                        f"{stored}, computed {actual:.3f}"
                    )


def css_blocks(css: str, selector: str) -> list[str]:
    """Return the bodies of exact selector blocks, including nested-media blocks."""
    pattern = re.compile(rf"(?m)^\s*{re.escape(selector)}\s*\{{")
    bodies = []
    for match in pattern.finditer(css):
        depth = 1
        position = match.end()
        body_start = position
        while position < len(css) and depth:
            if css[position] == "{":
                depth += 1
            elif css[position] == "}":
                depth -= 1
            position += 1
        if depth:
            raise ValueError(f"unclosed CSS block for {selector}")
        bodies.append(css[body_start : position - 1])
    return bodies


def css_token_block(css: str, selector: str) -> dict[str, str]:
    """Return the unique matching selector block that declares canonical colours."""
    candidates = [body for body in css_blocks(css, selector) if re.search(r"--page\s*:", body)]
    if len(candidates) != 1:
        raise ValueError(
            f"expected one {selector} colour-token block, found {len(candidates)}"
        )
    declarations: dict[str, str] = {}
    for name, value in re.findall(r"--([\w-]+)\s*:\s*(#[0-9A-Fa-f]{6})", candidates[0]):
        declarations[name] = value.upper()
    return declarations


def css_declarations(body: str) -> dict[str, str]:
    """Return ordinary and custom-property declarations from one flat block."""
    declarations: dict[str, str] = {}
    for name, value in re.findall(
        r"(?:^|;)\s*([-\w]+)\s*:\s*([^;{}]+)", body, flags=re.MULTILINE
    ):
        declarations[name] = " ".join(value.split())
    return declarations


def unique_css_declarations(css: str, selector: str) -> dict[str, str]:
    blocks = css_blocks(css, selector)
    if len(blocks) != 1:
        raise ValueError(f"expected one {selector} block, found {len(blocks)}")
    return css_declarations(blocks[0])


def require_declaration(
    declarations: dict[str, str],
    property_name: str,
    expected: str,
    label: str,
    failures: list[str],
) -> None:
    actual = declarations.get(property_name)
    if actual != expected:
        failures.append(
            f"{label} {property_name} is {actual or 'missing'}, expected {expected}"
        )


def verify_css_structure(tokens: dict, css: str, failures: list[str]) -> None:
    """Check the non-colour JSON values that the shared stylesheet implements."""
    screen = tokens["font"]["scale"]["screen"]
    root_blocks = [
        body for body in css_blocks(css, ":root") if re.search(r"--font-ui\s*:", body)
    ]
    if len(root_blocks) != 1:
        failures.append(
            f"CSS expected one :root typography-token block, found {len(root_blocks)}"
        )
        return
    root = css_declarations(root_blocks[0])

    for role in ("h1", "h2", "h3"):
        require_declaration(root, f"--size-{role}", screen[role]["size"], "CSS :root", failures)
        require_declaration(
            root,
            f"--lh-{role}",
            str(screen[role]["lineHeight"]),
            "CSS :root",
            failures,
        )
        rule = unique_css_declarations(css, role)
        require_declaration(rule, "font-size", f"var(--size-{role})", f"CSS {role}", failures)
        require_declaration(rule, "line-height", f"var(--lh-{role})", f"CSS {role}", failures)

    require_declaration(
        unique_css_declarations(css, "h1, h2, h3"),
        "font-weight",
        str(screen["h1"]["weight"]),
        "CSS h1/h2/h3",
        failures,
    )
    require_declaration(
        unique_css_declarations(css, "h3"),
        "font-weight",
        str(screen["h3"]["weight"]),
        "CSS h3",
        failures,
    )

    body = unique_css_declarations(css, "body")
    require_declaration(body, "font-size", "var(--size-body)", "CSS body", failures)
    require_declaration(body, "line-height", "var(--lh-body)", "CSS body", failures)
    require_declaration(root, "--size-body", screen["body"]["size"], "CSS :root", failures)
    require_declaration(
        root, "--lh-body", str(screen["body"]["lineHeight"]), "CSS :root", failures
    )

    padding = tokens["space"]["cardPadding"].split()
    if len(padding) != 2:
        failures.append("JSON space.cardPadding must contain block and inline values")
    else:
        require_declaration(root, "--card-padding-block", padding[0], "CSS :root", failures)
        require_declaration(root, "--card-padding-inline", padding[1], "CSS :root", failures)
    require_declaration(
        unique_css_declarations(css, ".card"),
        "padding",
        "var(--card-padding-block) var(--card-padding-inline)",
        "CSS .card",
        failures,
    )

    for index, pixels in enumerate(tokens["space"]["scale"], start=1):
        require_declaration(root, f"--sp-{index}", f"{pixels}px", "CSS :root", failures)


def verify_guide(tokens: dict, guide_path: Path, failures: list[str]) -> None:
    """Check the guide's executable examples against canonical type and spacing."""
    guide = guide_path.read_text(encoding="utf-8")
    match = re.search(r"<style(?:\s[^>]*)?>(.*?)</style>", guide, flags=re.DOTALL)
    if not match:
        failures.append("Guide has no style block")
        return
    css = re.sub(r"/\*.*?\*/", "", match.group(1), flags=re.DOTALL)
    screen = tokens["font"]["scale"]["screen"]

    for role in ("h1", "h2", "h3"):
        rule = unique_css_declarations(css, role)
        require_declaration(rule, "font-size", screen[role]["size"], f"Guide {role}", failures)
        require_declaration(
            rule, "line-height", str(screen[role]["lineHeight"]), f"Guide {role}", failures
        )
    require_declaration(
        unique_css_declarations(css, "h1,h2,h3"),
        "font-weight",
        str(screen["h1"]["weight"]),
        "Guide h1/h2/h3",
        failures,
    )
    require_declaration(
        unique_css_declarations(css, "h3"),
        "font-weight",
        str(screen["h3"]["weight"]),
        "Guide h3",
        failures,
    )

    body = unique_css_declarations(css, "body")
    require_declaration(body, "font-size", screen["body"]["size"], "Guide body", failures)
    require_declaration(
        body, "line-height", str(screen["body"]["lineHeight"]), "Guide body", failures
    )
    require_declaration(
        unique_css_declarations(css, ".card"),
        "padding",
        tokens["space"]["cardPadding"],
        "Guide .card",
        failures,
    )


def verify_css(tokens: dict, css_path: Path, failures: list[str]) -> None:
    css = re.sub(r"/\*.*?\*/", "", css_path.read_text(encoding="utf-8"), flags=re.DOTALL)
    scopes = {
        "dark default": ("dark", css_token_block(css, ":root")),
        "OS light": ("light", css_token_block(css, ':root:not([data-theme="dark"])')),
        "explicit light": ("light", css_token_block(css, '[data-theme="light"]')),
    }
    for scope_name, (theme_name, declarations) in scopes.items():
        for variable, path in CSS_TOKEN_PATHS.items():
            expected = token_hex(tokens["color"][theme_name], *path).upper()
            actual = declarations.get(variable)
            if actual != expected:
                failures.append(
                    f"CSS {scope_name} --{variable} is {actual or 'missing'}, expected {expected}"
                )

    anchor_match = re.search(r"(?:^|\n)\s*a\s*\{([^}]*)\}", css, flags=re.DOTALL)
    if not anchor_match:
        failures.append("CSS has no global inline-link rule")
    else:
        declarations = anchor_match.group(1)
        if not re.search(r"color\s*:\s*var\(--link\)", declarations):
            failures.append("CSS global link rule does not use --link")
        if not re.search(r"text-decoration\s*:\s*underline", declarations):
            failures.append("CSS global link rule lacks a persistent underline")

    scheme_scopes = {
        "dark default": (":root", "dark"),
        "OS light": (':root:not([data-theme="dark"])', "light"),
        "explicit light": ('[data-theme="light"]', "light"),
        "explicit dark": ('[data-theme="dark"]', "dark"),
    }
    for scope_name, (selector, expected) in scheme_scopes.items():
        if not any(
            re.search(rf"color-scheme\s*:\s*{expected}\b", body)
            for body in css_blocks(css, selector)
        ):
            failures.append(f"CSS {scope_name} does not declare color-scheme: {expected}")

    verify_css_structure(tokens, css, failures)


def verify_wcag(tokens: dict, css_path: Path, guide_path: Path) -> list[str]:
    failures: list[str] = []
    print("NORMATIVE WCAG ROLE CHECKS")
    print("CVD simulation is not part of this release gate.\n")

    for theme_name in ("dark", "light"):
        theme = tokens["color"][theme_name]
        print(f"-- {theme_name} theme --")
        surface_values = {name: token_hex(theme, "surface", name) for name in SURFACES}

        for text_name in ("primary", "quiet"):
            foreground = token_hex(theme, "text", text_name)
            for surface_name, background in surface_values.items():
                check_ratio(f"{text_name} text on {surface_name}", foreground, background, MIN_TEXT, failures)

        link = token_hex(theme, "utility", "link")
        for surface_name, background in surface_values.items():
            check_ratio(f"inline link on {surface_name}", link, background, MIN_TEXT, failures)

        for role in ("controlBorder", "stateIndicator"):
            foreground = token_hex(theme, "surface", role)
            for surface_name, background in surface_values.items():
                check_ratio(f"{role} on {surface_name}", foreground, background, MIN_NON_TEXT, failures)

        focus = token_hex(theme, "utility", "focus")
        for surface_name, background in surface_values.items():
            check_ratio(f"focus ring on {surface_name}", focus, background, MIN_NON_TEXT, failures)

        label = token_hex(theme, "utility", "labelOnFill")
        for section, names in (("category", CATEGORY), ("status", STATUS)):
            for name in names:
                fill = token_hex(theme, section, name)
                check_ratio(f"labelOnFill on {name}", label, fill, MIN_TEXT, failures)
                for surface_name, background in surface_values.items():
                    check_ratio(
                        f"{name} fill on {surface_name}", fill, background, MIN_NON_TEXT, failures
                    )

        verify_stored_ratios(theme_name, theme, failures)
        print()

    verify_css(tokens, css_path, failures)
    verify_guide(tokens, guide_path, failures)
    return failures


def print_cvd_advisory(tokens: dict, verbose: bool) -> None:
    print("ADVISORY CVD SIMULATION, NOT A CONFORMANCE OR RELEASE GATE")
    print("Machado et al. (2009) severity-1 matrices on linear-light sRGB; display gamut clipped once;")
    print("distances are CIE Lab dE76 with no 8-bit quantisation. Threshold words are intentionally absent.\n")

    for theme_name in ("dark", "light"):
        theme = tokens["color"][theme_name]
        colors = {
            name: token_hex(theme, "category", name) for name in CATEGORY
        } | {name: token_hex(theme, "status", name) for name in STATUS}
        print(f"-- {theme_name} theme --")
        for model_name, matrix in CVD_MATRICES.items():
            simulated = {name: simulate_linear(value, matrix) for name, value in colors.items()}
            category_pairs = [
                (f"{first}/{second}", delta_e_76(simulated[first], simulated[second]))
                for first, second in itertools.combinations(CATEGORY, 2)
            ]
            status_pairs = [
                (f"{first}/{second}", delta_e_76(simulated[first], simulated[second]))
                for first, second in itertools.combinations(STATUS, 2)
            ]
            good_problem = delta_e_76(simulated["good"], simulated["problem"])
            category_text = ", ".join(f"{name} {distance:.1f}" for name, distance in category_pairs)
            weakest_status = min(status_pairs, key=lambda item: item[1])
            print(f"  {model_name}: categories {category_text}")
            print(
                f"    weakest status {weakest_status[0]} {weakest_status[1]:.1f}; "
                f"good/problem {good_problem:.1f}"
            )
            if verbose:
                cross = sorted(
                    (
                        (f"{category}/{status}", delta_e_76(simulated[category], simulated[status]))
                        for category in CATEGORY
                        for status in STATUS
                    ),
                    key=lambda item: item[1],
                )
                print(
                    "    three closest cross-role pairs: "
                    + ", ".join(f"{name} {distance:.1f}" for name, distance in cross[:3])
                )
        print()


def self_test() -> None:
    assert abs(contrast("#000000", "#FFFFFF") - 21.0) < 1e-12
    assert abs(contrast("#716D64", "#201E1B") - 3.225476) < 0.000001
    assert abs(contrast("#3A659D", "#EDEBE6") - 4.995932) < 0.000001

    for matrix in CVD_MATRICES.values():
        for row in matrix:
            assert abs(sum(row) - 1.0) < 0.000002
        black = simulate_linear("#000000", matrix)
        white = simulate_linear("#FFFFFF", matrix)
        gray = simulate_linear("#808080", matrix)
        assert max(abs(channel) for channel in black) < 1e-12
        assert max(abs(channel - 1.0) for channel in white) < 0.000002
        assert max(gray) - min(gray) < 0.000001

    protan = CVD_MATRICES["protan severity 1.0"]
    assert all(
        abs(actual - expected) < 1e-12
        for actual, expected in zip(
            simulate_linear("#FF0000", protan), (0.152286, 0.114503, 0.0)
        )
    )
    copper = simulate_linear("#B17E51", protan)
    brass = simulate_linear("#BFB287", protan)
    assert any(abs(channel * 255 - round(channel * 255)) > 0.001 for channel in copper)
    assert abs(delta_e_76(copper, brass) - 18.5515) < 0.001

    tokens = load_tokens(DEFAULT_TOKENS)
    stale_css = DEFAULT_CSS.read_text(encoding="utf-8").replace("#0B0C0D", "#F5F5F3", 1)
    with tempfile.TemporaryDirectory() as directory:
        stale_path = Path(directory) / "stale.css"
        stale_path.write_text(stale_css, encoding="utf-8")
        parity_failures: list[str] = []
        verify_css(tokens, stale_path, parity_failures)
    assert any("dark default --page" in failure for failure in parity_failures)

    stale_type_css = DEFAULT_CSS.read_text(encoding="utf-8").replace(
        "--lh-h2: 1.35", "--lh-h2: 1.3", 1
    )
    with tempfile.TemporaryDirectory() as directory:
        stale_path = Path(directory) / "stale-type.css"
        stale_path.write_text(stale_type_css, encoding="utf-8")
        parity_failures = []
        verify_css(tokens, stale_path, parity_failures)
    assert any("--lh-h2" in failure for failure in parity_failures)

    stale_guide = DEFAULT_GUIDE.read_text(encoding="utf-8").replace(
        "h3{font-size:15px; line-height:1.4", "h3{font-size:15px; line-height:1.3", 1
    )
    with tempfile.TemporaryDirectory() as directory:
        stale_path = Path(directory) / "stale-guide.html"
        stale_path.write_text(stale_guide, encoding="utf-8")
        parity_failures = []
        verify_guide(tokens, stale_path, parity_failures)
    assert any("Guide h3 line-height" in failure for failure in parity_failures)
    print(
        "Self-test passed: contrast fixtures, matrix orientation/invariants, "
        "float precision, CVD regression, and colour/type/spacing parity fixtures."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-v", "--verbose", action="store_true", help="show closest cross-role CVD pairs")
    parser.add_argument("--tokens", type=Path, default=DEFAULT_TOKENS, help="canonical brand-tokens.json")
    parser.add_argument("--css", type=Path, default=DEFAULT_CSS, help="CSS file checked for token parity")
    parser.add_argument(
        "--guide", type=Path, default=DEFAULT_GUIDE, help="brand guide checked for example parity"
    )
    parser.add_argument("--no-cvd", action="store_true", help="skip advisory CVD output")
    parser.add_argument("--self-test", action="store_true", help="run calculation fixtures and exit")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        self_test()
        return 0

    try:
        tokens = load_tokens(args.tokens)
        failures = verify_wcag(tokens, args.css, args.guide)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if not args.no_cvd:
        print_cvd_advisory(tokens, args.verbose)

    if failures:
        print(f"FAILED {len(failures)} normative/source-parity checks:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("All normative WCAG contrast and source-parity checks pass.")
    if not args.no_cvd:
        print("CVD results above are advisory and did not affect this exit status.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
