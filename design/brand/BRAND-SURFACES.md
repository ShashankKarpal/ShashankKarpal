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
   Private geometry lives ONLY in `design/marks/private_marks.py`
   (gitignored; see INCIDENT 2026-08-19). Run
   `.venv/bin/python design/marks/generate_marks.py [project ...]`, then
   `rollout.py` for multi-repo changes. Never hand-edit exports.
   NOTE: the copies of generate_marks.py inside the nine consumer repos are
   sanitized snapshots for reference; they cannot regenerate wordmarks
   (fonts are not vendored there) and must never gain private entries. The
   canonical pipeline is this repo only.
2. REPO SURFACES. Apply per-project sections below. Commit and push every
   touched repo. A change that is not pushed does not exist.
3. INSTALLED SURFACES. Repos hold source; users see builds. Rebuild and
   reinstall every app, widget, and daemon output listed below.
4. REMOTE MACHINES. The M1 does not update itself reliably. Verify.
5. MIRROR. Refresh the ink-and-bone private backup repo.
6. VERIFY. Every section has a verification step. Do them all, same session.

## INCIDENT 2026-08-19: the monogram was public

Found by the external-critique audit (design/brand/reviews/). The private
sk monogram had leaked in two ways, both live on GitHub:

1. Its full geometry sat in the MARKS registry inside generate_marks.py,
   tracked in this PUBLIC repo since the initial rollout PR (d59f72f), and
   copied byte-identically by rollout.py into all nine consumer repos, six
   of which are public (ledge, content-digest-app, helios, zest,
   switchdeck, claude-tokens).
2. Two rendered images (round1-a-monogram.png and round1-contact-sheet.png)
   were committed to design/marks/exploration/ in this public repo by the
   avatar session (f473bb9), beside a README saying the concept must never
   ship.

Containment, done 2026-08-19: geometry moved to design/marks/
private_marks.py (gitignored here, tracked only in the ink-and-bone
mirror); generate_marks.py now loads it as an optional overlay and fails
closed without it; the two renders moved to design/marks/out/private/
exploration/; sanitized generate_marks.py pushed to all nine consumers.

STILL OPEN: the monogram remains in the git HISTORY of this repo and the
nine consumers until histories are rewritten (git filter-repo plus force
push, then M1 re-clone) or Shanky decides to treat the v1 monogram as
disclosed and redesign it. His call, asked 2026-08-19.

- RULE (new): private geometry lives ONLY in private_marks.py and
  out/private/. Nothing derived from a private mark (renders, contact
  sheets, exploration drafts) may be committed outside out/private/, even
  as a rejected concept. gitignore covers both paths.
- RULE (new): after any rollout or archive commit, run the privacy check
  in EVERY touched repo before pushing. Both commands must print nothing:

      git ls-files design/marks/out/private design/marks/private_marks.py
      git grep -n "PRIVATE_MARKS = " -- design/marks/generate_marks.py

  and design/marks/generate_marks.py must not contain a "monogram" entry
  in its MARKS registry (the geometry lives only in private_marks.py).

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
- [ ] web/tailwind.config.js colour block. RESOLVED DRIFT (2026-08-19): it
      still carried the ENTIRE pre-Ink-and-Bone palette (bg #0B0D0C, text
      #E8ECE9, mint #7EE0B1, alert #F87171 and friends) a day after
      rollout, because rollout.py only walked web/src and the src files use
      Tailwind CLASSES, not hexes. The live UI therefore rendered the old
      palette everywhere. Swapped to Ink and Bone values per the rollout
      mapping (alert -> problem #CB5B45). Any future palette change MUST
      touch this file and then npm run build.
- [ ] design/brand/README.md and design/brand/tokens/ snippets still
      describe the old mint system; README now carries a superseded header
      (2026-08-19). Retire or rewrite when next touched.
- [ ] design/brand: icon-composer layers (background, hub, line, mono),
      print letterhead, lockups
- [ ] design/brand/sf-symbol: still carries meridian-named files; regenerate
      or retire when next touched (known open item, 2026-08-19)
- [ ] ios-bridge/Assets.xcassets/AppIcon.appiconset (3x 1024 pngs) and the
      reference copies in design/brand/app-icons/ios-bridge
- [ ] web/public COMPLETE asset set, not just favicon.svg: favicon.svg,
      favicon.ico, icon.svg, icon-maskable.svg, icons/icon-192.png,
      icons/icon-512.png, icons/icon-512-maskable.png, apple-touch-icon.png,
      splash/*.png (9 sizes). Safari tabs use apple-touch-icon, Chrome can
      use manifest icons; fixing favicon.svg alone changes nothing visible.
- [ ] web/public/sw.js: bump the CACHE version string, or every returning
      browser keeps serving the old assets cache-first.
- [ ] npm run build in helios/web. dist is what heliosd serves on :8420
      and it is gitignored, so it MUST be rebuilt on the serving machine;
      patching single files inside dist is a trap (2026-08-19: a stale
      Aug 17 dist shipped the entire old bundle for a day).
- [ ] REBUILD + INSTALL: xcodegen + xcodebuild for Helios Bridge to iPhone
- [ ] VERIFY: curl the SERVED files on https://helios.local:8420 and
      compare shasum against dist, then load the page in CHROME INCOGNITO
      (the only clean client) and look at the tab icon and in-page branding.
      iPhone home screen icon for the bridge app.
- CLIENT CACHES after the server is verified (2026-08-19): Chrome normal
  profile heals with two reloads (SW update then serve). Safari uses its
  on-disk Favicon Cache even in PRIVATE windows; the fix is quit Safari,
  rm -rf ~/Library/Safari/"Favicon Cache", reopen. That folder is
  TCC-protected from automation; Shanky runs it in his own Terminal.
- RESTORED (2026-08-19): the five detailed lines above were added by
  c5b6d82 and ce8809c, then accidentally deleted hours later by 4775655
  (the toolchain commit), which also reintroduced the copy-into-dist trap
  as an instruction. Restored same day during the external-critique audit.
- LESSON: before editing this SOP, read its CURRENT committed state and
  diff your edit against it. Rewriting a section from memory or from an
  earlier read is how same-day incident knowledge got deleted.

### content-digest-app
- [ ] design/marks export tree
- [ ] design/web SERVED icons: favicon.svg, favicon-16/32/48.png,
      favicon.ico, apple-touch-icon.png, icon-192, icon-512,
      icon-512-maskable, og-1200x630 (server.py serves these at /assets/)
- [ ] extension/manifest.json icons if the extension ships artwork
- [ ] server.py and extension/options.html inline style hexes. RESOLVED
      DRIFT (2026-08-19): both still used the retired #ff6b35 accent a day
      after rollout because that hex was never in rollout.py's mapping.
      Swapped to copper #B17E51.
- LESSON: after any palette rollout, grep every touched repo for the OLD
  hexes (all of them, including pre-brand accents like #ff6b35), not just
  the ones the mapping happened to know about.
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
- RESOLVED DRIFT (2026-08-19): the repo was renamed uebersicht-claude-tokens
  to claude-tokens on 2026-08-18 (profile repo c396f32, widget repo b2b9126).
  That session renamed the MARKS key and references but left the export
  folder as out/uebersicht-claude-tokens/, so the tree was stale under the
  old name for a day, and the rename was never recorded here, which is how
  the next session mis-read which name was canonical. Fixed 2026-08-19:
  exports regenerated fresh under out/claude-tokens/ (template PNGs inside
  now carry the right names too), stale folder deleted.
- LESSON: a repo rename is a full SOP walk, and that includes the export
  tree under design/marks/out/ AND a line in this file naming old and new.
  The MARKS key, the folder, and the template filenames inside it must all
  agree before the rename is done.

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
- RESOLVED (2026-08-19): xbar wedged into blank items twice in one day
  (second time after a sleep/wake), so it is RETIRED. ccusage.30s.sh and
  claude-burnrate.1m.sh now live in ~/SwiftBarPlugins next to
  claude-bridge.2m.sh; SwiftBar is the ONLY menu bar plugin host. xbar was
  quit and removed from login items; stale copies remain in
  ~/Library/Application Support/xbar/plugins but nothing runs them.
  Do not reintroduce xbar. Refresh plugins with
  open swiftbar://refreshallplugins after any plugin edit.

### claude-skills-workspace
- [ ] design/marks export tree only. Branch is MASTER, not main.

### Profile repo (ShashankKarpal/ShashankKarpal)
- [ ] design/github/profile-banner-dark.svg + light (README uses these)
- [ ] design/github/social-preview-1280x640.png (six marks, banner grammar)
- [ ] design/github/avatar-dark.svg + avatar-light.svg, avatar-dark-460.png +
      avatar-light-460.png. Generated by
      `.venv/bin/python design/marks/generate_marks.py avatar`; the full
      size matrix (460, 400, 200, 80, 40, 20) lands in
      design/marks/out/github/avatar/. Never hand-edit either copy.
- [ ] design/github/profile-banner-dark.svg + light are the ONLY banner
      files; the stale -1400x400.png pair (pre-Ink-and-Bone palette) was
      removed 2026-08-19. The README embeds the SVGs. If PNG banners are
      ever needed again, generate them from the current SVGs, never revive
      the deleted pair.
- [ ] VERIFY: profile page renders both themes.

### GitHub account avatar (account-level, not a repo file)
Added 2026-08-19. This is the only surface on the list that no push can
change, and the easiest one to believe is done when it is not.
- LIVE VARIANT: avatar-light-460.png, uploaded by Shanky 2026-08-19. The
  light ground was his call; if the avatar is ever regenerated, light is
  the file to re-upload unless he says otherwise.
- [ ] Regenerate: `.venv/bin/python design/marks/generate_marks.py avatar`
- RESOLVED (2026-08-19): the generated out/github/avatar/README.md used to
  say "upload avatar-dark-460.png", contradicting the LIVE VARIANT line
  below. The generator text now names the light file. LESSON: when an owner
  decision changes a generated file's instructions, regenerate the file in
  the same session; a stale generated README is a regression path.
- [ ] UPLOAD (MANUAL): github.com/settings/profile, upload
      design/github/avatar-light-460.png (see LIVE VARIANT above), then Set
      new profile picture and confirm the crop (GitHub offers a crop step
      even on a square file)
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
- EXPLORATION: the rejected concepts and both contact sheets from the
  2026-08-19 design session live in design/marks/exploration/, per the
  standing rule that all artwork produced for this brand lands in this
  repo, not in a chat scratchpad.

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

- [ ] M4 TOOLCHAIN (resolved 2026-08-19): the pipeline runs on the M4 via
      the repo venv. Rebuild any target with:

          cd ~/Projects-with-Claude/shashankkarpal
          .venv/bin/python design/marks/generate_marks.py [project ...]

      Setup that made it work: brew install cairo (1.18.4), then
      uv venv --python /opt/homebrew/bin/python3 .venv, then uv pip install
      --python .venv/bin/python -r requirements.lock. The venv is
      gitignored; if it is ever missing (new machine, fresh clone), those
      three lines recreate it EXACTLY.
- PINNED (2026-08-19): .python-version (3.14) and requirements.lock at the
  repo root record the working toolchain (cairosvg 2.9.0, pillow 12.3.0,
  fonttools 4.63.0, icnsutil 1.1.0, python 3.14.7, native cairo 1.18.4 via
  Homebrew). After any deliberate upgrade, regenerate the lock with
  uv pip freeze --python .venv/bin/python > requirements.lock and rebuild
  one project to confirm, in the same session.
- KNOWN QUIRK (2026-08-19): rebuilt PNGs are never byte-identical to the
  committed ones even when nothing changed. Pillow's effect_noise (the
  grain) is not seedable, so every run lays fresh grain. Verified: SVGs
  byte-identical, PNG mean pixel delta about 2.5/255, pure noise. So a
  dirty git status full of PNGs after a rebuild does NOT mean the marks
  changed. Diff an SVG to know the truth; git checkout the PNGs if the
  SVGs are clean and you did not intend a change.
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

Run on the M4 to catch unpushed, unpulled, or missing work across the
fleet. Unlike the earlier version, this one fetches first, fails loudly on
a missing repo or missing upstream, and reports behind as well as ahead:

    fail=0
    for r in ledge content-digest-app helios zest switchdeck claude-tokens \
             claude-bridge claude-burnrate claude-skills-workspace \
             shashankkarpal ink-and-bone; do
      d=/Users/shashank.kk/Projects-with-Claude/$r
      if [ ! -d "$d/.git" ]; then echo "$r: MISSING REPO"; fail=1; continue; fi
      cd "$d"; git fetch -q 2>/dev/null
      if ! git rev-parse --abbrev-ref @{u} >/dev/null 2>&1; then
        echo "$r: NO UPSTREAM"; fail=1; continue; fi
      s=$(git status --short | wc -l | tr -d ' ')
      a=$(git rev-list --count @{u}..HEAD); b=$(git rev-list --count HEAD..@{u})
      [ "$s$a$b" != "000" ] && fail=1
      echo "$r: dirty=$s ahead=$a behind=$b"
    done; [ $fail = 0 ] && echo "FLEET CLEAN" || echo "FLEET INCOMPLETE"
