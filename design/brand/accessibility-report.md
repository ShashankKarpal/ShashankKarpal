# Accessibility report

Direction: Ink and Bone, v1.0.0, 2026-08-18. Every number below was computed, not estimated.

Method:
- Contrast ratios use the WCAG 2.1 relative luminance formula. AA needs 4.5:1 for body text and 3:1 for large text and meaningful non-text elements.
- Colour blindness uses the Vienot 1999 LMS reduction for deuteranopia, protanopia and tritanopia, then measures perceptual distance in CIE Lab (dE76) between every pair after simulation.
- Reading the dE numbers: under 10 means the two colours are effectively the same colour to that viewer, 10 to 20 means you can tell them apart if they are side by side, above 25 means they are plainly different.
- Design rule that makes the results hold in practice: category colour and status colour never occupy the same slot in one component, and every status carries a word as well as a colour, which satisfies WCAG 1.4.1.

## Dark theme, the default

### Text and icon contrast on the page `#0B0C0D`

| Token | Hex | On page | On card `#171614` | Verdict |
|---|---|---|---|---|
| Text primary | `#F3F1EB` | 17.33 | 16.01 | AA and AAA |
| Text quiet | `#8F8C85` | 5.83 | 5.39 | AA |
| Copper | `#B17E51` | 5.57 | 5.14 | AA |
| Brass | `#BFB287` | 9.26 | 8.55 | AA and AAA |
| Mist | `#CFDFE8` | 14.33 | 13.24 | AA and AAA |
| Good | `#4FC4A6` | 9.12 | 8.42 | AA and AAA |
| Watch | `#E0B93A` | 10.41 | 9.62 | AA and AAA |
| Problem | `#CB5B45` | 4.77 | 4.41 | AA on page, large text only on card |
| Info | `#4681D0` | 4.95 | 4.57 | AA |
| Neutral | `#7F8B85` | 5.53 | 5.11 | AA |

Two notes that matter:
- Problem `#CB5B45` sits at 4.41 on the card surface, just under the 4.5 body-text floor. Rule: Problem is used as a fill with `#0B0C0D` text on it (4.77:1), or as text on the page, never as small text on a card.
- Card `#171614` against page `#0B0C0D` is 1.08:1, and the hairline edge `#292826` is 1.33:1. Those are deliberate, quiet separations, not state indicators. Anything that must be perceived to use the interface, such as an input border, a selected row or a focus ring, uses `#3A3833` or the focus colour Mist `#CFDFE8` at 14.33:1.

### Label text placed on a colour fill

All fills carry `#0B0C0D` as the label colour.

| Fill | Ratio with `#0B0C0D` label | Verdict |
|---|---|---|
| Copper `#B17E51` | 5.57 | AA |
| Brass `#BFB287` | 9.26 | AAA |
| Mist `#CFDFE8` | 14.33 | AAA |
| Good `#4FC4A6` | 9.12 | AAA |
| Watch `#E0B93A` | 10.41 | AAA |
| Problem `#CB5B45` | 4.77 | AA |
| Info `#4681D0` | 4.95 | AA |
| Neutral `#7F8B85` | 5.53 | AA |

White text on these fills fails in every case, so the rule is absolute: never white on a fill in dark theme.

### Colour blindness, category colours

| Pair | Deuteranopia | Protanopia | Tritanopia |
|---|---|---|---|
| Copper / Brass | 61.4 | 41.9 | 26.5 |
| Copper / Mist | 67.2 | 52.4 | 52.2 |
| Brass / Mist | 31.8 | 35.4 | 25.6 |

All three pairs clear 25 in every simulation. This is the single strongest result in the system and it is why one of the three category colours had to be near-white: on a near-black page, three colours can only stay separable under red-green colour blindness if they also differ in brightness.

### Colour blindness, status colours

Worst pair across the five status colours: 17.6 under deuteranopia, 17.6 under protanopia, 21.2 under tritanopia. The pairs that matter most are far apart:

| Pair | Deuteranopia | Protanopia |
|---|---|---|
| Good / Problem | 89.8 | 65.7 |
| Watch / Problem | 33.8 | 66.5 |
| Good / Watch | 111.6 | 111.7 |

The weakest status pair is Good against Neutral at 17.6. Both always carry a word, so the colour is a second signal, not the only one.

### Known collisions, stated honestly

Under deuteranopia and protanopia, four cross pairs fall below 20:

| Pair | Deuteranopia | Protanopia | Why it is safe |
|---|---|---|---|
| Brass / Neutral | 6.1 | 6.9 | Brass only appears on a left rail, a mark or a repo badge. Neutral only appears in a status chip with a word in it. They never sit in the same slot. |
| Brass / Good | 12.0 | 11.9 | Same separation of slots, and Good always reads "good". |
| Mist / Info | 13.5 | 13.1 | Mist is a category rail, Info is a chip or a link. |
| Copper / Problem | 19.8 | 13.5 | Copper is a rail or a badge, Problem is a chip that reads "problem". |

This is the honest limit of a three-colour category system plus a five-colour status system on one surface: with eight meaningful colours in a limited brightness range, some pairs must collide. The system resolves it structurally rather than pretending it does not exist.

## Light theme

### Text contrast on the page `#F5F5F3`

| Token | Hex | On page | On card `#FFFFFF` | Verdict |
|---|---|---|---|---|
| Text primary | `#1A1917` | 16.09 | 17.57 | AA and AAA |
| Text quiet | `#5A5852` | 6.52 | 7.11 | AA |
| Copper | `#99612F` | 4.69 | 5.12 | AA |
| Brass | `#4D4323` | 8.98 | 9.80 | AA and AAA |
| Mist | `#2D647F` | 5.94 | 6.48 | AA |
| Good | `#307A64` | 4.70 | 5.13 | AA |
| Watch | `#695725` | 6.43 | 7.02 | AA |
| Problem | `#C73C20` | 4.70 | 5.13 | AA |
| Info | `#3A659D` | 5.45 | 5.95 | AA |
| Neutral | `#3B413E` | 9.56 | 10.44 | AA and AAA |

Fills in light theme carry white labels: Copper 5.12, Brass 9.80, Mist 6.48, Good 5.13, Watch 7.02, Problem 5.13, Info 5.95, Neutral 10.44. All pass AA. Black text on these fills fails, so the rule inverts cleanly: white on a fill in light theme, ink on a fill in dark theme.

### Colour blindness, light theme

| Pair | Deuteranopia | Protanopia | Tritanopia |
|---|---|---|---|
| Copper / Brass | 32.3 | 36.0 | 30.0 |
| Copper / Mist | 80.6 | 79.9 | 59.6 |
| Brass / Mist | 68.4 | 64.4 | 39.6 |

Worst status pair: 27.1 under deuteranopia, 24.0 under protanopia. Cross collisions below 20, deuteranopia first and protanopia second: Mist / Good 13.0 and 12.4, Copper / Watch 14.0 and 9.0, Mist / Info 16.3 and 16.5, Brass / Watch 18.7 and 29.1, Copper / Problem 27.0 and 19.6. Same structural resolution as dark theme.

### Tritanopia caveat

Blue-yellow colour blindness is rare, roughly one in ten thousand, and it is the one place this palette is weaker: in light theme Mist against Info measures 2.8, and Good against Info measures 4.9. Both pairs are category-against-status, so the slot rule and the mandatory word already cover them. No further change was made, because fixing it would have cost the deuteranopia and protanopia results, which affect roughly one in twelve men.

## Non-colour accessibility, since colour is not the whole job

- Minimum 12px gap between rows in any list. You named "no air between rows" as a real cost, so density is capped by the token set rather than left to judgement.
- No text below 11px, and 11px only for uppercase-tracked labels, never for values.
- Grain is banned behind body text, inside tables, behind charts, and under any type smaller than 14px.
- No italics and no underlines, so emphasis always comes from weight or size. Links use colour plus a hover border, not a permanent underline.
- Karpal Geometric is a display face only. Body text stays Montserrat, which has real capitals, real punctuation and proper hinting at small sizes.
- Focus is visible everywhere: 2px Mist ring at 14.33:1 on dark, 2px `#2D647F` on light, always with 2px offset.

## What was rejected and why

- The muted trio you first liked (dusty rose, sage, slate blue) measured 5.2 between rose and sage under deuteranopia. Effectively one colour to a red-green colour blind viewer. Rebuilt rather than shipped.
- An all-cool palette (Cold Steel, direction 4) cannot carry three separable categories on a dark page, because every cool hue collapses toward the same blue. It needed a warm anchor to work at all.
- Eight project colours were dropped before they were designed. Past six, colour stops being recall and starts being a legend you have to decode.

## Amendment, 2026-08-19, after the external-critique audit

Full context: `reviews/2026-08-19-external-critique-audit.md`. Owner decisions applied:

- EdgeStrong (`#3A3833` dark, `#CDCAC2` light) is reclassified as DECORATIVE. Its measured ratios (1.38 to 1.67 against page, card and raised) never met the 3:1 that WCAG 2.2 non-text contrast requires where a boundary identifies a control or state. Two tested tokens replace it in those roles:

| Token | Dark | vs page | vs card | vs raised | Light | vs page | vs card | vs raised |
|---|---|---:|---:|---:|---|---:|---:|---:|
| controlBorder | `#716D64` | 3.80 | 3.51 | 3.23 | `#85827B` | 3.51 | 3.83 | 3.22 |
| stateIndicator | `#9A968C` | 6.63 | 6.13 | 5.63 | `#67645C` | 5.41 | 5.91 | 4.96 |

- Inline text links now carry a PERSISTENT underline plus a dedicated link token: dark `#5E92DC` (6.17 page, 5.70 card, 5.24 raised), light `#3A659D` (5.45, 5.95, 5.00). The old rule (Info colour, hover border only) failed twice: light Info differs from body text by only 2.95:1, and dark Info on raised is 4.21:1. Info remains for chips and notices. Underline-free links are allowed only in controls whose navigation role is already explicit (buttons, tabs, nav).
- Selected and active states must pair stateIndicator with a non-colour cue (check, weight change, icon, or rail).
- CAUTION on the colour-blindness tables above: the audit found the simulation mixes an LMS matrix with replacement coefficients derived for a different matrix, and attributes tritanopia to Vienot 1999, which covers protanopia and deuteranopia only. With the paper's own matrix, dark Copper/Brass separations land near 18, not 61.4 and 41.9, and light protan Good/Problem lands near 26. The dE figures in this report should be treated as advisory until verify-palette.py is rebuilt (open item in the audit). The WCAG contrast tables are unaffected; they recompute correctly.
- Raised-surface gaps found by the audit, unchanged for now and to be respected in layouts: dark Problem 4.06 and dark Info 4.21 on raised; light Copper, Good and Problem about 4.29 to 4.31 on raised. Keep these as fills or large text on raised, or keep them off raised.

## How to re-run these checks

The verification script lives with this report as `verify-palette.py`. Run `python3 verify-palette.py` after any colour change. It prints every ratio and every simulated pair, and exits non-zero if a required pair fails. Note the CVD caution in the amendment above; the contrast arithmetic is trustworthy, the simulation is pending a rebuild.
