#!/usr/bin/env python3
"""Retired Ink and Bone v1 migration marker.

The one-time migration is permanently disabled and must never be reused.
Its full historical implementation is retained only in the private
operations repository. Current manifest-defined asset copies use the
separate guarded `distribute_assets.py`; this marker performs no work.
"""

import sys


def main():
    print(
        "ARCHIVED: the v1 migration is permanently disabled; "
        "follow the current BRAND-SURFACES.md.",
        file=sys.stderr,
    )
    return 64


if __name__ == "__main__":
    sys.exit(main())
