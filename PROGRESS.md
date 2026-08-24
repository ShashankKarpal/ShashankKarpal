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
| 5 | Full check-toolchain.sh run on the existing 3.14.7 venv (includes the unittest suite); handoff's python3.11/pytest instructions ignored as approved | PENDING |
| 6 | Execute .github/workflows/brand-integrity.yml locally, step by step | PENDING |
| 7 | Verify ledge iOS build (build only, no device install) | PENDING |
| 8 | Verify ledge watchOS build (build only) | PENDING |
| 9 | Verify helios web build | PENDING |
| 10 | Sync the SOP mirror via the private repo's sync script (dry-run, review, apply), re-run both boundary gates after | PENDING |
| 11 | Handoff doc on the Desktop: correct swapped document authorship labels, point the Section 10 prompt at the full audit file | PENDING |

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
