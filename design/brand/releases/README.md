# Ink and Bone release policy

Status: normative public release policy.

1. The version in `brand-tokens.json` is the system version. Consumer product
   versions are independent.
2. A release requires clean canonical and private worktrees, a locked clean
   build, privacy verification, accessibility verification, generated-output
   verification, consumer provenance verification, and the live checks scoped
   by the public and private operations documents.
3. Create a signed annotated tag only after those checks pass on committed
   source. Never tag a working tree, a build-only commit, or a historical commit
   that contains retired private material.
4. The canonical release manifest records the public source commit, token-file
   hash, dependency-lock hash, and public output manifest. The private release
   extension records its own commit and private-output manifest without
   publishing private names or paths.
5. Consumers reference the canonical release and exact asset hashes. They do
   not receive brand-system tags or copies of the generator.
6. `v1.0.0` remains a retrospective untagged entry. The first eligible signed
   tag is `v1.1.0` after the 2026-08-20 remediation is reviewed and verified.

No release command in this repository pushes, tags, or publishes by default.
Those actions require an explicit owner decision after reviewing the proposed
commits and the live-check list.
