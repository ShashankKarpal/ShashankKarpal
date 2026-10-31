# Changelog

Ink and Bone follows semantic versioning for the shared specification,
generator, and canonical exports. Consumer applications keep their own product
versions.

## Unreleased (since v1.1.0)

- Added the menutile mark, ibp-07 brass, as the seventh public consumer
  (2026-10-31). Its 11 manifest entries carry `expectedPreviousSha256` set to
  that build, so the distributor accepts those files as trusted predecessors
  when the mark next changes.
- Recorded the Karpal Geometric licence: all rights reserved, for Shashank
  Karpal's own brand and projects only (2026-10-30,
  `design/brand/font/KARPAL-LICENSE-STATUS.md`). Added the canonical brand
  terms, `design/brand/TRADEMARKS.md` (2026-10-31): each public consumer
  keeps a plain MIT LICENSE for its source code and carries a byte-identical
  root TRADEMARKS.md that reserves its name, marks, icons and other brand
  assets wherever they sit, and the typeface.
- The generator writes an upload JPEG beside every social preview PNG
  (quality 92, 4:4:4, optimized) and fails if one reaches 1,000,000 bytes,
  GitHub's limit. New reserved target `profile-social` derives the profile's
  JPEG from its tracked PNG. Every PNG is byte-identical to before.

## v1.1.0: released, tagged 2026-08-24

- Made public generation fail closed and private generation explicitly opt-in.
- Separated public brand rules from private operations and private project data.
- Repaired the locked build environment and added executable toolchain checks.
- Rebuilt accessibility verification, semantic control and link tokens, font
  loading, light-theme evidence, and type-floor compliance.
- Added Montserrat SemiBold 600 and recoverable Karpal Geometric v1 source.
- Added art-directed avatar sizes, small-mark family gates, deterministic grain,
  x-height wordmark rules, and transactional generation.
- Replaced broad consumer snapshots with guarded manifest-driven distribution
  and content-addressed provenance.
- Added privacy, token, output, glyph, retired-colour, and fleet checks.

Prepared as a candidate on 2026-08-20 and tagged `v1.1.0` on 2026-08-24.
The 2026-09-24 and 2026-09-30 author-identity rewrites of this repository's
history moved the tag to the rewritten commit each time; it was not
re-released.

## v1.0.0: retrospective, untagged, retired

The first Ink and Bone rollout shipped on 2026-08-18. It is recorded for
history but deliberately has no Git tag because the reachable historical
commits contain material that was later retired from public use. Do not point a
v1.0.0 tag at those commits.
