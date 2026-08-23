#!/usr/bin/env python3
"""Compare the source-built Karpal font with the shipped v1 golden master."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from fontTools.ttLib import TTFont


TABLES = ("cmap", "glyf", "head", "hhea", "hmtx", "loca", "maxp", "name", "OS/2", "post")


def digest_table(font: TTFont, tag: str) -> str:
    return hashlib.sha256(font.getTableData(tag)).hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: verify-karpal.py GOLDEN.ttf BUILT.ttf", file=sys.stderr)
        return 2

    golden_path, built_path = map(Path, sys.argv[1:])
    golden = TTFont(golden_path, recalcBBoxes=False, recalcTimestamp=False)
    built = TTFont(built_path, recalcBBoxes=False, recalcTimestamp=False)

    failures: list[str] = []
    for tag in TABLES:
        if tag not in golden or tag not in built:
            failures.append(f"{tag}: missing table")
            continue
        if digest_table(golden, tag) != digest_table(built, tag):
            failures.append(f"{tag}: table bytes differ")

    if golden.getGlyphOrder() != built.getGlyphOrder():
        failures.append("glyph order differs")

    if failures:
        print("Karpal source verification failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
