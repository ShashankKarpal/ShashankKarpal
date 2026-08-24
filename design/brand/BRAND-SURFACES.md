# Brand surfaces checklist (SOP)

Whenever ANY mark, palette value, or brand asset changes, walk this entire
file top to bottom. No surface is done until its verification step passes.
This SOP exists because the 2026-08 Ink and Bone rollout missed surfaces
four separate times: a remote runtime, installed apps, served web icons, and the
watch complication. Every one of those is now a line item here.

Written 2026-08-19. Update this file the moment a new surface appears
(new app, new widget, new machine, new served endpoint).

This PUBLIC file is the normative checklist for public brand rules and
surfaces. Machine addresses, service endpoints, daemon names, private-repo
procedures, and backup operations belong only in the tracked private
operations extension. Complete both documents for a real rollout; never
copy the private extension into a public repository.

## The protocol

1. GENERATE. Edit public geometry or palette only in
   `design/marks/generate_marks.py` and `design/brand/brand-tokens.json`.
   Run public builds without private flags:
   `bash design/brand/run-mark-pipeline.sh [project ...]`. The wrapper exposes
   Homebrew Cairo to the locked Python runtime, and the generator never loads
   an adjacent private overlay implicitly. Private generation is governed by
   the private operations extension. Never hand-edit exports.
   DISTRIBUTE. `rollout-v1-migration.py` is a historical, hard-disabled
   record of the one-time v1 migration; it cannot be run or adapted. Its
   guarded replacement for asset copies is `distribute_assets.py`, driven by
   the visibility-specific consumer manifest. It is non-writing by default:

       .venv/bin/python design/marks/distribute_assets.py --check

   Exit 0 means every declared public asset and provenance file matches;
   exit 1 means updates are pending; exit 2 means a safety check failed.
   Review every reported path. `--apply` is an explicit, separate action,
   refuses a dirty canonical source by default, validates trusted predecessor
   provenance, contains paths, reads every source before writing, guards
   changed destinations, and rolls back a failed batch. The
   `--allow-dirty-source` escape hatch must not be used in a normal release;
   it requires explicit owner approval and records the dirty state. Before
   applying, independently confirm affected consumer worktrees are clean.
   The tool never commits, pushes, builds, deploys, or verifies a runtime.
   CONSUMERS (decision 2026-08-20): consumer repos hold ONLY the declared
   live assets they use plus `design/BRAND-ASSETS.json` and
   `design/BRAND-ASSETS.md` (canonical source commit and dirty state, brand
   version, input hashes, content-set hash, and exact destination hashes).
   They do not carry `design/marks`, the generator, fonts, or canonical
   output matrices; the canonical pipeline is this repo only.
2. REPO SURFACES. Apply per-project sections below. Commit and push every
   touched repo. A change that is not pushed does not exist.
3. INSTALLED SURFACES. Repos hold source; users see builds. Rebuild and
   reinstall each affected application or runtime surface.
4. PRIVATE OPERATIONS. Use the tracked private extension for exact hosts,
   deployed endpoints, installed-copy paths, mirror sync, and backup. Do
   not infer those steps from this public document.
5. VERIFY. Every relevant public and private verification must pass in the
   same session.

## INCIDENT 2026-08-19: private identifier disclosure

The external-critique audit found private source and derived previews in
public history. Containment removed them from every current public tree and
placed the private source and derivatives under the private-only paths.

DECISION (Shanky, 2026-08-19): no history rewrite. The disclosed v1 is
retired permanently as a private identifier. Any future private identifier
must be a wholly new design created and built only in the private system.
Do not add a release tag or other durable reference to a contaminated
historical commit. The detailed incident record remains in the audit; this
SOP records only the durable operational rules. The public audit is a
sanitized summary; the full forensic record is retained privately.

- RULE: private project source lives only in the private extension's
  `design/marks/private_projects.py` and retired `private_marks.py`; derived
  private work lives only under `design/marks/out/private/`. None of those
  paths may be tracked in a public repository. No private-derived preview or
  exploration draft may be committed elsewhere, even as a rejected concept.
- RULE: after any rollout or archive commit, run the public boundary gate and
  the private extension's cross-tree gate before pushing:

      python3 design/brand/check-public-boundary.py

  Both must exit zero. Also inspect the public registry and staged diff for
  private-derived entries or assets before every push.

## Per-project surfaces

### ledge
- [ ] Guarded distributor reports the declared live assets and both
      `design/BRAND-ASSETS` files current; no consumer `design/marks` tree.
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
  iPhone writes do not reach the Mac. Use the private operations extension
  for the local daemon recovery, force-download inbox from the Files app,
  pull to refresh in Ledge, then verify a fresh capture round-trips BOTH ways.
  Note: brctl status is TCC-denied from automation; diagnose by reading
  the shared file and comparing against what each device shows.

### helios
- [ ] Guarded distributor reports the declared live assets and both
      `design/BRAND-ASSETS` files current; no consumer `design/marks` tree.
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
- [ ] npm run build in helios/web. dist is what the deployed service serves
      and it is gitignored, so it MUST be rebuilt on the serving machine;
      patching single files inside dist is a trap (2026-08-19: a stale
      Aug 17 dist shipped the entire old bundle for a day).
- [ ] REBUILD + INSTALL: xcodegen + xcodebuild for Helios Bridge to iPhone
- [ ] VERIFY: use the deployed origin recorded in the private operations
      extension; compare served-file checksums against dist, then load the
      page in a clean browser profile and inspect the tab icon, in-page
      branding, and the iPhone home-screen icon for the bridge app.
- CLIENT CACHES after the server is verified (2026-08-19): Chrome normal
  profile heals with two reloads (SW update then serve). Safari can retain
  its on-disk favicon cache even in private windows; use the private
  operations extension for the TCC-protected local cleanup.
- RESTORED (2026-08-19): the five detailed lines above were added by
  c5b6d82 and ce8809c, then accidentally deleted hours later by 4775655
  (the toolchain commit), which also reintroduced the copy-into-dist trap
  as an instruction. Restored same day during the external-critique audit.
- LESSON: before editing this SOP, read its CURRENT committed state and
  diff your edit against it. Rewriting a section from memory or from an
  earlier read is how same-day incident knowledge got deleted.

### content-digest-app
- [ ] Guarded distributor reports the declared live assets and both
      `design/BRAND-ASSETS` files current; no consumer `design/marks` tree.
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
- [ ] DEPLOYED RUNTIME: pull and verify the serving checkout using the
      private operations extension; static assets are read from disk and
      do not require a service restart.
- [ ] Safari web app on the Dock: icon is SNAPSHOTTED at add time. Delete
      ~/Applications/Content Digest.app and re-add via File > Add to Dock
      (clears its site data; articles live on the server)
- [ ] VERIFY: the deployed asset URL recorded privately serves the expected
      checksum; check the tab favicon after hard reload and Dock icon after
      re-adding the web app.

### zest / switchdeck
- [ ] Guarded distributor reports each repo's declared live assets and both
      `design/BRAND-ASSETS` files current; neither repo has `design/marks`.
- [ ] Zest: all ten PNGs in
      `design/app-icons/macos/AppIcon.appiconset/`. `build.sh` compiles these
      declared live sources into the ignored `Zest.app`; the removed
      consumer `design/marks` snapshot was never a build input.
- [ ] `design/tokens.json` records Ink and Bone v1.1.0 Brass semantics;
      check `knowledge.html` hexes whenever the palette changes.
- [ ] Zest rebuild/reinstall is manual: run `./build.sh`, replace the installed
      application only after reviewing the ignored build, then verify its
      Finder and Dock icon. Do not commit `Zest.app` or a release zip.
- [ ] Switchdeck: if a built app exists on this Mac, rebuild it and check its
      Dock icon.
- [ ] VERIFY: repos pushed; installed app icons checked where applicable.
- DECISION (switchdeck audit 2026-08-17, confirmed 2026-08-24): the
  switchdeck menu bar item is TEXT on purpose. switchdeck.py sets its rumps
  title to an arrow glyph plus the active slot label. The declared live
  assets in design/menubar/SwitchdeckTemplate (png, @2x, @3x, pdf, svg) are
  loaded by nothing, and stay that way: wiring a template icon needs a real
  .app bundle, and that audit moved all bundling to the planned Swift
  MenuBarExtra rewrite rather than spend it on an interim Python surface.
  So this is a declared-live asset with no consumer, by decision. Do not
  diagnose a missing menu bar glyph as a brand asset problem, and do not
  "fix" it by wiring the icon into the Python app.
- SURFACE RENAME (2026-08-24): the LaunchAgent label is now
  com.shashank.switchdeck, the app file is switchdeck.py, and the class,
  notification titles, and notification bundle identifier all say
  SwitchDeck. The old com.shashank.switchbar label is booted out and its
  plist retired by scripts/install.sh. macOS keys notification permissions
  and grouping to the bundle identifier, so that string is now a surface:
  changing it again resets the user's notification choices for this app.
- INCIDENT 2026-08-24: the switchdeck menu bar item was absent. Root cause
  was the Python toolchain, not the brand. Homebrew python@3.14 (3.14.6) was
  removed on or around 2026-08-16 during the uv migration; only python@3.13
  remains in the Cellar. That left two environments whose pyvenv.cfg home
  pointed at the now dangling /opt/homebrew/opt/python@3.14:
  ~/.switchdeck-venv, which is the LaunchAgent program, so
  com.shashank.switchbar failed to spawn with last exit code 78 EX_CONFIG
  and no item ever drew; and the claude-swap uv tool environment, which
  left cswap with a bad interpreter shebang, so even a running switchbar
  would have shown the cswap unavailable row. Fix: rebuild both against the
  uv-managed CPython at ~/.local/bin/python3.14 (uv venv for the switchdeck
  venv plus rumps 0.4.0, uv tool install claude-swap --reinstall), then
  launchctl kickstart -k gui/501/com.shashank.switchbar.
- LESSON: removing or replacing a Homebrew Python silently breaks every venv
  and every uv tool environment whose pyvenv.cfg home points at it, and a
  LaunchAgent failure is invisible because there is no window to miss. After
  any Python version change, check LaunchAgent exit codes and every
  environment under ~/.local/share/uv/tools, not only the repo in hand.

- KNOWN QUIRK (2026-08-24, corrected same day): a rumps menu bar app run
  from a VENV cannot post notifications. rumps resolves
  NSUserNotificationCenter through an Info.plist beside sys.executable and
  needs CFBundleIdentifier in it; a venv has none, so the centre is nil and
  every notification raises. Verified on macOS 26.6.2 as a bare script and
  inside a live rumps run loop. A Homebrew FRAMEWORK Python is different:
  it runs inside Python.app, so the centre exists and notifications deliver,
  but under the identity "Python" (org.python.python). So a fleet rumps app
  either runs from a venv carrying the two-key Info.plist beside its
  interpreter (written at startup, because a venv rebuild silently removes
  it), or it notifies as "Python". The first SOP entry today wrongly said
  content-digest had the same silent-failure exposure; it actually had the
  wrong-identity exposure. Both apps now use the venv-plus-plist pattern:
  switchdeck as com.shashank.switchdeck, content-digest as
  com.shashank.contentdigest (own uv venv at ~/.contentdigest-venv since
  2026-08-24, decision logged in that repo).
- COLLATERAL (2026-08-24): the same Homebrew python@3.14 removal also took
  down com.shashank.contentdigest.client, which ran on
  /opt/homebrew/bin/python3 and failed with the same exit 78. python@3.14
  was reinstalled (3.14.7) for the gcloud virtenv and the AI Centric Catalog
  venv, but neither menu bar app depends on any Homebrew Python any more.
  Still at risk on Homebrew interpreters: speaker-hunter/.venv (python@3.13),
  the gcloud virtenv, and the AI Centric Catalog venv. Dead and orphaned:
  ~/dev/myproject/.venv and ~/mcp-servers/bigquery-mcp/venv (python@3.11,
  removed; nothing live uses them, the BigQuery MCP runs through npx).
  FORENSICS: the removal happened around 2026-08-16 18:05 (the formula's
  emptied Homebrew log directory is the only trace); no shell history line,
  no session log, and no bridge handoff records it. Deliberate uv-migration
  cleanup, not A/B testing, but unrecorded, which is its own failure: the
  cost of the missing one-line log entry was three agents down for days.
  LESSON: after any Python change, sweep the whole fleet, not one app: every
  LaunchAgent exit code, and every pyvenv.cfg home under BOTH $HOME and the
  project roots (the first sweep used -maxdepth 5 and missed repo venvs one
  level deeper). And write the removal down in the session log when it
  happens, not when it bites.
- MENU BAR INVENTORY (2026-08-24), so nobody re-diagnoses this layout:
  four owner surfaces live in the bar. switchdeck (venv python3, text glyph
  by decision), content-digest client (venv python3, its own brand template
  icon, wired at client.py), Zest (Swift .app), and SwiftBar hosting the
  ccusage, claude-burnrate, and claude-bridge plugins from
  ~/SwiftBarPlugins. xbar is INSTALLED BUT RETIRED: /Applications/xbar.app
  is not running and its plugin folder still holds stale June/August copies
  of ccusage.30s.sh and claude-burnrate.1m.sh. SwiftBar is canonical since
  2026-08-16. If xbar is ever launched, those stale copies will draw
  duplicate menu items with outdated logic; delete the app or its plugin
  copies before using it again.
### claude-tokens
- [ ] Guarded distributor reports the declared live assets and both
      `design/BRAND-ASSETS` files current; no consumer `design/marks` tree.
- [ ] README banner SVGs (this repo uses the
      readme-banner-dark.svg / -light.svg names)
- [ ] claude-tokens.widget/index.coffee hexes
- [ ] INSTALLED WIDGET: refresh the running copy at the location recorded in
      the private operations extension; the repo remains source of truth.
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

### Private consumer repositories
- [ ] Complete each affected private-consumer checklist in the private
      operations extension. That extension owns repository identities,
      branch exceptions, installed-copy locations, and runtime verification.
- [ ] Apply the same public asset/provenance/privacy rules to every private
      consumer without copying its operational details back into this file.

### Profile repo (ShashankKarpal/ShashankKarpal)
- [ ] design/github/profile-banner-dark.svg + light (README uses these)
- [ ] design/github/social-preview-1280x640.png (six marks, banner grammar)
- [ ] design/github/avatar-dark.svg + avatar-light.svg, avatar-dark-460.png +
      avatar-light-460.png. Generated by
      `bash design/brand/run-mark-pipeline.sh avatar`; the full
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
- [ ] Regenerate: `bash design/brand/run-mark-pipeline.sh avatar`
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
- NOTE: the avatar deliberately does not use the retired private identifier.
- EXPLORATION: public-safe rejected concepts and the public review sheet from
  the 2026-08-19 session live in design/marks/exploration/. Anything derived
  from private source belongs only under the private output path.

## Accessibility tokens (decision 2026-08-19)

- edge and edgeStrong are DECORATIVE. Anything that must be perceived to
  operate the interface uses controlBorder (3:1 or better on page, card,
  raised, both themes) or stateIndicator (stronger, for selected and
  active states, always paired with a non-colour cue).
- Inline text links carry a PERSISTENT underline and the link token (dark
  #5E92DC, light #3A659D), which clears 4.5:1 on all three surfaces.
  Underline-free treatment only where the navigation role is already
  explicit (buttons, tabs, nav). "No underlines" as a blanket rule is
  retired; underlines never appear as emphasis.
- Values, ratios, and rationale: brand-tokens.json, brand-tokens.css, and
  the amendment in accessibility-report.md.

## Fonts in the repo

- design/brand/font/KarpalGeometric-Regular.{ttf,otf,woff2} - display font,
  wordmarks only, never body text.
- design/brand/font/Montserrat-{Regular,Medium,SemiBold}.{ttf,woff2} - the UI
  family and weights declared in brand-tokens and used by the browser guide.
  Vendored so generated assets and the guide resolve repository-owned fonts
  rather than whatever happens to be installed on the machine. SIL OFL 1.1;
  see MONTSERRAT-LICENSE.md.

## GitHub layer (all repos)

- [ ] Every touched repo: committed, pushed, CI green
- [ ] Social preview upload (MANUAL, settings page): PUBLIC repos only.
      Private repos have no social preview section; the file waits in
      design/marks/web/social-preview-1280x640.png for a visibility flip
- [ ] Labels and README badge hexes if palette changed
- [ ] VERIFY: repo page banner in dark AND light, social card via a link
      paste somewhere private.

## Build toolchain and private-operations handoff

- Python is pinned exactly in `.python-version`; direct dependencies live in
  `requirements.in`; `requirements.lock` pins the full Python dependency
  graph with distribution hashes. The lock was generated and verified with
  uv 0.12.5. Bootstrap a clean environment from the repo root with:

      HOMEBREW_NO_AUTO_UPDATE=1 brew bundle --file Brewfile
      uv python install "$(cat .python-version)"
      uv venv --clear --python "$(cat .python-version)" .venv
      uv pip sync --strict --require-hashes --python .venv/bin/python requirements.lock
      bash design/brand/check-toolchain.sh

- `Brewfile` declares native Cairo, and the check enforces the validated
  Cairo 1.18.4. Homebrew formula resolution is not an immutable native lock:
  if that version is unavailable, stop and deliberately qualify a new
  version or introduce a pinned container/bottle. Do not claim an arbitrary
  current Homebrew install reproduces the validated environment exactly.
- `run-mark-pipeline.sh` delegates to `run-with-brand-env.sh`, which exposes
  Homebrew Cairo to the locked interpreter and suppresses source-tree bytecode.
  Use that environment wrapper for every direct Python command or test that
  can import CairoSVG; a bare `.venv/bin/python` invocation is not a complete
  native runtime on macOS.
- The toolchain check uses that wrapper for an in-memory CairoSVG render and
  the complete generator/distributor regression suite, then rebuilds the
  Karpal source in a temporary directory and verifies its round trip against
  the golden master. A version-only check is not sufficient.
- After a deliberate Python dependency change, update `requirements.in`,
  regenerate the hashed lock, recreate the venv, and run the check:

      uv pip compile requirements.in --generate-hashes \
        --python-version "$(cat .python-version)" --output-file requirements.lock

- DETERMINISM (amended 2026-08-20): raster grain uses the generator's stable
  seeded PRNG and PDF metadata is normalized. Under the locked toolchain, an
  unchanged full rebuild must be byte-identical across SVG, raster, PDF,
  icon, avatar, and QA outputs. The regression suite gates grain and PDF
  determinism. Any unexplained rebuild diff is a failure to investigate; do
  not dismiss it as expected noise or discard it with a destructive checkout.
- [ ] Run the public fleet audit below. Then complete the remote-host,
      installed-copy, private-mirror, and backup checks in the private
      operations extension.

## One-command audit

Run the tracked audit from the canonical repo. It fetches every public repo,
fails nonzero on fetch/status/upstream errors or missing repos, and reports
dirty, ahead, and behind counts:

    bash design/brand/audit-fleet.sh

Pass `--root REPOSITORY_PARENT` when the repos are not siblings of the
canonical checkout. The private operations extension adds the private repo
to the same audit without publishing its identity or location.
