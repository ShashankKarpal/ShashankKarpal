# PROGRESS: audit recovery continuation

Started 2026-08-24. Session: Claude Code (Fable 5), single window, no subagents.
Mode approved by Shanky: option (c), Claude executes the bounded scope below,
Codex audits the result afterward. No merges, no pushes without explicit
approval.

A parallel Cowork session is live on this machine (menu bar app promotion,
SwiftBar retirement). Its lane: switchdeck, content-digest-app, SwiftBar
plugin material, menu bar apps. This session stays out of that lane except
for moving the SOP menu bar inventory block, as approved. Expect its commits
on this same branch; each step below re-checks HEAD before writing.

This file names no private consumer repositories on purpose: it is a commit
candidate in a public repository and must keep the private boundary gate
green. Where a step touches private consumers they are called "the private
consumers" or "the private ops extension".

## Scope (approved 2026-08-24)

| # | Item | Status |
|---|---|---|
| 1 | Write PROGRESS.md before any edit | DONE |
| 2 | Boundary regression: move the menu bar inventory block from the public SOP into the private ops extension, leave one generic pointer line; mark the moved block in-flux | DONE |
| 3 | Private boundary gate green (pre-edit state at bbe7b93 re-confirmed: exit 1, BRAND-SURFACES.md) | DONE, exit 0 |
| 4 | Correct the retired-overlay header (both copies, byte-identical): it still describes the removed implicit-load behavior | DONE |
| 5 | Full check-toolchain.sh run on the existing 3.14.7 venv (includes the unittest suite); handoff's python3.11/pytest instructions ignored as approved | DONE, TOOLCHAIN OK, 20 tests pass, Karpal round-trip OK |
| 6 | Execute .github/workflows/brand-integrity.yml locally, step by step | DONE, see log; reproducibility gate caught the interrupted run's missing final rebuild, resolved below |
| 7 | Verify ledge iOS build (build only, no device install) | DONE, BUILD SUCCEEDED, 0 errors |
| 8 | Verify ledge watchOS build (build only) | DONE, LedgeWatch.app built (arm64_32 + arm64) with its widget extension, embedded in Ledge.app/Watch |
| 9 | Verify helios web build | DONE, tsc + vite exit 0, verify:brand exit 0 |
| 10 | Sync the SOP mirror via the private repo's sync script (dry-run, review, apply), re-run both boundary gates after | DONE, both SOP copies byte-identical, gates green; required a sync-script fix, see log |
| 11 | Handoff doc on the Desktop: correct swapped document authorship labels, point the Section 10 prompt at the full audit file | DONE, four surgical corrections marked LABEL CORRECTED 2026-08-24 |

## Closed in the first turn (2026-08-24, verification only)

- Q3 and Q4 recovered verbatim from the parent rollout; both were decided and
  executed on 2026-08-19 (audit items 18 and 13, commit 31d19c5), then
  extended on 2026-08-20. No decision is pending on them.
- ink-and-bone confirmed PRIVATE on GitHub via gh.
- The two private overlay files are two intentional files with distinct
  roles, not a rename.
- Montserrat TTF changes are deliberate re-vendoring from the pinned
  upstream commit; all six recorded SHA-256 hashes match the bytes.
- Parse checks, public boundary gate, WCAG gate: pass. Private boundary
  gate: fail (introduced 2026-08-24 by 8cc3f4d, extended by bbe7b93), fixed
  by item 2 above.

## Deferred (not worked in this session)

- KICKOFF.md on the Desktop carries the same swapped document labels as the
  handoff; only the handoff is corrected under item 11.
- Handoff errata beyond the labels: subagent table (five agents, not three;
  two have rollouts under sessions/2026/08/20/ missed by the recovery
  digest), open item 1 (interpreter: stale, venv is healthy 3.14.7), open
  item 8 (Q3/Q4: recovered, already executed). Documented in the first-turn
  report; handoff text left as written apart from item 11's corrections.
- SOP forensic date for the Homebrew python removal (~2026-08-16 18:05)
  conflicts with the 2026-08-19 audit's claim of a same-day venv rebuild and
  the 2026-08-20 dangling-interpreter finding. Unresolved; low stakes now.
- The retired migration tombstone, CVD advisory model, and consumer
  provenance were reworked during the 2026-08-20 run; Codex's audit should
  re-verify those claims independently.
- Off-account backup: provider choice, key custody, first backup and restore
  drill are owner actions (private ops extension records the policy; drill
  table still pending).
- Release tags (v1.1.0) after everything verifies; merge and push decisions.
- Distributor state after the completed rebuild: --check exits 1 with
  pending updates. Five public consumers pend only their two provenance
  files; zest additionally pends its ten macOS iconset PNGs, which is the
  interrupted run's known unfinished manifest fix. --apply is an
  owner-approved action and was not run.
- The parallel session finalized the moved menu bar inventory in the
  private ops extension and recorded follow-on procedure changes there;
  nothing further needed from this session on that block.
- Two stray hits of a retired commit-message claim: bbe7b93's message says
  the boundary gate was green at commit time; it was not (exit 1 re-confirmed
  at that HEAD). History is not rewritten; recorded here for the audit trail.

## Live verification log

- 2026-08-24: pre-edit gate run at bbe7b93: private boundary exit 1, only
  design/brand/BRAND-SURFACES.md flagged. Public gate, WCAG gate, parse
  checks: pass (first-turn run at 8cc3f4d; public tree unchanged since except
  the SOP file).
- 2026-08-24, after items 2 and 4: overlay copies byte-identical (cmp 0),
  overlay parses; public boundary gate pass (795 paths, this file included);
  private boundary gate PASS exit 0. Regression closed.
- 2026-08-24, item 5: check-toolchain.sh exit 0. uv 0.12.5, python 3.14.7,
  exact lock match (11 packages), cairo 1.18.4, native CairoSVG render OK,
  20/20 unittest regressions OK, Karpal source round-trip matches the v1
  golden master. The handoff's "tests never run / blocked on interpreter"
  item is closed.
- 2026-08-24, item 6, brand-integrity.yml executed locally step by step.
  Deviation from CI recorded: the existing .venv was used instead of a
  recreate, justified by the exact requirements.lock match above.
  verify-palette --self-test exit 0; --no-cvd exit 0; public boundary exit 0;
  regressions 20/20 (inside the toolchain check); full public rebuild exit 0.
  The final reproducibility gate (git diff on design/github, design/marks/out)
  failed on first run, and the diff is fully explained: the committed
  generator (snapshot 70d0406) carries a corrected, extended watchOS icon
  table (22pt slot removed, modern 24/27.5/33 notification, 46/51/54
  launcher, 117/129 quickLook slots added) and per-project web icons, but the
  committed out/ tree predates those generator edits; the interrupted
  2026-08-20 run died before its final rebuild. Evidence of intent: the
  table is in the committed generator; a second rebuild reproduces the
  identical 72-path state (stable status fingerprint), so the new output is
  deterministic; all six regenerated Contents.json parse with 17 slots and
  no 22pt entry; zero pixel churn in any pre-existing PNG (grain determinism
  held). Resolution: regenerated outputs committed; gate then exits 0.
- 2026-08-24, items 7 and 8: ledge project regenerated with xcodegen, built
  unsigned for generic iOS with a scratch derived-data path. BUILD
  SUCCEEDED, zero error lines. Products verified on disk: Ledge.app with
  LedgeWidgets.appex, and Debug-watchos/LedgeWatch.app with a universal
  arm64_32 plus arm64 binary and LedgeWatchWidgets.appex, embedded at
  Ledge.app/Watch/. No device install attempted.
- 2026-08-24, item 9: helios web, npm run build exit 0 (tsc plus vite),
  then npm run verify:brand exit 0: active sources and the fresh bundle
  carry only the current palette. The old reopen item about a retired
  alert hex in the built CSS is closed against a fresh build.
- 2026-08-24, item 10: the mirror sync script refused with nondeterministic
  refusal lists on identical trees (25 flags, then 32, files that exist in
  both trees). Root cause class: the mirror-only comparison ran comm over
  process-substitution FIFOs, and one stream lost a variable-length chunk;
  the flagged names were a contiguous C-sorted range. Separately the guard
  had no classification for formerly-public files legitimately deleted by
  the completed rebuild (the six 22pt watch icons), so any public deletion
  wedged the sync. Fixed in the private repo's script: listings and the
  comm result go through temp files under C collation, and a mirror-only
  path with public git history is announced as a carried deletion while
  unknown paths still refuse. Two consecutive dry-runs byte-identical,
  exit 0; review showed exactly the six known deletions and 78 updates and
  no private path in the transfer; apply exit 0 with the script's own
  sentinel, protected-hash, and private-output digests passing; both SOP
  copies byte-identical afterward; both boundary gates green; synced state
  committed in the private repo.
- 2026-08-24, item 11: handoff corrected in place: 1.2 and 1.3 authorship,
  the 8.1 reading-list labels, and the Section 10 prompt now points at the
  full 31K audit on the Desktop instead of the 1.7K sanitized repo stub.
