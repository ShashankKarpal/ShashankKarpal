# Ink and Bone documentation map

This directory contains the public, normative part of the Ink and Bone brand
system. Private operations and private project definitions live in the private
mirror and are never copied into this repository.

## Authority order

1. `brand-tokens.json` is the machine-readable source of truth for colour,
   typography, spacing, grain, and mark-use constraints.
2. `BRAND-SURFACES.md` is the public operating procedure for applying those
   tokens to repositories and product surfaces.
3. `releases/README.md` defines versioning, release evidence, and tag policy.
4. If a derived file conflicts with one of the three sources above, the
   derived file is wrong and must be regenerated or corrected.

## Derived references

- `brand-tokens.css` is the web binding of the canonical JSON tokens.
- `shanky-brand-guide.html` is the browser visual guide and component specimen.
  Keep it beside `font/` so its three vendored Montserrat web fonts resolve.
- `accessibility-report.md` records current contrast evidence, advisory colour
  vision simulation, and typography constraints.
- `font/` contains the vendored runtime fonts, licenses, provenance, and the
  lossless editable source for the custom display face.

## Executable checks and builds

- `verify-palette.py` gates normative WCAG role pairs and token/CSS binding.
- `check-public-boundary.py` verifies the public project allowlist and rejects
  tracked private-capable mark paths.
- `check-toolchain.sh` verifies the pinned interpreter, dependency graph,
  native Cairo dependency, and custom-font rebuild.
- `run-mark-pipeline.sh` runs the mark generator through the locked local
  environment.
- `run-with-brand-env.sh` exposes the same pinned Python and native Cairo
  environment to regression tests and other explicit commands.
- `audit-fleet.sh` performs a fail-loud public consumer audit.
- `../marks/distribute_assets.py` checks or applies the explicit consumer
  manifests and writes machine-verifiable provenance in each consumer.

## Historical and exploratory material

- `reviews/` contains sanitized historical review records. It is evidence, not
  current instruction.
- `exploration/` and `../marks/exploration/` contain retained public studies.
  They are not approved production assets.
- The full external remediation record is private. The public review summary
  intentionally omits private project, infrastructure, and retired-mark detail.

Production assets are the generated files declared by the mark pipeline and
consumer manifests. Do not copy a draft, contact sheet, or historical export
into an application merely because it is present in the repository.
