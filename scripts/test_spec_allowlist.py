#!/usr/bin/env python3
"""Unit tests for spec allowlist parsing (SoloRail E03-ISS-09).

The gate previously substring-matched the whole spec file, so any filename
mentioned in prose -- including in a no-go list -- became writable.

Stdlib-only (unittest). Run with:
    python3 scripts/test_spec_allowlist.py
"""

import glob
import os
import unittest

from spec_allowlist import find_allowlist_section, is_allowlisted, parse_allowlist

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPECS_DIR = os.path.join(REPO_ROOT, ".solorail", "specs")

PROSE_BYPASS_SPEC = """# Technical Spec: X

## Problem

A blanket exemption would unlock `README.md`, which we do not want.

## Allowlisted Files to Create/Modify

- `scripts/a.py` *(modify)* — the only real target

No other file may be touched.

## No-Go Constraints

Must not be touched:

- `scripts/forbidden.py` — belongs to another issue
- `hooks/hooks.json`
"""


class ProseBypassTests(unittest.TestCase):
    def test_prose_mention_is_rejected(self):
        """Test 1: the exact E03-ISS-07 failure."""
        allowed, _ = is_allowlisted("README.md", PROSE_BYPASS_SPEC)
        self.assertFalse(allowed)

        allowed, _ = is_allowlisted("scripts/a.py", PROSE_BYPASS_SPEC)
        self.assertTrue(allowed)

    def test_no_go_entries_are_rejected(self):
        """Test 2: naming a file as forbidden must not authorise it."""
        for path in ("scripts/forbidden.py", "hooks/hooks.json"):
            with self.subTest(path=path):
                allowed, _ = is_allowlisted(path, PROSE_BYPASS_SPEC)
                self.assertFalse(allowed, path)

    def test_parsed_paths_are_exactly_the_allowlist(self):
        self.assertEqual(parse_allowlist(PROSE_BYPASS_SPEC), ["scripts/a.py"])


class HeadingShapeTests(unittest.TestCase):
    """Test 3: every shape used by the existing specs must parse."""

    def _spec(self, heading: str) -> str:
        return (
            "# Spec\n\n## Problem\n\nwords\n\n"
            f"{heading}\n\n- `scripts/target.py` *(modify)*\n\n"
            "## Interface\n\n- `scripts/other.py`\n"
        )

    def test_all_known_headings(self):
        for heading in [
            "## Allowlisted Files",
            "## Allowlisted Files to Create/Modify",
            "## 3. Allowlisted Files to Create/Modify",
            "### 2.2 Allowlisted Files to Create/Modify",
        ]:
            with self.subTest(heading=heading):
                self.assertEqual(
                    parse_allowlist(self._spec(heading)), ["scripts/target.py"], heading
                )

    def test_section_ends_at_next_same_level_heading(self):
        """Test 5: a path under a later section must not leak in."""
        spec = self._spec("## Allowlisted Files to Create/Modify")
        allowed, _ = is_allowlisted("scripts/other.py", spec)
        self.assertFalse(allowed)

    def test_level_three_section_ends_at_level_three(self):
        spec = (
            "# Spec\n\n## 2. Design\n\n### 2.2 Allowlisted Files to Create/Modify\n\n"
            "- `scripts/target.py`\n\n### 2.3 Something Else\n\n- `scripts/other.py`\n"
        )
        self.assertEqual(parse_allowlist(spec), ["scripts/target.py"])


class AmendmentSubsectionTests(unittest.TestCase):
    def test_amendment_subsection_stays_inside(self):
        """Test 4: guards E03-ISS-02 and E03-ISS-04, which record mid-build
        allowlist amendments as ### subsections."""
        spec = (
            "# Spec\n\n## Allowlisted Files to Create/Modify\n\n"
            "- `scripts/a.py` *(modify)*\n"
            "- `scripts/added_later.py` *(modify)* — **added mid-build**\n\n"
            "### Allowlist amendment — 2026-11-25\n\n"
            "Prose explaining why, mentioning `scripts/unrelated.py` in passing.\n\n"
            "## Interface\n\n- `scripts/other.py`\n"
        )
        paths = parse_allowlist(spec)

        self.assertIn("scripts/a.py", paths)
        self.assertIn("scripts/added_later.py", paths)
        self.assertNotIn("scripts/unrelated.py", paths,
                         "prose inside the section is still prose")
        self.assertNotIn("scripts/other.py", paths)


class BulletParsingTests(unittest.TestCase):
    def test_only_first_backtick_token_per_bullet(self):
        """Test 6."""
        spec = (
            "# Spec\n\n## Allowlisted Files\n\n"
            "- `a/b.py` *(modify)* — also uses `c/d.py` internally\n"
        )
        self.assertEqual(parse_allowlist(spec), ["a/b.py"])

    def test_asterisk_bullets_parse(self):
        spec = "# Spec\n\n## Allowlisted Files\n\n* `a/b.py` *(create)*\n"
        self.assertEqual(parse_allowlist(spec), ["a/b.py"])

    def test_non_path_tokens_ignored(self):
        spec = (
            "# Spec\n\n## Allowlisted Files\n\n"
            "- `SomeClassName` — not a path\n"
            "- `scripts/real.py` *(modify)*\n"
        )
        self.assertEqual(parse_allowlist(spec), ["scripts/real.py"])


class ExactMatchTests(unittest.TestCase):
    def test_basename_match_is_rejected(self):
        """Test 7: basename matching was half the hole."""
        spec = "# Spec\n\n## Allowlisted Files\n\n- `scripts/sync_metrics.py` *(modify)*\n"

        allowed, _ = is_allowlisted("vendor/sync_metrics.py", spec)
        self.assertFalse(allowed)

        allowed, _ = is_allowlisted("scripts/sync_metrics.py", spec)
        self.assertTrue(allowed)


class MissingSectionTests(unittest.TestCase):
    def test_missing_section_returns_none_and_blocks(self):
        """Test 8: fail closed, with an actionable reason."""
        spec = "# Spec\n\n## Problem\n\nNo allowlist here, but `scripts/a.py` is mentioned.\n"

        self.assertIsNone(parse_allowlist(spec))
        self.assertIsNone(find_allowlist_section(spec.splitlines(keepends=True)))

        allowed, reason = is_allowlisted("scripts/a.py", spec)
        self.assertFalse(allowed)
        self.assertIn("Allowlisted Files", reason)

    def test_empty_section_blocks_everything(self):
        """An empty list is distinct from None: section present, lists nothing."""
        spec = "# Spec\n\n## Allowlisted Files\n\nNothing yet.\n\n## Next\n"

        self.assertEqual(parse_allowlist(spec), [])
        allowed, _ = is_allowlisted("scripts/a.py", spec)
        self.assertFalse(allowed)


class LiveSpecTests(unittest.TestCase):
    def test_every_live_spec_parses(self):
        """Test 9: catches a heading shape this parser would silently reject."""
        specs = sorted(glob.glob(os.path.join(SPECS_DIR, "*-spec.md")))
        self.assertGreater(len(specs), 0, "no specs found")

        for spec_path in specs:
            with self.subTest(spec=os.path.basename(spec_path)):
                with open(spec_path, encoding="utf-8") as f:
                    paths = parse_allowlist(f.read())
                self.assertIsNotNone(paths, f"{os.path.basename(spec_path)} has no allowlist section")
                self.assertGreater(len(paths), 0, f"{os.path.basename(spec_path)} allowlist is empty")

    def test_e03_specs_authorise_their_own_targets(self):
        """Test 10: asserted against the real spec files."""
        expected = {
            "E03-ISS-01-spec.md": ["scripts/sync_metrics.py", "scripts/test_sync_metrics.py"],
            "E03-ISS-02-spec.md": ["scripts/solorail_state.py", "scripts/compute_actual_hours.py"],
            "E03-ISS-06-spec.md": ["hooks/hooks.json", "scripts/sync_on_git.py"],
            "E03-ISS-07-spec.md": ["scripts/enforce_gate.py", "scripts/test_enforce_gate.py"],
            "E03-ISS-09-spec.md": ["scripts/spec_allowlist.py", "scripts/enforce_gate.py"],
        }

        for name, targets in expected.items():
            path = os.path.join(SPECS_DIR, name)
            if not os.path.exists(path):
                continue
            with open(path, encoding="utf-8") as f:
                spec_text = f.read()
            for target in targets:
                with self.subTest(spec=name, target=target):
                    allowed, reason = is_allowlisted(target, spec_text)
                    self.assertTrue(allowed, f"{name} should authorise {target}: {reason}")

    def test_live_specs_reject_their_no_go_files(self):
        """The inversion that made this bug perverse."""
        path = os.path.join(SPECS_DIR, "E03-ISS-09-spec.md")
        if not os.path.exists(path):
            self.skipTest("spec not present")
        with open(path, encoding="utf-8") as f:
            spec_text = f.read()

        for forbidden in ("scripts/sync_metrics.py", "scripts/next_sprint.py", "hooks/hooks.json"):
            with self.subTest(forbidden=forbidden):
                allowed, _ = is_allowlisted(forbidden, spec_text)
                self.assertFalse(allowed, f"no-go file {forbidden} must not be authorised")


if __name__ == "__main__":
    unittest.main(verbosity=2)
