#!/usr/bin/env python3
"""SessionStart status banner for SoloRail v2.7.3."""

import os

from solorail_state import resolve_active_sprint


def main():
    sprints_dir = os.path.join(os.getcwd(), ".solorail", "sprints")
    # The banner must describe the ACTIVE sprint; selecting the last filename
    # could report against a CLOSED one (E03-ISS-02).
    latest = resolve_active_sprint(sprints_dir)
    if not latest:
        return

    in_progress = []
    with open(latest, "r", encoding="utf-8") as f:
        for line in f:
            if "|" not in line:
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 5 and parts[4].upper() == "IN_PROGRESS":
                started = parts[7] if len(parts) > 7 else "-"
                in_progress.append(f"{parts[1]}: {parts[3]} (Started: {started})")

    print(f"=== SoloRail Active Sprint ({os.path.basename(latest)}) ===")
    if in_progress:
        for item in in_progress:
            print(f"IN_PROGRESS -> {item}")
    else:
        print("No issues currently IN_PROGRESS. Run /solorail:next")


if __name__ == "__main__":
    main()
