#!/usr/bin/env python3
"""Test that evolve skill wiring calls next_sprint.py via the script."""

import sys
import os

# Read the evolve skill file
skill_path = "/Users/menilub/.claude/plugins/cache/solorail/solorail/0.4.0-beta/skills/evolve/SKILL.md"

try:
    with open(skill_path, 'r') as f:
        content = f.read()
except FileNotFoundError:
    print(f"ERROR: Evolve skill not found at {skill_path}")
    sys.exit(1)

# TEST 1: Skill must reference next_sprint.py
print("TEST 1: Evolve skill mentions next_sprint.py...")
if "next_sprint.py" not in content:
    print("FAIL: next_sprint.py not mentioned in evolve skill")
    sys.exit(1)
print("PASS")

# TEST 2: Skill must call it via CLAUDE_PLUGIN_ROOT
print("TEST 2: Evolve skill calls it with CLAUDE_PLUGIN_ROOT...")
if '${CLAUDE_PLUGIN_ROOT}/scripts/next_sprint.py' not in content:
    print("FAIL: script not called with CLAUDE_PLUGIN_ROOT variable")
    sys.exit(1)
print("PASS")

# TEST 3: Skill must NOT ask the user to hand-author
print("TEST 3: Evolve skill does NOT ask user to hand-author...")
old_wording = "Ask the user if they want to initialize"
if old_wording in content:
    print(f"FAIL: Old wording still present: '{old_wording}'")
    sys.exit(1)
print("PASS")

print("\nAll tests passed.")
sys.exit(0)
