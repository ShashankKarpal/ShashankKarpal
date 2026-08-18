# Handoff: mark set and full rollout

Written 2026-08-18 at the end of the session that created the Ink and Bone brand system. This file is the brief for the next session. Read it before doing anything, then read `shanky-brand-guide.html` and `brand-tokens.json` in this folder.

Owner: Shashank Karpal (Shanky). GitHub: `ShashankKarpal`. Personal work only; KodeKloud client work is out of scope and keeps the KodeKloud system.

## What already exists in this folder

| File | What it is |
|---|---|
| `shanky-brand-guide.html` | The system. Self-contained, dark by default, has a light toggle. Open it first. |
| `brand-tokens.json` | Every colour, type, space, pattern and logo rule as data. Canonical. |
| `brand-tokens.css` | The same tokens as CSS custom properties, with components. |
| `repo-rollout.md` | Per-repo colour, badge, label and banner plan. |
| `accessibility-report.md` | Measured contrast and colour blindness results. |
| `verify-palette.py` | Run after any colour change. Exits non-zero on failure. |
| `font/KarpalGeometric-Regular.{woff2,ttf,otf}` | The display face, built from the banner letterforms. Lowercase only. |
| `font/specimen2.png` | What the face looks like. |

Nothing in this folder is committed yet. Review before pushing.

## The system in one screen

Dark is the default. Page `#0B0C0D`, card `#171614`, raised `#201E1B`, edge `#292826`, edge strong `#3A3833`, text `#F3F1EB`, quiet `#8F8C85`.

Three category colours, grouped by the job a project does:

| Colour | Dark | Light and badges | Job | Repos |
|---|---|---|---|---|
| Copper | `#B17E51` | `#99612F` | capture and keep | ledge, content-digest-app |
| Brass | `#BFB287` | `#4D4323` | read a signal against a baseline | helios, zest |
| Mist | `#CFDFE8` | `#2D647F` | Claude and AI tooling | switchdeck, claude-tokens, claude-bridge, claude-burnrate |
| Ink | `#F3F1EB` on page | `1A1917` | no accent | profile repo, forks, skills workspace, 3D printing |

Status colours never double as category colours: good `#4FC4A6`, watch `#E0B93A`, problem `#CB5B45`, info `#4681D0`, neutral `#7F8B85` (dark theme). Light theme: `#307A64`, `#695725`, `#C73C20`, `#3A659D`, `#3B413E`.

Hard rules that apply to marks as much as to screens:
1. Category colour lives on the mark, a left rail or a badge. Status lives in a chip that carries a word. They never share a slot.
2. One accent per mark, maximum. The rest of the mark is ink or text colour.
3. Grain is the only texture, at 0.16 on dark and 0.07 on light, and never behind small type.
4. No gradients as a full-bleed wash. No italics, underlines, emoji, em dashes.
5. The mark identifies the project. The colour identifies the group. Two projects sharing a colour is the design, not a bug.

## Drawing rules for the marks

The letterforms in `font/` were built on this geometry, and the marks must speak the same language:

- Monoline. One stroke weight per mark, no tapering.
- Round caps and round joins, always.
- Curves are true circles and true arcs, never freehand.
- Reference grid: draw in a 96 by 96 box. Stroke weight 7 units at that scale (roughly 7.3 percent of the box). Keep all ink inside an 80 by 80 safe area, so there is 8 units of clear space on every side.
- At 24 and 16 pixels, ship a separate optically simplified variant. Detail that survives at 512 will turn to mud at 16, so the small variant drops strokes rather than shrinking them.
- Filled shapes are permitted only where the concept requires solidity (see ledge below). If a mark is filled, it should still read as the same family: same corner radii, same visual weight.

## Per-project concept briefs

These come directly from Shanky in the session, and they override any inference.

### ledge, Copper. Keep the existing concept.
The current filled step mark stays. His words: "there is a ledge and there is an idea which might fall if I don't record it quickly." The dot sitting near the edge is the idea about to fall, and that reading matters more than monoline consistency. Do not replace it with an outlined L-shape; that version was shown and rejected. Job: refine the existing shape so it survives 16px, keep it filled, keep the Copper dot on the edge.

### content-digest-app, Copper. Keep as is, rebuild cleanly.
Four round-capped lines, three stacked and one carrying out to the right in Copper. His words: "brilliant." Rebuild as a proper SVG master with the standard stroke weight, do not redesign.

### helios, Brass. New concept needed.
The current mark (a filled circle between two bars) was rejected: it reads as a dot between two dashes at 16px. His words: "a lot of information from various devices coming into a hub", and "a lot of data coming into one machine, and it then gives a straight line." So the concept is convergence plus a clean output: several sources feeding one hub, and one steady line coming out. Explore that. Note it is a health dashboard with a device trust layer, so the idea of picking the best source rather than averaging them is fair game. Show two or three directions before committing.

### zest, Brass. Keep as is, rebuild cleanly.
Battery cell with a charge wedge in Brass. His words: "brilliant."

### switchdeck, Mist. Keep as is, rebuild cleanly.
Fanned deck of three cards with the active card in Mist. His words: "brilliant."

### claude-tokens, Mist. Keep as is, rebuild cleanly.
Coin stacks with one loose coin tilted at the top. His words: "brilliant."

### claude-bridge, Mist. New mark.
Private. Cross-account handoff between two Claude accounts (kk1 and kk2) on one Mac. File-first, no database, no daemon. Currently a placeholder "B" in the menu bar. Concept space: two nodes and a span, a handoff, a baton, a shared file passing between two sides. Must work as a menu bar template at 16 and 18px, since that is its main surface.

### claude-burnrate, Mist. New mark.
Private. Burn-rate statusline and widgets for Claude Code usage. Concept space: rate of consumption over a window, a slope, a gauge, a depleting bar. Distinct from the tokens mark, which is about accumulated volume: burnrate is about speed.

### claude-skills-workspace, Ink. New mark, low priority.
Private, internal. A quiet mark is enough. Ink only, no accent.

### netwatch, Ink. Confirm before drawing.
A fork of Sniffnet with a trust layer added: what is expected, what is new, what is flagged. Shanky asked for every repo to have its own mark. Raise the tension once, in one line, before drawing: a mark on a fork can read as claiming authorship. If he confirms, draw it in ink only and keep the upstream credit prominent.

### openTeleprompt, Ink. Confirm before drawing.
Same tension as netwatch, and this one is a straight fork with upstream branding intact.

### ShashankKarpal, the profile repo. Ink.
No new mark. Its banner is the map of the portfolio and carries all six project marks. Once the new marks exist, rebuild both banner SVGs from the new marks rather than hex-swapping the old ones.

### Personal monogram. Private, do not publish.
His words: design it, keep it, he will approve or ask for changes, but it must not go on the README or anywhere public on GitHub. Put it in a clearly private location and say so plainly in the file name and the folder. He is looking forward to seeing it, so make it good, but treat publication as forbidden until he says otherwise.

## Export matrix, per mark

His words: "Everything I might need the logo on my MacBook, on App Store someday, on my watch complications, on my watch as an app, on my iPad, my iPhone." Build all of it.

Vector masters
- `mark.svg` full detail, dark ground version and light ground version
- `mark-24.svg` and `mark-16.svg` optically simplified variants
- `mark-mono.svg` single colour, no accent, for template use
- `mark.pdf` vector, for print and for anything that refuses SVG
- wordmark lockups in Karpal Geometric: horizontal and stacked, SVG and PDF

Raster
- PNG at 1024, 512, 256, 128, 64, 48, 32, 24, 16, transparent background
- PNG at the same sizes on page `#0B0C0D` and on paper `#F5F5F3`
- JPEG at 1024 and 512 on both grounds, for anything that will not take alpha

macOS
- `AppIcon.iconset` with 16, 32, 128, 256, 512 at 1x and 2x, then `iconutil` to `.icns`
- menu bar template: transparent PNG at 44px, plus 1x, 2x and 3x, single colour black with alpha only, named `*-template.png` so macOS tints it automatically

iOS and iPadOS
- App Store marketing icon 1024x1024, no alpha, no rounded corners
- full `Assets.xcassets/AppIcon.appiconset` set with `Contents.json`
- apple-touch-icon at 180x180

watchOS
- watch app icon set, all required sizes with `Contents.json`
- complication assets: circular, extra large, graphic corner and graphic circular, as monochrome templates. ledge already uses a static Step mark on the Watch, so match that behaviour.

Web
- `favicon.ico` multi-size (16, 32, 48)
- `favicon.svg`
- social preview 1280x640 per repo
- README banner 1400x400, dark and light, with grain and the category rail

Every generated file must be reproducible: write the generator script into the repo, do not hand-place pixels.

## Approval workflow, as instructed

Shanky's words, paraphrased tightly: design the idea, show one or two, get approval, then produce everything and show it one by one. Keep designing and showing until he has said yes to every item. Only after every yes does anything get committed or pushed.

So:

1. Phase A, concepts. Show the helios directions (two or three) and the refined ledge at 512, 24 and 16. Nothing else. Wait for yes.
2. Phase B, the full mark set. Every mark at 512, 24 and 16, on dark and light, presented for one-by-one approval. Include claude-bridge, claude-burnrate, claude-skills-workspace, the monogram, and the two forks if he confirmed them. Iterate until every single one has a yes.
3. Phase C, exports. Run the full matrix above, then show a contact sheet per project so he can see what he is getting.
4. Phase D, rollout. Only now touch git.

Do not skip to Phase D because the files look finished. He asked to approve every item.

## Phase D, the rollout checklist

For every repo, on the machine this session runs on:

1. `git pull --ff-only` first. The profile repo clone is five commits behind origin, and editing in two places is what caused the existing drift.
2. Branch per repo, for example `brand/ink-and-bone`. Push the branch, open a PR, do not merge. He reviews.
3. Update, in each repo:
   - `design/` folder: new mark masters, exports, generator script
   - README: banner block, badge hexes from `repo-rollout.md`, any inline SVG lockup
   - any tokens or theme file (helios has `design/tokens.json`, and it has drifted from its README badge before; reconcile both in the same commit)
   - app assets: iconsets, menu bar templates, AccentColor in Xcode asset catalogues
   - any docs page, STATE file or design note that describes the old colours or the old mark
4. GitHub-side items the API cannot always do: social preview images are uploaded manually. Say so plainly rather than claiming they are done.
5. Apply the GitHub label colours from `brand-tokens.json`, the same eight labels in every repo.
6. Rebuild both profile banner SVGs from the new marks. Keep the order: ledge, content-digest-app, helios, zest, switchdeck, claude-tokens. The README Projects list must keep matching that order.
7. The other Mac. Only the machine running the session gets edited. The second machine is brought level with `git pull --ff-only`, never with a parallel editing pass. State this to him at the end with the exact commands.

## Open items inherited from the previous session

- Mark to project mapping was never written down. From the banner it reads as: battery cell is zest, fanned deck is switchdeck, rising bars is claude tokens, sun between baselines is helios. Confirm with him, then write it into the guide.
- Karpal Geometric is lowercase only; capitals map to the lowercase shapes. Real capitals are a separate project and the recommendation is to wait a month.
- helios `design/tokens.json` versus its README badge: verify they agree after the change.
- Making and 3D printing stays ink, by his decision. No repo, no colour.
- Grain is the only approved texture. The dot field, fine grid and circle patterns were liked but deliberately held in reserve; using one needs a decision, not a habit.

## Style rules for everything you write to him

- No em dashes, en dashes, curly quotes, ellipsis characters, arrows or emoji. Commas, periods, colons, semicolons and parentheses only.
- Concise and structured. Headings and bullets. No filler, no "great choice".
- Documents use Montserrat, title 18, headings 13, body 10, line spacing 1. Designed collateral uses 1.5 body and 1.4 in cards.
- He is technical and commercial. Match that depth. Do not explain basics.
