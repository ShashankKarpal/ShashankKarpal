# Accessibility report

Direction: Ink and Bone, v1.1.0, 2026-08-20.

This report separates normative contrast checks from advisory colour-vision
simulation. They answer different questions and have different confidence.

## Method and release gate

- WCAG contrast uses relative luminance. Normal text and text-like symbols
  require 4.5:1. Meaningful control boundaries, state indicators, focus rings,
  rails and fills require 3:1 against adjacent colours.
- `verify-palette.py` reads `brand-tokens.json`, the canonical source. It does
  not carry a second hardcoded palette.
- The verifier checks primary text, quiet text, inline links, control borders,
  state indicators and focus rings on page, card and raised surfaces in both
  themes. It also checks label-on-fill contrast and category/status fills as
  meaningful non-text elements on all three surfaces.
- It checks each colour variable in the default-dark, OS-light and
  explicit-light scopes, plus the persistent link underline, in
  `brand-tokens.css` against the JSON. A missing, swapped or stale binding fails
  the run.
- Only normative WCAG and source-parity failures produce exit status 1. CVD
  distances are always labelled advisory and never affect the exit status.

## Normative semantic contrast

### Dark theme

| Role | Value | Page `#0B0C0D` | Card `#171614` | Raised `#201E1B` | Requirement |
|---|---|---:|---:|---:|---:|
| Primary text | `#F3F1EB` | 17.33 | 16.01 | 14.72 | 4.5 |
| Quiet text | `#8F8C85` | 5.83 | 5.39 | 4.95 | 4.5 |
| Inline link | `#5E92DC` | 6.17 | 5.70 | 5.24 | 4.5 plus underline |
| controlBorder | `#716D64` | 3.80 | 3.51 | 3.23 | 3.0 |
| stateIndicator | `#9A968C` | 6.63 | 6.13 | 5.63 | 3.0 plus non-colour cue |
| Focus ring | `#CFDFE8` | 14.33 | 13.24 | 12.17 | 3.0 |

### Light theme

| Role | Value | Page `#F5F5F3` | Card `#FFFFFF` | Raised `#EDEBE6` | Requirement |
|---|---|---:|---:|---:|---:|
| Primary text | `#1A1917` | 16.09 | 17.57 | 14.75 | 4.5 |
| Quiet text | `#5A5852` | 6.52 | 7.11 | 5.97 | 4.5 |
| Inline link | `#3A659D` | 5.45 | 5.95 | 5.00 | 4.5 plus underline |
| controlBorder | `#85827B` | 3.51 | 3.83 | 3.22 | 3.0 |
| stateIndicator | `#67645C` | 5.41 | 5.91 | 4.96 | 3.0 plus non-colour cue |
| Focus ring | `#2D647F` | 5.94 | 6.48 | 5.44 | 3.0 |

The lowest passing normative pair is light controlBorder on raised at 3.22:1.
This is enough for the declared non-text role but leaves little room for an
unreviewed colour change, which is why the verifier uses unrounded values.

## Edge and state semantics

`edge` and `edgeStrong` are decorative only. EdgeStrong measures 1.42 to 1.67
against dark surfaces and 1.37 to 1.64 against light surfaces. It cannot be
the only visible boundary of a control or state.

- Inputs, buttons and other required boundaries use `controlBorder`.
- Selected and active states use `stateIndicator` plus an ARIA state and a
  visible non-colour cue such as weight, a check, an icon or a labelled rail.
- Focus uses a 2px focus token ring with a 2px offset.

## Inline links

Inline links use their dedicated `utility.link` token and a persistent
underline. Info remains a status colour for notices and hints, never a link
token. Underline-free navigation is allowed only when the control role is
already explicit, such as a button, tab or navigation item.

The underline is essential. Link colour against surrounding body text is only
2.81:1 in dark and 2.95:1 in light, below the 3:1 colour-only differentiation
test. The persistent underline supplies the non-colour distinction.

## Labels on category and status fills

Dark fills use ink `#0B0C0D`; light fills use white `#FFFFFF`.

| Fill | Dark label ratio | Light label ratio |
|---|---:|---:|
| Copper | 5.57 | 5.12 |
| Brass | 9.26 | 9.80 |
| Mist | 14.33 | 6.48 |
| Good | 9.12 | 5.13 |
| Watch | 10.41 | 7.02 |
| Problem | 4.77 | 5.13 |
| Info | 4.95 | 5.95 |
| Neutral | 5.53 | 10.44 |

Every label-on-fill pair clears 4.5:1. Every category and status fill also
clears 3:1 as a meaningful non-text element against page, card and raised.

Category colour is secondary and never the sole identifier. A visible project
name or mark carries identity. Status occupies a different slot and always
carries a word. Ink is the neutral, unaccented default, not a fourth functional
category; an internal tooling exception can remain ink without changing the
taxonomy.

## Role restrictions that remain important

Category and status colours are not general-purpose body-text colours on every
surface. The following normal-text combinations remain below 4.5:1:

- Dark Problem on card: 4.41:1.
- Dark Problem on raised: 4.06:1.
- Dark Info on raised: 4.21:1.
- Light Copper, Good and Problem on raised: approximately 4.29 to 4.31:1.

Use these colours as tested fills, rails, marks or large text in those
locations. Body copy continues to use primary or quiet text. Inline links use
the dedicated link token.

## Advisory colour-vision-deficiency simulation

The former Viénot-labelled implementation was invalid. It combined an LMS
matrix with coefficients derived for a different matrix, quantised before
distance measurement, silently changed thresholds for one condition, and
incorrectly attributed tritanopia to a paper that did not cover it. Its old
numbers and pass/fail conclusions are retired.

The current advisory implementation uses the severity-1 matrices published
with Machado, Oliveira and Fernandes, "A Physiologically-based Model for
Simulation of Color Vision Deficiency", IEEE TVCG 15(6), 2009,
[DOI 10.1109/TVCG.2009.113](https://doi.org/10.1109/TVCG.2009.113). The exact
coefficients come from the authors'
[supplementary matrix table](https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/CVD_Simulation.html).

Implementation details:

- Matrices operate on linear-light sRGB.
- Results are clipped once to the displayable sRGB gamut.
- CIE Lab dE76 is measured in floating point, without an intermediate 8-bit
  hex round-trip.
- No dE value is labelled pass, fail, clear or merged. These are house review
  distances, not WCAG requirements or validated accessibility thresholds.
- The paper validates protan and deutan modelling. It explicitly says its
  replacement model is not intended for tritanopia. The supplementary
  tritanomaly severity-1 matrix is therefore shown as provisional and is not
  presented as a tritanopia result.

### Current advisory dE76 output

| Theme and pair | Protan 1.0 | Deutan 1.0 | Provisional tritanomaly 1.0 |
|---|---:|---:|---:|
| Dark Copper / Brass | 18.6 | 17.6 | 26.5 |
| Dark Copper / Mist | 49.5 | 49.7 | 51.7 |
| Dark Brass / Mist | 34.0 | 33.8 | 25.2 |
| Dark Good / Problem | 32.2 | 39.0 | 109.4 |
| Light Copper / Brass | 20.5 | 25.9 | 32.4 |
| Light Copper / Mist | 53.4 | 61.7 | 63.3 |
| Light Brass / Mist | 42.1 | 44.4 | 37.9 |
| Light Good / Problem | 29.3 | 48.1 | 110.3 |

The weakest status pair in the full advisory output is dark Good / Neutral at
19.5 for protan and 13.8 for deutan; in light it is Watch / Problem at 4.7 for
protan and Good / Neutral at 18.3 for deutan. This reinforces the structural
rule: status always carries a word, and category and status never share a slot.

## Typography, wordmarks and grain

- Montserrat Regular 400, Medium 500 and SemiBold 600 are vendored as TTF and
  WOFF2 from one pinned official commit. CSS and the guide load all three
  upright weights; no italic face is declared.
- Screen text never falls below 11px. Eleven pixels is reserved for uppercase,
  tracked labels. Status words, values, ratios and compact badges use 12px or
  larger.
- Karpal Geometric remains display-only. Below 20px it uses `+0.04em`
  tracking instead of the display-size `+0.02em`.
- Wordmark minimum size is rendered lowercase x-height, not universal width:
  8px on screen and 2mm in print. A 7px screen x-height is an absolute
  exception for a known static export reviewed at 1x on both themes.
- Per-lockup minimum width is generated as
  `ceil(sourceRenderedWidthPx * targetXHeightPx / sourceRenderedXHeightPx)`.
  Long and short names therefore get different legal minimum widths.
- Grain never sits behind body text, tables, charts or type below 14px. It
  never overlays a category or status fill.

## Re-run

From `design/brand/`:

```sh
python3 verify-palette.py --self-test
python3 verify-palette.py
```

The first command checks deterministic contrast fixtures, published matrix
invariants, one CVD regression fixture and a deliberately stale scoped-CSS
fixture. The second performs the normative JSON-driven release gate, CSS parity
check and clearly separated advisory CVD report.
