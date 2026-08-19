# Audit of the external Ink and Bone critique, 2026-08-19

Auditor: Claude session of 2026-08-19, acting as the strictest reviewer in
the chain per the brief on the Desktop. Inputs: the review brief
(ink-and-bone-critique-prompt.md), GPT's critique (ink-and-bone-critique.md),
and the actual working trees of all eleven repos. Every claim below was
checked against files and git history on this machine, not taken on faith.

This document deliberately does not reproduce or describe the private
monogram's geometry. File paths and line references only.

## 1. Verdict on the critique

GPT's report is unusually accurate. Out of roughly fifty checkable factual
claims, none of substance is invented. I reproduced its WCAG contrast
figures to three decimals, confirmed its two live-drift findings, confirmed
the SOP regression down to the exact commits, and confirmed the critical
privacy finding, which is real and slightly WORSE than GPT stated: beyond
the two rendered images in the public profile repo, the monogram's full
source geometry was public in the tracked generator of the profile repo and
all nine consumer repos, six of them public. Two partial misreads and a
handful of already-documented quirks are noted below. The report's ranked
priorities were broadly correct.

Trust calibration for future external reports: this one earned high trust
because it cited paths and numbers that verified. The lesson is not that
external reports can be trusted, it is that verifiable citations make
verification cheap. A report with the same tone and no reproducible numbers
deserves none of this credit.

## 2. Claim-by-claim classification

Buckets: CONFIRMED (reproduced against files), WRONG (factually incorrect),
MISREAD (real observation, wrong conclusion), TASTE (opinion, no action
without Shanky), ALREADY KNOWN (documented in BRAND-SURFACES.md before GPT
ran).

### Privacy (the critical section)

| Claim | Bucket | Evidence |
|---|---|---|
| Public profile repo tracks the private exploration image and its contact sheet | CONFIRMED | round1-a-monogram.png and round1-contact-sheet.png were tracked and on origin/main (commit f473bb9). Both render the monogram; verified visually. |
| The public generator contains the private source definition | CONFIRMED | generate_marks.py MARKS registry carried a full "monogram" entry (former lines 173-191), public since the initial rollout PR d59f72f. |
| rollout.py copies the generator into every consumer; all nine track byte-identical copies | CONFIRMED | rollout.py copy_marks (lines 89-94). All nine consumer copies hashed identical to each other (6b6f3badea4d prefix), an older snapshot of the canonical file. |
| Several consumers are publicly synchronized | CONFIRMED | gh: ledge, content-digest-app, helios, zest, switchdeck, claude-tokens are PUBLIC; claude-bridge, claude-burnrate, claude-skills-workspace PRIVATE. |
| The ignore rule covers only out/private and does not protect source or exploration files | CONFIRMED | .gitignore had only design/marks/out/private/. |
| The mirror's claim that the design exists nowhere else is false | CONFIRMED | ink-and-bone README said "exists nowhere else on GitHub" while the geometry sat in seven-plus public repos. |
| out/private itself was ever tracked publicly | CONFIRMED NEGATIVE | git log --all --diff-filter=A on that path is empty; the gitignore held for renders in out/private. The leak paths were the generator and the exploration folder. |

### SOP regression

| Claim | Bucket | Evidence |
|---|---|---|
| c5b6d82 and ce8809c added detailed helios PWA steps; 4775655 deleted them | CONFIRMED | git show 4775655: 23 insertions, 30 deletions on BRAND-SURFACES.md; the deleted hunk is exactly the PWA asset list, sw.js cache bump, npm build requirement, checksum verify, and client-cache block. |
| The replacement text permits copying files directly into dist, the documented trap | CONFIRMED | The post-4775655 helios section said "either npm run build or copy into dist directly". |

### Live drift

| Claim | Bucket | Evidence |
|---|---|---|
| content-digest-app still uses retired #FF6B35 | CONFIRMED | 9 hits in server.py, 3 in extension/options.html (lowercase #ff6b35). Root cause: the hex predates the brand and was never in rollout.py's mapping. |
| helios web tailwind config carries #E8ECE9, #9AA49E, #7EE0B1, #1B7A55 | CONFIRMED, understated | web/tailwind.config.js carried the ENTIRE old palette (ten values including #0B0D0C, #FBBF24, #F87171). Root cause: rollout walked web/src only, and src uses Tailwind classes, so the live UI rendered fully old colours. Additional drift GPT missed: helios/design/brand/README.md and design/brand/tokens/ snippets still document the old mint system. |

### Avatar

| Claim | Bucket | Evidence |
|---|---|---|
| Generated avatar README says upload dark, SOP records light as live | CONFIRMED | out/github/avatar/README.md said avatar-dark-460.png; SOP LIVE VARIANT says light. The generator itself emitted the wrong instruction (build_avatar). |
| Same composition rendered at 460 to 20 px, no optical variants | CONFIRMED | build_avatar loops (460, 400, 200, 80, 40, 20) over one layout. At 40 px the light file is visually near-empty; verified by eye. |
| Circle boundary fails on matching host themes (about 1.09, 1.64, 1.03, 1.62) | CONFIRMED | Recomputed: 1.092, 1.638, 1.035 (vs GitHub dark #0D1117), 1.616. |
| Round-two contact sheet already shows the small-size failure | CONFIRMED | Sizes fail by inspection; the gate was missing, not the evidence. |
| Avatar copy is 10.5 and 11 design units exported unchanged to 20 px | CONFIRMED | avatar_copy uses em 11.0, 15.0, 10.5 in a 400 viewBox. |

### Tokens, fonts, source of truth

| Claim | Bucket | Evidence |
|---|---|---|
| brand-tokens.json is canonical in name only; no executable reads it; values duplicated in generate_marks.py 37-47, rollout.py 33-60, verify-palette.py 7-16, CSS, guide | CONFIRMED | All five locations verified; nothing imports the JSON. |
| Token production-mark status stale (says marks are open) | CONFIRMED | logo.marks.status still said the shapes were not drawn, one day after all nine shipped. |
| Guide open items stale | CONFIRMED | Guide still said marks not drawn and mapping unrecorded. |
| 96 px universal wordmark minimum makes long lockups illegible | CONFIRMED | brand-tokens.json line 188; lockup PNGs measure 1095x400 (ledge) to 3074x400 (claude-skills-workspace); at 96 px wide the longest is 12.5 px tall. |
| Montserrat declares 400, 500, 600 but only Regular and Medium are vendored | CONFIRMED | font/ contains Regular and Medium only; tokens declare [400, 500, 600]; browsers would synthesize 600. |
| brand-tokens.css expects Karpal files beside it; files live in font/ | CONFIRMED | @font-face src lacked the font/ prefix. |
| The guide does not vendor Montserrat and can silently fall back | CONFIRMED with nuance | The guide embeds Karpal as base64 (self-contained for the display face) but declares Montserrat with no @font-face, so body text silently uses the system fallback on machines without Montserrat. Footer overclaimed. |
| No editable Karpal source or build script; font not regenerable | CONFIRMED | No .glyphs, .ufo, .sfd, or build script anywhere in either repo. |
| Montserrat license is a summary, not the full OFL; Karpal license unstated | CONFIRMED | MONTSERRAT-LICENSE.md was 17 lines; no Karpal statement exists. |

### Grain

| Claim | Bucket | Evidence |
|---|---|---|
| Raster grain is applied after compositing the entire image and can land on foreground | MISREAD in scope, CONFIRMED for banners and social | True for render_with_grain (banner and social PNGs: grain composited last, over rail, mark, and wordmark, while the same assets' SVGs put grain under the foreground). FALSE for the avatar: avatar_png lays grain on the page first and composites art on top, exactly as its docstring says. GPT partially acknowledged the avatar but framed the flaw generator-wide. |
| SVG applies opacity twice (feFuncA slope and rect opacity), PNG once; texture strength differs by format | CONFIRMED | GRAIN_FILTER embeds slope 0.16 and the carrying rect repeats opacity 0.16; effective SVG alpha is about 0.026 vs the PNG overlay's 0.16. Same filename stem, different texture. |
| random.seed(96) does not control effect_noise; raster grain nondeterministic | CONFIRMED and ALREADY KNOWN | SOP KNOWN QUIRK documents the nondeterminism with a workaround. GPT correctly noted the workaround is incomplete (an unchanged SVG does not prove raster packaging unchanged). The seed call itself is misleading dead code. |
| 256 px noise tile repeats across 1400 px assets | CONFIRMED | grain_overlay pastes one 256 tile in a grid. |
| Guide cover puts grain under an 11 px label; README example under 12 px text and 9 px badges | CONFIRMED | Cover: .label 11 px plus 14 px quiet copy over the grain pseudo-element. README example SVG: grain rect under 12 px description and two 9 px badges. Both violate the token rule (no grain under type below 14 px). |

### Accessibility

| Claim | Bucket | Evidence |
|---|---|---|
| CVD simulation math is internally inconsistent; coefficients belong to a different LMS matrix; tritanopia is not in Vienot 1999 | CONFIRMED | verify-palette.py uses a normalized HPE matrix with replacement coefficients derived for the Vienot 1999 paper matrix. Rerunning with the script's math reproduces the published tables exactly (61.4, 41.9, 32.3, 36.0), so those tables came from this script. Rerunning with the paper's own matrix and inverse gives 18.0 and 18.4 dark copper/brass, 26.7 and 19.5 light, and 25.6 for light protan good/problem, below the script's own 30 floor. GPT's rerun numbers (16.3, 18.2, 25.0, 19.4, 23.9) differ slightly from mine, method details, but the direction and materiality are right: the headline separation evidence is an artifact of mismatched math. |
| Script clips and quantizes before measuring distance; silently relaxes tritan thresholds | CONFIRMED | rgb2hex clamps and rounds before dE76; tritan status floor drops from 15 to 4.0 with no output saying so. |
| EdgeStrong fails 3:1 for its declared must-see role | CONFIRMED | 1.672, 1.544, 1.420 dark and 1.500, 1.638, 1.375 light against page, card, raised. Tokens assign it input borders and selected rows. WCAG 1.4.11 wants 3:1 where the boundary is required to perceive the control. |
| Light Info vs body text is 2.95, below the 3:1 link-differentiation guidance; no persistent underline; dark Info on raised 4.21 | CONFIRMED | 2.9516 and 4.205 recomputed. CSS: a { text-decoration: none } with hover border only. |
| Raised-surface pairs below 4.5 are untested: dark Problem 4.055, dark Info 4.206, light Copper, Good, Problem about 4.29 to 4.31 | CONFIRMED | 4.055, 4.205, 4.294, 4.306, 4.304 recomputed; verify-palette.py never tests raised. |
| Guide ships 10.5 px, 9 px, 11 px lowercase type against the report's own floor | CONFIRMED | .ratio 10.5 px, README-example badges 9 px. Note: the guide's own .label class does enforce uppercase; the one in brand-tokens.css does not. GPT overgeneralized slightly. |
| color-scheme: dark light while data attributes force a theme | CONFIRMED | brand-tokens.css line 70; neither forced-theme block resets color-scheme. Native widgets can follow the OS against the forced theme. |
| Internal accent-to-ink contrast is weak (dark mist 1.21, brass about 1.9) | CONFIRMED | 1.21, 1.87, 3.11 dark; 2.71, 1.79, 3.43 light. Category-by-colour is weaker inside a mark than the on-page numbers imply. |
| Dark Problem on card disclosed; focus rings strong; label-on-fill pairs pass | CONFIRMED, to the system's credit | GPT credited these correctly. |

### Marks at small sizes

| Claim | Bucket | Evidence |
|---|---|---|
| 16 px alpha bounds: content-digest-app, helios, claude-bridge, claude-burnrate touch the horizontal crop; ledge touches top; switchdeck footprint much smaller | CONFIRMED, one omission | Measured bboxes agree; GPT missed that claude-tokens touches the right edge too. |
| Identity readings (switchdeck purse-like, helios scissors at 16, tokens not coin-like, and so on) | TASTE | Plausible readings, but judgment calls. No action without Shanky. |
| Eight older out trees carry both contact-sheet.png and the project-named sheet; newest tree only the new name; marks README documents the legacy name | CONFIRMED | Exactly 8 plus claude-tokens; README table row said contact-sheet.png. |

### Engineering and process

| Claim | Bucket | Evidence |
|---|---|---|
| ICNS errors are swallowed; command still succeeds; stale-icns risk | CONFIRMED | try/except Exception prints "icns skipped" and continues. |
| Missing glyphs become silent 0.35 em blanks | CONFIRMED | text_paths and ui_text_paths skip unknown cmap entries. |
| Output writes are not transactional | CONFIRMED | build writes directly into out/; the legacy contact sheets are the observed consequence. |
| Toolchain unpinned: no pyproject, lock, .python-version, Brewfile | CONFIRMED | None existed; venv held python 3.14.7, cairosvg 2.9.0, pillow 12.3.0, fonttools 4.63.0, icnsutil 1.1.0, unrecorded in source. |
| rollout.py knows only old-to-new v1 mappings; no clean-tree, branch, dry-run, atomicity guards; log overwritten, names the old repo, covers a subset | CONFIRMED | Log listed six repos including uebersicht-claude-tokens; no bridge, burnrate, skills-workspace, profile entries survive; main() rewrites the log wholesale. |
| Consumer generator copies cannot regenerate (fonts missing) and can partially overwrite before failing | CONFIRMED | No consumer has design/brand/font; the copied script's FONT_PATH dangles; build() writes marks before touching wordmarks. |
| Fleet audit does not fetch, skips missing repos, checks ahead only, reports zero without an upstream; M1 check lacks a directory | CONFIRMED | All visible in the old SOP snippet. |
| Public SOP contains machine username, private-network address, service URLs, daemon names | CONFIRMED | shashankkarpal@100.112.78.47, helios.local:8420, :7778, com.shashank.autodeploy, in a public repo. Tailnet addresses are unreachable from outside, but the aggregation still maps the infrastructure. |
| Stale profile-banner PNGs use the previous palette | CONFIRMED | Pixel palette of the tracked PNGs: #2FD4C4, #7EE0B1, #E78892 on #1C1B1D. README references the SVGs, so not a live failure, an unmanaged trap. |
| No release tags or changelog; version pinned at 1.0.0 through real changes | CONFIRMED | git tag is empty in both repos. |
| Documentation roles unclear; stale handoffs make current-sounding claims | CONFIRMED | HANDOFF-marks-and-rollout.md, RUNBOOK-phase-e-finish.md (gitignored), guide, docs/STATE.md (predates the brand entirely) all coexist with no normative/historical marking. |
| Mirror shares machine and account; rsync procedure underspecified | CONFIRMED | Same M4, same GitHub account; SOP says "rsync" with no direction, exclusions, or restore test. |
| PNG rebuild nondeterminism reported responsibly | ALREADY KNOWN | SOP KNOWN QUIRK; GPT cited it as documented, as the brief demanded. |
| helios sf-symbol meridian files stale | ALREADY KNOWN | SOP open item since 2026-08-19. |
| Avatar copper exception and light-variant choice | ALREADY KNOWN | Recorded DECISION and LIVE VARIANT lines in the SOP. |
| Category taxonomy critique (functional vs vendor-bound), banner six-of-nine, no-underline aesthetic, category colour as decoration | TASTE / QUESTION | For Shanky. Note: the six banner projects are exactly the six public repos, which looks intentional; GPT did not spot the pattern. |

### Where GPT was wrong or overreached

1. Grain-over-foreground framed as a generator-wide behavior; the avatar
   path masks grain correctly and only banner and social PNGs composite it
   last (their SVG twins layer it correctly, which is itself a parity bug).
2. "The reusable label class does not enforce uppercase" is true of
   brand-tokens.css and false of the guide's own class.
3. Its re-derived CVD numbers did not reproduce exactly under a clean
   Vienot 1999 implementation (mine differ by 1 to 2 dE); GPT itself warned
   its figures were not new thresholds, so this is a quibble, not an error.
4. Minor: claude-tokens' 16 px mark also touches the crop; GPT's edge list
   was incomplete.

## 3. Where previous Claude sessions screwed up

1. The Phase D rollout session (2026-08-18) created the privacy breach: it
   shipped the monogram geometry inside the public generator and then
   copied that file into nine repos. The Phase E runbook even wrote "lives
   only in out/private, gitignored" while the geometry sat in the tracked
   script. Nobody checked.
2. The avatar session (2026-08-19, f473bb9) committed two monogram renders
   to the public exploration folder in the same commit whose README says
   the concept must never ship. A privacy rule stated in prose was violated
   by the very session writing the prose.
3. The toolchain session (4775655, same day) deleted the helios PWA
   incident knowledge added hours earlier by c5b6d82 and ce8809c, and
   reintroduced a documented trap as an instruction. Almost certainly a
   section rewritten from a stale read of the file.
4. The avatar decision session recorded "light is live" in the SOP but
   never regenerated the avatar README, leaving a generated file
   instructing the opposite of the owner's decision.
5. Recorded and self-corrected before this audit: the rename session left
   a stale export tree and no SOP record; the pipeline shipped before the
   Mac could run it; PNG grain nondeterminism.
6. Chronic smaller sins: a random.seed call that controls nothing, dead
   code (an if False expression in tile_svg, a vacuous privacy condition
   and a self-identical string replace in rollout.py), a stale
   docs/STATE.md, stale token status, stale guide open items, a stray
   specimen2.png in font/.

## 4. What GPT missed

1. The full extent of the helios drift: the whole tailwind palette, not
   four values, plus the stale old-brand README and token snippets in
   helios/design/brand/.
2. The six-of-nine banner selection matches the public/private repo split
   exactly, which likely answers its own question 17.
3. The dead code listed above.
4. claude-tokens' 16 px right-edge crop.
5. docs/STATE.md, a pre-brand snapshot presenting itself as current state.
6. The marks README run instruction (python3) contradicts the SOP's venv
   command on the only machine that matters.
7. That the exploration README's own text ("exists only here and in
   out/private") was self-refuting the moment it was committed publicly.

## 5. Triage table with status

Severity: CRITICAL, HIGH, MEDIUM, LOW. Effort: S under 15 min, M under 2 h,
L more. Status: DONE (this session, verified), WAITING-ON-SHANKY, or OPEN
(accepted debt, tracked here and in the SOP).

| id | Item | Where | Sev | Effort | Decision? | Status |
|---|---|---|---|---|---|---|
| 1 | Monogram geometry in public generator | shashankkarpal + 9 consumers, design/marks/generate_marks.py | CRITICAL | M | No | DONE: moved to gitignored private_marks.py overlay, fail-closed build, all ten repos sanitized and pushed |
| 2 | Monogram renders tracked publicly | design/marks/exploration/2026-08-19-github-avatar/ | CRITICAL | S | No | DONE: both files moved to design/marks/out/private/exploration/, git rm from public tree, README rewritten |
| 3 | Monogram in git HISTORY of profile repo and nine consumers | all ten repos on GitHub | CRITICAL | L | Decided | DONE by decision (Shanky, 2026-08-19): v1 treated as disclosed and RETIRED as a private identifier; no history rewrite; any future private monogram is a new v2 living only in the overlay. Recorded in SOP, overlay header, and mirror README |
| 4 | Mirror README false "nowhere else" claim | ink-and-bone/README.md | CRITICAL | S | No | DONE: reworded honestly, incident referenced |
| 5 | Generated avatar README says upload dark | generate_marks.py build_avatar + out/github/avatar/README.md | CRITICAL (live-avatar regression path) | S | No | DONE: generator fixed, README regenerated, SVGs verified byte-identical, PNG churn reverted |
| 6 | Helios PWA knowledge deleted from SOP | design/brand/BRAND-SURFACES.md | HIGH | S | No | DONE: restored from the ce8809c-era text, regression recorded with a lesson |
| 7 | content-digest-app live #ff6b35 | server.py, extension/options.html | HIGH | S | No | DONE with one manual step left: swapped to copper #b17e51, pushed, M1 pulled to 584e235. The running com.shashank.contentdigest process predates the pull; Shanky restarts it (launchctl kickstart -k gui/501/com.shashank.contentdigest on the M1) and reloads the Safari web app. Automation was correctly blocked from killing the live service. |
| 8 | helios live old palette | web/tailwind.config.js | HIGH | S | No | DONE: full palette swapped per rollout mapping, sw.js bumped v4, dist rebuilt, served files checksum-verified; Chrome incognito eyeball left for Shanky |
| 9 | Stale old-palette profile banner PNGs | design/github/*-1400x400.png | HIGH | S | No | DONE: removed; README uses the SVGs; SOP notes the removal |
| 10 | Unpinned toolchain | repo root | HIGH | S | No | DONE: .python-version and requirements.lock committed, SOP recovery lines updated |
| 11 | brand-tokens.css Karpal font path wrong | design/brand/brand-tokens.css | HIGH | S | No | DONE: font/ prefix added |
| 12 | Tokens not executable, palette duplicated in five places | tokens, generator, rollout, verifier, CSS, guide | HIGH | L | Partly | OPEN: structural; recommendation below. Not attempted in one session on purpose |
| 13 | rollout.py cannot express future changes, no guards, weak log | design/marks/rollout.py | HIGH | M | Decided | DONE: archived as rollout-v1-migration.py (log too) with a do-not-reuse header; removed from the live SOP protocol. A future reusable tool must be manifest-driven with dry-run, clean-tree, expected-match, fail-closed, transactional install |
| 14 | CVD verifier math incompatible, silent tritan relaxation | design/brand/verify-palette.py, accessibility-report.md, guide | HIGH | M | Partly | OPEN: numbers stand in shipped docs; flagged here and in SOP; rebuild of the verifier recommended before the next palette decision |
| 15 | EdgeStrong below 3:1 for its declared control role | tokens | HIGH | M | Decided | DONE: edgeStrong reclassified decorative; controlBorder (dark #716D64, light #85827B) and stateIndicator (dark #9A968C, light #67645C) added, all clearing 3:1 on page, card, raised; states must pair with a non-colour cue. Tokens, CSS, guide, and accessibility report amended |
| 16 | Link style fails differentiation in light theme, no persistent underline | tokens, CSS | HIGH | S | Decided | DONE: inline links get a persistent underline plus a link token (dark #5E92DC, light #3A659D) clearing 4.5:1 on all surfaces; blanket no-underline rule retired in tokens, CSS, and guide; consumer BRAND.md files updated |
| 17 | Public SOP discloses infra details | BRAND-SURFACES.md | HIGH | M | YES (split decision) | WAITING-ON-SHANKY |
| 18 | Consumer pipeline copies cannot regenerate | 9 consumer repos | MEDIUM | M | Decided | DONE: copied generators and pipeline READMEs deleted from all nine consumers; each now carries design/marks/PROVENANCE.md with the canonical repo, generator commit, token version, and sha256 hashes of every asset. No package unless independent regeneration becomes a real need |
| 19 | Avatar has no optical variants at 80, 40, 20; rim invisible on matching hosts | generate_marks.py avatar | MEDIUM | M | YES (design) | WAITING-ON-SHANKY |
| 20 | Weak or cropped 16 px marks (switchdeck, helios, skills-workspace; five marks touch the crop) | generate_marks.py | MEDIUM | M | YES (design) | WAITING-ON-SHANKY |
| 21 | 96 px universal wordmark minimum | brand-tokens.json line 188 | MEDIUM | S | YES (rule change) | WAITING-ON-SHANKY: recommend a minimum x-height rule |
| 22 | Montserrat 600 declared, not vendored | tokens, font/ | MEDIUM | S | YES | WAITING-ON-SHANKY: vendor SemiBold or drop 600 |
| 23 | Grain parity (SVG double attenuation vs PNG), banner/social PNG grain over foreground, tile repetition, misleading seed | generate_marks.py | MEDIUM | M | No | OPEN: recorded; fix alongside the next generator change; removing the seed line alone is cosmetic |
| 24 | Guide violates own grain and type-floor rules; dark-only evidence tables | shanky-brand-guide.html | MEDIUM | M | Partly | OPEN: stale open-items and footer fixed this session; cover label, 9 and 10.5 px examples, and a light evidence table remain |
| 25 | Stale legacy contact sheets in 8 out trees and consumers | design/marks/out/, consumers | MEDIUM | S | No | DONE in consumers (removed); canonical out/ trees self-clean on next full rebuild; README row fixed |
| 26 | brand-tokens.json marks.status stale | brand-tokens.json | MEDIUM | S | No | DONE: reflects the shipped nine |
| 27 | ICNS failures swallowed, silent glyph blanks, non-transactional writes | generate_marks.py | MEDIUM | M | No | OPEN: recorded; fold into the next pipeline change |
| 28 | Montserrat license incomplete, Karpal license unstated, no Karpal source | design/brand/font/ | MEDIUM | S/M | Partly | Full OFL text DONE; Karpal license statement and editable source WAITING-ON-SHANKY (where is the source?) |
| 29 | Fleet audit weak | BRAND-SURFACES.md | MEDIUM | S | No | DONE: replaced with a fetch-aware, fail-loud version reporting ahead and behind |
| 30 | No tags, changelog, or version discipline | both repos | MEDIUM | S | YES (naming) | WAITING-ON-SHANKY: recommend tagging v1.0.0 now and v1.1.0 after this audit's fixes |
| 31 | Mirror is same-machine, same-account; no off-account backup or restore test | ink-and-bone | MEDIUM | S/M | YES (where) | WAITING-ON-SHANKY |
| 32 | Category-colour semantics (skills-workspace in ink, taxonomy axis, colour as sole group cue) | tokens, MARKS | MEDIUM | S | YES | WAITING-ON-SHANKY |
| 33 | docs/STATE.md presented stale state as current | docs/STATE.md | LOW | S | No | DONE: historical header added. Discovery: the file is excluded via .git/info/exclude, so it was never tracked or public; the note lives on disk only |
| 34 | Dead code: if False in tile_svg, vacuous rollout condition, no-op replace, seed(96) | generator, rollout | LOW | S | No | OPEN: cosmetic; batch with the next real pipeline edit to keep this session's diffs reviewable |
| 35 | marks README python3 vs SOP venv command | design/marks/README.md | LOW | S | No | DONE via SOP protocol line update; README run block left generic since consumers have no venv |
| 36 | specimen2.png stray in font/ | design/brand/font/ | LOW | S | No | OPEN: ask before deleting an artifact I cannot identify |
| 37 | color-scheme: dark light under forced themes | brand-tokens.css | MEDIUM | S | No | DONE with the token round: color-scheme now follows the active theme in every block |

## 6. What was executed this session, with verification

All git on the Mac via osascript. All eleven repos ended clean, pushed,
correct branches (master for claude-skills-workspace).

1. Privacy containment (items 1, 2, 4). Overlay tested both ways: with
   private_marks.py present the registry holds ten marks and the monogram
   builds into out/private; without it, nine marks and the monogram target
   exits 1. Rebuilt monogram SVG hashes byte-identical to the mirror's
   committed copy (c3a4d380...), proving the overlay preserves geometry.
   Privacy check ran in all ten repos before push: no tracked private
   paths, no PRIVATE_MARKS block, no monogram registry entry.
2. Avatar instruction (item 5). Generator text fixed; avatar target rebuilt
   with the venv; zero SVG diffs; PNG churn reverted per the SOP quirk;
   only README.md carries a diff.
3. SOP restoration and hardening (items 6, 29, plus incident, rules,
   lessons, pinning, drift records).
4. Drift (items 7, 8). CDA: 12 occurrences swapped, pushed, M1 pulled.
   helios: ten palette values swapped, sw bumped to v4, npm build clean,
   dist index.html and sw.js byte-identical to served copies over
   https://helios.local:8420, referenced bundle greps: new hexes present,
   old hexes zero.
5. Hygiene (items 9, 10, 11, 25 consumers, 26, 28 OFL, 33). 
6. Mirror refreshed by rsync, monogram and overlay verified present,
   committed, pushed, still private.
7. GitHub-side verification from the Mac: the monogram render returns 404
   on the profile repo's main; the generator at HEAD of the profile repo
   and a public consumer contains zero monogram registry entries; the
   fetch-aware fleet audit reports all eleven repos dirty=0 ahead=0
   behind=0, FLEET CLEAN.

## 7. Owner decisions and open questions

Decided by Shanky on 2026-08-19, executed same session:

1. History purge (item 3): DECIDED. Accept the v1 monogram as disclosed,
   no history rewrite, retire it as a private identifier; any future
   private monogram is a wholly new v2 living only in the private overlay.
2. rollout.py (item 13): DECIDED. Archived as the one-time v1 migration,
   removed from the live SOP; a future rollout tool must be
   manifest-driven with dry-run, clean-tree, expected-match, fail-closed,
   and transactional installation.
3. Consumer copies (item 18): DECIDED. Generators deleted from consumers;
   assets plus a PROVENANCE.md (generator commit, token version, file
   hashes) per repo; no versioned package unless independent regeneration
   becomes a real requirement.
4. EdgeStrong and links (items 15, 16): DECIDED. EdgeStrong kept for
   decorative edges; dedicated controlBorder and stateIndicator tokens
   added clearing 3:1 on page, card, and raised; inline text links get a
   persistent underline and a semantic link token meeting normal-text
   contrast on every allowed surface.

Still open, each with a recommendation:

5. Montserrat 600 (item 22): vendor SemiBold or drop 600 from the tokens?
   Recommendation: vendor it; 600 is used by h3.
6. SOP split (item 17): move machine, tailnet, and daemon details to a
   private ops file (mirror or gitignored), leaving the public SOP with
   surfaces and rules? Recommendation: yes; nothing public needs the IP.
7. Avatar small sizes (item 19): art-direct 80, 40, 20 variants (bigger
   mascot, no field, no copy) and add a self-sufficient rim? Recommendation:
   yes, next design session; the current files fail at their most common
   sizes.
8. Small marks (item 20): retune switchdeck, helios s16, skills-workspace,
   and the four crop-touchers only? Recommendation: yes, narrow scope.
9. Wordmark rule (item 21): replace the 96 px minimum with a minimum
   x-height (about 7 px) or per-lockup minima? Recommendation: x-height.
10. Where is Karpal Geometric's editable source (item 28)? If none exists,
    commission or rebuild one; the most distinctive asset is currently
    unrepairable.
11. Tags (item 30): tag v1.0.0 retroactively and v1.1.0 after this audit?
    Recommendation: yes.
12. Off-account backup (item 31): encrypted copy outside the GitHub
    account and machine? Recommendation: yes, one encrypted archive to a
    second provider with a quarterly restore test.
13. specimen2.png (item 36): keep or delete?

## 8. Structural recommendation not executed (item 12)

The single highest-leverage engineering change remains making
brand-tokens.json (plus a small projects and surfaces manifest) the file
everything actually reads: generator, rollout successor, verifier, CSS and
guide generation, and a CI check that fails on drift or on any private
identifier in a public build. Every drift found today (tailwind, #ff6b35,
stale PNGs, stale status lines, the avatar README) is a symptom of values
living in more than one place. This is M-to-L effort and touches every
repo, so it deserves its own session with this table as the spec.
