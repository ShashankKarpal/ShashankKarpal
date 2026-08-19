# Brand surfaces checklist (SOP)

Whenever ANY mark, palette value, or brand asset changes, walk this entire
file top to bottom. No surface is done until its verification step passes.
This SOP exists because the 2026-08 Ink and Bone rollout missed surfaces
four separate times: the M1, installed apps, served web icons, and the
watch complication. Every one of those is now a line item here.

Written 2026-08-19. Update this file the moment a new surface appears
(new app, new widget, new machine, new served endpoint).

## The protocol

1. GENERATE. Edit geometry or palette only in
   `shashankkarpal/design/marks/generate_marks.py` (and brand-tokens.json).
   Run `python3 generate_marks.py [project ...]`, then `rollout.py` for
   multi-repo changes. Never hand-edit exports.
2. REPO SURFACES. Apply per-project sections below. Commit and push every
   touched repo. A change that is not pushed does not exist.
3. INSTALLED SURFACES. Repos hold source; users see builds. Rebuild and
   reinstall every app, widget, and daemon output listed below.
4. REMOTE MACHINES. The M1 does not update itself reliably. Verify.
5. MIRROR. Refresh the ink-and-bone private backup repo.
6. VERIFY. Every section has a verification step. Do them all, same session.

## Per-project surfaces

### ledge
- [ ] design/marks export tree (from pipeline)
- [ ] design/github banners + design/logo SVGs
- [ ] apps/ios: iOS AppIcon.appiconset, watch AppIcon.appiconset
- [ ] apps/ios/WatchWidgetSources LedgeStep.imageset (watch COMPLICATION glyph)
- [ ] apps/ios/WidgetSources LedgeStep.imageset (iOS widget glyph)
- [ ] apps/mac/Resources/Ledge.iconset (build-mac.sh compiles this, NOT design/marks)
- [ ] apps/mac/Resources/MenuBarIconTemplate 1x/2x/3x at 18/36/54 px (not 22/44/66)
- [ ] REBUILD + INSTALL: ./scripts/deploy.sh all (Mac /Applications, iPhone, Watch)
- [ ] VERIFY: Mac Dock icon (killall Dock if cached), iPhone home screen,
      watch app icon, complication on the face (remove + re-add to bust
      the watchOS snapshot cache), menu bar glyph.
- KNOWN QUIRK (2026-08-19): reinstalling the iPhone app via devicectl can
  invalidate the security-scoped folder bookmark. Symptom: Mac notes stop
  appearing on the iPhone while Watch capture still works (WatchConnectivity
  is direct). Captures are safe in the app's local pending-captures.md.
  Fix: tap the folder icon (top-left, always visible since 2026-08-19) and
  re-pick iCloud Drive > Ledge. ALWAYS verify sync end to end after any
  iPhone reinstall: capture on Mac, confirm on iPhone.
  History: the button used to appear only when isConnected was false, and
  two state bugs (ignored startAccessingSecurityScopedResource result,
  refresh() never clearing isConnected on failure) kept it hidden while
  sync was dead. Fixed same day; do not regress the always-visible button.
- KNOWN QUIRK (2026-08-19): even with the app healthy, iCloud Drive
  transport itself can wedge. Symptoms: the iPhone holds inbox.md as a
  grayed dataless placeholder in Files (app cannot show Mac notes), and
  iPhone writes do not reach the Mac. Fix, in order: on the Mac run
  killall bird fileproviderd (daemons restart and resync); on the iPhone
  open the Ledge folder in Files and tap inbox to force-download; pull to
  refresh in Ledge; then verify a fresh capture round-trips BOTH ways.
  Note: brctl status is TCC-denied from automation; diagnose by reading
  the shared file and comparing against what each device shows.

### helios
- [ ] design/marks export tree
- [ ] design/brand: icon-composer layers (background, hub, line, mono),
      print letterhead, lockups
- [ ] design/brand/sf-symbol: still carries meridian-named files; regenerate
      or retire when next touched (known open item, 2026-08-19)
- [ ] ios-bridge/Assets.xcassets/AppIcon.appiconset (3x 1024 pngs) and the
      reference copies in design/brand/app-icons/ios-bridge
- [ ] web/public/favicon.svg + favicon.ico AND web/dist copies (vite build
      output; either npm run build or copy into dist directly)
- [ ] REBUILD + INSTALL: xcodegen + xcodebuild for Helios Bridge to iPhone
- [ ] VERIFY: https://helios.local:8420 tab icon (hard reload; Safari
      favicon cache is stubborn), iPhone home screen icon.

### content-digest-app
- [ ] design/marks export tree
- [ ] design/web SERVED icons: favicon.svg, favicon-16/32/48.png,
      favicon.ico, apple-touch-icon.png, icon-192, icon-512,
      icon-512-maskable, og-1200x630 (server.py serves these at /assets/)
- [ ] extension/manifest.json icons if the extension ships artwork
- [ ] M1 RUNTIME: repo must be pulled on the M1 (see Machines below);
      server reads assets from disk, no restart needed for icons
- [ ] Safari web app on the Dock: icon is SNAPSHOTTED at add time. Delete
      ~/Applications/Content Digest.app and re-add via File > Add to Dock
      (clears its site data; articles live on the server)
- [ ] VERIFY: http://100.112.78.47:7778/assets/icon-512.png serves the new
      file, tab favicon after hard reload, Dock icon after re-add.

### zest / switchdeck
- [ ] design/marks export tree, design/tokens.json, knowledge.html hexes
- [ ] If a built .app exists on this Mac, rebuild it; check its Dock icon
- [ ] VERIFY: repo pushed, installed app icon if applicable.

### claude-tokens
- [ ] design/marks export tree, README banner svgs (this repo uses the
      readme-banner-dark.svg / -light.svg names)
- [ ] claude-tokens.widget/index.coffee hexes
- [ ] INSTALLED Uebersicht widget copy in
      ~/Library/Application Support/Übersicht/widgets (repo is source, the
      widget folder is the running copy)
- [ ] Gallery zip claude-tokens.widget.zip regenerated by CI on push to main
- [ ] VERIFY: widget on the desktop after Uebersicht refresh.
- OPEN DRIFT (found 2026-08-19): the export folder on disk is
  design/marks/out/uebersicht-claude-tokens/, but the MARKS key in
  generate_marks.py is still claude-tokens. So `generate_marks.py
  claude-tokens` writes a SECOND folder, out/claude-tokens/, and the
  uebersicht- one goes stale without anyone noticing. Pick one name, rename
  the MARKS key or the folder to match, and delete the loser. Until then,
  check which folder a consumer actually reads before trusting it.

### claude-bridge
- [ ] design/marks export tree
- [ ] bin/bridge.py MENUBAR_ICON base64 constant (44 px, 144 dpi template
      png; regenerate from design/marks/macos/claude-bridge-template@2x.png)
- [ ] SwiftBar plugin reads bridge.py live, no reinstall; refresh with
      open swiftbar://refreshallplugins
- [ ] VERIFY: menu bar shows the span mark, not a text B.

### claude-burnrate
- [ ] design/marks export tree
- [ ] burnrate-report.sh ICON base64 constant (same recipe as bridge)
- [ ] INSTALLED COPY: cp burnrate-report.sh to
      ~/.claude/statusline/burnrate-report.sh (the xbar plugin execs the
      installed copy, NOT the repo)
- [ ] Uebersicht burnrate widget if styled artwork is added later
- [ ] VERIFY: menu bar shows the burn line mark.
- KNOWN QUIRK (2026-08-19): xbar can wedge into rendering ALL its items
  blank (hover highlight only, dark and light). Plugins are fine; fix is
  killall xbar and relaunch. xbar is unmaintained; if it recurs, migrate
  ccusage.30s.sh and claude-burnrate.1m.sh to ~/SwiftBarPlugins and retire
  xbar (SwiftBar renders both, proven by claude-bridge).

### claude-skills-workspace
- [ ] design/marks export tree only. Branch is MASTER, not main.

### Profile repo (ShashankKarpal/ShashankKarpal)
- [ ] design/github/profile-banner-dark.svg + light (README uses these)
- [ ] design/github/social-preview-1280x640.png (six marks, banner grammar)
- [ ] design/github/avatar-dark.svg + avatar-light.svg, avatar-dark-460.png +
      avatar-light-460.png. Generated by `generate_marks.py avatar`; the full
      size matrix (460, 400, 200, 80, 40, 20) lands in
      design/marks/out/github/avatar/. Never hand-edit either copy.
- [ ] VERIFY: profile page renders both themes.

### GitHub account avatar (account-level, not a repo file)
Added 2026-08-19. This is the only surface on the list that no push can
change, and the easiest one to believe is done when it is not.
- [ ] Regenerate: `python3 design/marks/generate_marks.py avatar`
- [ ] UPLOAD (MANUAL): github.com/settings/profile, upload
      design/github/avatar-dark-460.png, then Set new profile picture and
      confirm the crop (GitHub offers a crop step even on a square file)
- [ ] VERIFY in three places, not one: the profile page, a comment in a
      public repo, and a commit list. Org member lists and PR reviewer
      chips cache separately and lag the others.
- KNOWN QUIRK (2026-08-19): avatars are served from
  avatars.githubusercontent.com with a long cache and a rolling ?v= suffix,
  so a normal reload keeps showing the old picture for a while. Verify in a
  private window or on another device. Do NOT re-upload because the old one
  is still showing; that is the cache, not a failed upload.
- DECISION (2026-08-19): the avatar carries copper in the contribution
  field. brand-tokens rule 2 says the profile repo stays ink. Shanky
  approved copper here explicitly after seeing the alternatives, so this is
  a recorded exception, not drift. Everything else in the profile repo still
  stays ink.
- DESIGN NOTE: the layout puts the copy inside a card on purpose. The three
  lines are 10.5 to 15px and brand-tokens forbids grain under type below
  14px, so the card is what keeps the composition legal. If the card is ever
  removed, the copy has to grow or the grain has to go.
- NOTE: the avatar deliberately does NOT use the sk monogram. The monogram
  stays private per design/marks/out/private/README-PRIVATE.md.

## Fonts in the repo

- design/brand/font/KarpalGeometric-Regular.{ttf,otf,woff2} - display font,
  wordmarks only, never body text.
- design/brand/font/Montserrat-Regular.ttf, Montserrat-Medium.ttf - the UI
  font declared as font.ui in brand-tokens. Vendored 2026-08-19 so the
  avatar copy renders from the repo rather than from whatever happens to be
  installed on the machine, which is the whole point of this system
  surviving the M4. SIL OFL 1.1, see MONTSERRAT-LICENSE.md.

## GitHub layer (all repos)

- [ ] Every touched repo: committed, pushed, CI green
- [ ] Social preview upload (MANUAL, settings page): PUBLIC repos only.
      Private repos have no social preview section; the file waits in
      design/marks/web/social-preview-1280x640.png for a visibility flip
- [ ] Labels and README badge hexes if palette changed
- [ ] VERIFY: repo page banner in dark AND light, social card via a link
      paste somewhere private.

## Machines

- [ ] M4 TOOLCHAIN: generate_marks.py needs cairosvg, pillow, fonttools,
      icnsutil. OPEN ITEM (2026-08-19): none of the Mac interpreters has
      cairosvg (/opt/homebrew/bin/python3, python3.13, python3.14,
      /usr/bin/python3), so the documented rebuild command does not actually
      run on the M4 today. The 2026-08-19 avatar exports were produced by
      this same script, same fonts, same seeds, in a Linux environment that
      had the deps. Deterministic, but it means the M4 cannot currently
      regenerate its own brand assets. FIX WHEN NEXT TOUCHED: brew install
      cairo, create a venv inside the profile repo, install the four deps,
      and record the interpreter path on this line.
- [ ] M4: every repo clean and pushed (git status loop, see below)
- [ ] M1 (shashankkarpal@100.112.78.47): pull per repo. The
      com.shashank.autodeploy launchd job has stalled before (2026-08-19);
      never assume it ran. Never edit on the M1.
      As of 2026-08-19 the M1 has ONE clone: ~/content-digest-app
- [ ] M1: restart the affected service only if server code changed;
      static assets are read from disk per request
- [ ] ink-and-bone mirror: rsync shashankkarpal/design into the mirror,
      commit, push (PRIVATE, holds the monogram)
- [ ] VERIFY: ssh m1 git log -1 matches origin; mirror repo pushed.

## One-command audit

Run on the M4 to catch unpushed work across the fleet:

    for r in ledge content-digest-app helios zest switchdeck claude-tokens \
             claude-bridge claude-burnrate claude-skills-workspace \
             shashankkarpal ink-and-bone; do
      cd /Users/shashank.kk/Projects-with-Claude/$r 2>/dev/null || continue
      s=$(git status --short | head -3); a=$(git log --oneline @{u}.. 2>/dev/null | wc -l)
      echo "$r: dirty=$([ -n "$s" ] && echo YES || echo no) unpushed=$a"
    done
