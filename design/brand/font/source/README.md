# Karpal Geometric v1 source recovery

Status: archival, rebuildable source for the shipped v1 font.

The original drawing source was not present in either brand repository or its
reachable history during the 2026-08-20 audit. `KarpalGeometric-Regular.ttx`
is a lossless XML decompilation of the shipped TrueType golden master. It
preserves outlines, metrics, character mapping, names, and OpenType tables in
an editable, versionable form. It is suitable for repairs and deterministic
reconstruction, though a UFO or Glyphs source may be more comfortable for a
future redesign.

The shipped `../KarpalGeometric-Regular.ttf` remains the v1 golden master.
Do not replace it merely because a compiler emits different container bytes.
Run `./build-karpal.sh` to rebuild and compare the semantic font tables.

The font's distribution terms are not inferred here. See
`../KARPAL-LICENSE-STATUS.md` before using it outside Shashank Karpal's own
repositories and products.
