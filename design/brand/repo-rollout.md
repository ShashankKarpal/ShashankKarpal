# Per-repo rollout plan

Direction: Ink and Bone. Three category colours, grouped by the job the project does. The mark identifies the project, the colour identifies the group. Making, 3D printing, forks and the profile repo stay ink.

Badges and GitHub labels always use the deeper light-theme values, because shields.io and GitHub both render white label text.

## The three groups

| Group | Colour | Dark hex | Badge and label hex | Repos |
|---|---|---|---|---|
| Capture and keep | Copper | `#B17E51` | `99612F` | ledge, content-digest-app |
| Read a signal against a baseline | Brass | `#BFB287` | `4D4323` | helios, zest |
| Claude and AI tooling | Mist | `#CFDFE8` | `2D647F` | switchdeck, claude-tokens, claude-bridge, claude-burnrate |
| Everything else | Ink | `#F3F1EB` on `#0B0C0D` | `1A1917` | ShashankKarpal, netwatch, openTeleprompt, claude-skills-workspace, making and 3D printing |

## Public repos

### ledge
- Category: Copper. Was already the source of the old crimson and ink, so this is the one repo where the colour genuinely changes character. Crimson `#BD4753` retires to Copper `#99612F`.
- README header: near-black band, 4px Copper left rail, wordmark in Karpal Geometric lowercase, one-line description in `#8F8C85`, fine grain at 0.16.
- Badges: platform `99612F`, licence `1A1917`, "local only" `4D4323`.
- Banner: the `<picture>` block is already live and `design/github/readme-banner-{dark,light}-1400x400.png` already exist. Re-render both at 1400x400 in the new palette, Copper rail, grain at 0.16 dark and 0.07 light. Social preview, if you add one, is 1280x640.
- Labels: adhd-loop `99612F`, bug `C73C20`, feature `2D647F`, docs `695725`, shipped `307A64`.
- Note: ledge also ships on iPhone, iPad and Watch. App icon tile stays light paper, per your earlier decision. Watch complication stays the static Step mark.

### content-digest-app
- Category: Copper. Replaces the current crimson `#BD4753` badge.
- README header: same spec, Copper rail.
- Badges: runtime `99612F`, licence `1A1917`, "local first" `4D4323`.
- Existing assets to re-tint: `design/logo/content-digest-symbol-mono-black.svg` (the four round-capped lines) stays mono, the horizontal dark lockup in the `/view` header takes Copper for its accent element, `design/logo/menubar-template.png` stays a macOS template image and takes no colour at all.
- Labels: as above, plus local-only `4D4323`.

### helios
- Category: Brass. Replaces mint `#1B7A55`, which itself replaced `#18C98B`.
- README header: near-black band, Brass rail. The banner block is already live, so re-render the 1400x400 pair in the new palette.
- Badges: platform `4D4323`, licence `1A1917`, "no cloud" `1A1917`.
- Open item carried over: the badge hex and `design/tokens.json` drifted apart once before. Reconcile `design/tokens.json` to Brass in the same commit as the README, then diff them.
- Also carried over from the `brand/meridian` work: AccentColor set, wordmark `s` refinement, SF Symbols blank export at three weights, prior-art search before public use of the mark.
- Labels: bug `C73C20`, feature `2D647F`, device-trust `4D4323`, shipped `307A64`.

### zest
- Category: Brass. Amber `#F5B03E` stays retired; the reason holds, zest and helios both read a signal against a baseline.
- README header: near-black band, Brass rail.
- Badges: current mint `1B7A55` becomes Brass `4D4323`; licence `1A1917`.
- Banner: the `<picture>` block is live and both `design/github/readme-banner-{dark,light}-1400x400.png` exist. Re-render them in the new palette. The old rule still stands for anything new: no banner block goes in before its artwork exists, in public or in private.
- Labels: as helios, plus battery `4D4323`.

### switchdeck
- Category: Mist. Replaces turquoise `#0F7D74`.
- README header: near-black band, Mist rail. Banner block is live, so re-render the 1400x400 pair in the new palette.
- Badges: current turquoise `0F7D74` becomes Mist `2D647F`; licence `1A1917`.
- Open cosmetic item: the notification title still reads "SwitchBar". Still cosmetic, still parked.
- Labels: bug `C73C20`, feature `2D647F`, accounts `2D647F`, shipped `307A64`.

### claude-tokens
- Category: Mist. Replaces turquoise `#0F7D74`.
- README header: near-black band, Mist rail.
- Badges: widget host `2D647F`, licence `1A1917`.
- Existing asset: `design/github/social-preview-1280x640.png` is a dark banner with the coin-stacks lockup. Regenerate it on `#0B0C0D` with grain at 0.16 and the Mist rail.
- Labels: as switchdeck.

### netwatch (fork of Sniffnet)
- Category: Ink only. No accent. It is not your design, and the fork line should stay visible.
- README header: text and badges only, no banner band.
- Badges: upstream credit `1A1917`, licence `1A1917`.
- Labels: minimal, bug `C73C20` and upstream `3B413E`.

### openTeleprompt (fork)
- Category: Ink only, same reasoning as netwatch.
- README: leave upstream branding intact. Your only change is the ink badge row if you want one.

### ShashankKarpal (profile README)
- Category: Ink. The banner is the one place where all three category colours appear together, because it is the map of the whole portfolio.
- Banner update, both files in `design/github/`. This is a straight hex swap, the shapes and layout do not change:

```bash
cd design/github
# dark banner
sed -i '' \
 -e 's/#1C1B1D/#0B0C0D/g' -e 's/#F7F5F2/#F3F1EB/g' -e 's/#E8ECE9/#F3F1EB/g' \
 -e 's/#9AA49E/#8F8C85/g' \
 -e 's/#E78892/#B17E51/g' -e 's/#7EE0B1/#BFB287/g' -e 's/#2FD4C4/#CFDFE8/g' \
 profile-banner-dark.svg
# light banner
sed -i '' \
 -e 's/#F7F5F2/#F5F5F3/g' -e 's/#1C1B1D/#1A1917/g' -e 's/#101413/#1A1917/g' \
 -e 's/#5F6B65/#5A5852/g' \
 -e 's/#BD4753/#99612F/g' -e 's/#1B7A55/#4D4323/g' -e 's/#0F7D74/#2D647F/g' \
 profile-banner-light.svg
```

- Order in the banner stays: ledge, content-digest-app, helios, zest, switchdeck, claude-tokens. The Projects list in the README already matches it; keep it matching.
- Open decision carried over: whether claude-bridge and claude-burnrate join the Projects list once public.
- Before you edit anything locally, run `git pull --ff-only`. The clone is behind the remote, and the drift came from editing in two places.

## Private repos

| Repo | Category | Notes |
|---|---|---|
| claude-bridge | Mist | Menu bar "B" icon takes Mist. No banner needed. |
| claude-burnrate | Mist | The rolled-over week currently states itself in orange. Move that to Watch `#E0B93A` on dark, `695725` in any light surface. |
| claude-skills-workspace | Ink | Internal, no branding work. |
| noop-archive | Ink | Archival mirror of someone else's project. No branding, ever. |
| zest-archive | Ink | Superseded by zest. Leave it alone. |
| kodekloud-collateral-kit, kodekloud-salesos-template | Out of scope | These stay on the KodeKloud system. Your personal palette does not enter client work beyond one thin accent edge on documents you personally authored. |

## Making and 3D printing

No repo, no colour, by your decision. It stays ink until it has something worth colouring. If it ever gets a repo, the first question is whether it joins capture and keep rather than becoming a fourth colour.

## Order of work

1. `git pull --ff-only` on the profile repo clone, then run the two sed commands and push.
2. Swap badge hexes in the six own-project READMEs. Pure find and replace, one commit each.
3. Reconcile helios `design/tokens.json` to Brass and diff it against the README badge.
4. Re-render the four live README banners (ledge, helios, zest, switchdeck) at 1400x400 in the new palette, and regenerate the uebersicht social preview at 1280x640.
5. Draw the four locked marks (battery cell, collapsing bars, fanned deck, rising bars) as reusable production SVGs on light and dark ground at 512, 24 and 16. The banner PNGs are not a mark set, and a menu bar needs 16px.
6. Apply GitHub labels. Same eight labels everywhere, so a label means the same thing in every repo.
