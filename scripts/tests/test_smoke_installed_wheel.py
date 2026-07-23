#!/usr/bin/env python3
"""Tests for the installed-wheel smoke runner."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.smoke_installed_wheel import run


class InstalledWheelSmokeTest(unittest.TestCase):
    def test_nested_python_uses_utf8_when_parent_requests_legacy_encoding(self) -> None:
        with tempfile.TemporaryDirectory() as raw, patch.dict(
            os.environ,
            {"PYTHONIOENCODING": "cp1252"},
        ):
            result = run(["-c", "print('中文输出')"], cwd=Path(raw))

        self.assertEqual(result.stdout.strip(), "中文输出")


if __name__ == "__main__":
    unittest.main()
