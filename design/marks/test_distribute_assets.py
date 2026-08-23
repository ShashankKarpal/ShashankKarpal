#!/usr/bin/env python3
"""Regression tests for the guarded asset distributor."""

from __future__ import annotations

import base64
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import distribute_assets as distributor


class TransformationTests(unittest.TestCase):
    def test_python_base64_replaces_one_parenthesized_assignment(self) -> None:
        original = b'before = 1\nICON = (\n    "b2xk"\n)\nafter = 2\n'
        updated = distributor.replace_python_base64(original, "ICON", b"new payload")
        namespace: dict[str, object] = {}
        exec(updated, namespace)
        self.assertEqual(base64.b64decode(str(namespace["ICON"])), b"new payload")
        self.assertIn(b"before = 1", updated)
        self.assertIn(b"after = 2", updated)

    def test_python_base64_refuses_ambiguous_assignment(self) -> None:
        with self.assertRaises(distributor.DistributionError):
            distributor.replace_python_base64(b'ICON = "b2xk"\n', "ICON", b"new")

    def test_shell_base64_replaces_exact_assignment_only(self) -> None:
        updated = distributor.replace_shell_base64(
            b'KEEP="yes"\nICON="b2xk"\n', "ICON", b"new payload"
        )
        encoded = base64.b64encode(b"new payload")
        self.assertEqual(updated, b'KEEP="yes"\nICON="' + encoded + b'"\n')


class SafetyTests(unittest.TestCase):
    def test_contained_path_rejects_parent_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(distributor.DistributionError):
                distributor.contained_path(Path(directory), "../escape", "test")

    def test_atomic_apply_rolls_back_every_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.txt"
            second = root / "second.txt"
            first.write_bytes(b"first-old")
            second.write_bytes(b"second-old")
            real_replace = os.replace
            forward_calls = 0

            def fail_second_forward(source: os.PathLike[str], destination: os.PathLike[str]) -> None:
                nonlocal forward_calls
                if ".rollback." not in str(source):
                    forward_calls += 1
                    if forward_calls == 2:
                        raise OSError("synthetic write failure")
                real_replace(source, destination)

            with mock.patch.object(distributor.os, "replace", side_effect=fail_second_forward):
                with self.assertRaises(OSError):
                    distributor.apply_atomically(
                        [(first, b"first-new"), (second, b"second-new")]
                    )

            self.assertEqual(first.read_bytes(), b"first-old")
            self.assertEqual(second.read_bytes(), b"second-old")
            self.assertEqual(list(root.glob(".*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
