#!/usr/bin/env python3
"""Telemetry evaluator for SoloRail v2.7.3.

Parses Git history, sprint boards, and ROADMAP.md to generate a Markdown report:
1. Sprint Throughput Rate
2. Estimation Accuracy Ratio
3. Unplanned Maintenance Drag
4. Diff Surgicality Rate (from spec receipts & git history)
"""

import glob
import os
import re
import subprocess
from datetime import datetime

from solorail_state import resolve_active_sprint


def run_cmd(cmd: str) -> str:
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT).strip()
    except subprocess.CalledProcessError:
        return ""


def parse_hours(val: str) -> float:
    cleaned = val.strip().lower().rstrip("h").strip()
    if not cleaned or cleaned == "-":
        return 0.0
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def split_row(line: str) -> list[str]:
    parts = re.split(r'(?<!\\)\|', line)
    return [p.strip() for p in parts if p.strip()]


def parse_table(lines: list[str], header_marker: str):
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and header_marker in line:
            start_idx = i
            break
    if start_idx is None:
        return []

    rows = []
    for i in range(start_idx + 2, len(lines)):
        line = lines[i].strip()
        if not line.startswith("|"):
            break
        rows.append(split_row(line))
    return rows


def generate_report():
    solorail_dir = os.path.join(os.getcwd(), ".solorail")
    if not os.path.exists(solorail_dir):
        print("No .solorail directory found.")
        return

    sprints_dir = os.path.join(solorail_dir, "sprints")
    roadmap_path = os.path.join(solorail_dir, "ROADMAP.md")

    # Telemetry must describe the ACTIVE sprint, not whichever file sorts last
    # (E03-ISS-02).
    latest_sprint_file = resolve_active_sprint(sprints_dir)
    if not latest_sprint_file:
        print("No sprint files found.")
        return

    sprint_name = os.path.basename(latest_sprint_file).replace(".md", "")

    with open(latest_sprint_file, "r", encoding="utf-8") as f:
        sprint_lines = f.readlines()

    sprint_rows = parse_table(sprint_lines, "| ID |")

    done_count = 0
    active_count = 0
    total_est_active = 0.0
    total_actual = 0.0

    for cells in sprint_rows:
        if len(cells) < 6 or cells[0].strip() == "-":
            continue
        status = cells[3].upper()
        est = parse_hours(cells[4])
        act = parse_hours(cells[5])

        if status != "CUT":
            active_count += 1
            total_est_active += est
            if status == "DONE":
                done_count += 1
        total_actual += act

    throughput = (done_count / active_count * 100) if active_count > 0 else 0.0
    est_accuracy = (total_actual / total_est_active) if total_est_active > 0 else 0.0

    unplanned_drag = 0.0
    if os.path.exists(roadmap_path):
        with open(roadmap_path, "r", encoding="utf-8") as f:
            rm_lines = f.readlines()

        rm_rows = parse_table(rm_lines, "| Epic ID |")
        total_roadmap_actual = 0.0
        hotfix_actual = 0.0

        for cells in rm_rows:
            if len(cells) < 5:
                continue
            eid = cells[0]
            act = parse_hours(cells[4])
            total_roadmap_actual += act
            if eid == "HOTFIX":
                hotfix_actual += act

        unplanned_drag = (hotfix_actual / total_roadmap_actual * 100) if total_roadmap_actual > 0 else 0.0

    spec_count = len(glob.glob(os.path.join(solorail_dir, "specs", "*-spec.md")))
    verified_count = len(glob.glob(os.path.join(solorail_dir, "specs", "*-verified.json")))
    surgicality_note = f"{verified_count}/{spec_count} architected issues passed verified diff receipts."

    report = f"""# SoloRail Telemetry Report: {sprint_name}
_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_

| Metric | Result | Target | Status |
| :--- | :--- | :--- | :--- |
| **Sprint Throughput Rate** | {done_count}/{active_count} ({throughput:.1f}%) | >= 80% | {'✅' if throughput >= 80 else '⚠️'} |
| **Estimation Accuracy Ratio** | {est_accuracy:.2f} | 0.85 - 1.15 | {'✅' if 0.85 <= est_accuracy <= 1.15 else '⚠️'} |
| **Unplanned Maintenance Drag** | {unplanned_drag:.1f}% | < 15% | {'✅' if unplanned_drag < 15 else '⚠️'} |

## Additional Insights
* **Spec & Diff Verification:** {surgicality_note}
* **Tokens & Cost:** Run `/cost` in Claude Code and log in `Notes / Scope Impact` during `/solorail:verify-issue`.
* **Repeat Mistakes:** Review `.solorail/CONTEXT.md` -> `## 5. Learned Guardrails` for recent regressions.
"""

    os.makedirs(os.path.join(solorail_dir, "retros"), exist_ok=True)
    report_path = os.path.join(solorail_dir, "retros", f"{sprint_name}-telemetry.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Generated SoloRail telemetry report: {report_path}")


if __name__ == "__main__":
    generate_report()
