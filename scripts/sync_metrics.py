#!/usr/bin/env python3
"""Deterministic metrics synchronizer for SoloRail v2.7.3.

Parses active sprint boards (.solorail/sprints/sprint-*.md) and updates:
1. Each sprint file's 'Time & Velocity Summary' block.
2. .solorail/ROADMAP.md 'Est. Hours' and 'Actual Hours' per Epic and HOTFIX.
"""

import glob
import os
import re


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


def parse_markdown_table(lines: list[str], header_marker: str):
    start_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and header_marker in line:
            start_idx = i
            break
    if start_idx is None:
        return None, None, []

    rows = []
    end_idx = start_idx + 2
    for i in range(start_idx + 2, len(lines)):
        line = lines[i].strip()
        if not line.startswith("|"):
            break
        cells = split_row(line)
        rows.append((i, cells))
        end_idx = i + 1
    return start_idx, end_idx, rows


def sync():
    solorail_dir = os.path.join(os.getcwd(), ".solorail")
    if not os.path.exists(solorail_dir):
        return

    sprint_files = sorted(glob.glob(os.path.join(solorail_dir, "sprints", "sprint-*.md")))
    roadmap_path = os.path.join(solorail_dir, "ROADMAP.md")

    epic_est = {}
    epic_act = {}
    seen_issues = set()
    valid_statuses = {"TODO", "IN_PROGRESS", "BLOCKED", "DONE", "CUT"}

    for sp_path in sprint_files:
        with open(sp_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        _, _, rows = parse_markdown_table(lines, "| ID |")
        total_est_active = 0.0
        total_cut = 0.0
        total_actual = 0.0
        done_count = 0
        active_count = 0
        cut_count = 0

        for _, cells in rows:
            if len(cells) < 6:
                continue

            issue_id = cells[0].strip()
            epic_id = cells[1].strip()
            status = cells[3].strip().upper()
            est = parse_hours(cells[4])
            act = parse_hours(cells[5])

            if issue_id == "-" or not status:
                continue

            if issue_id in seen_issues:
                print(f"WARNING [SoloRail]: Duplicate Issue ID '{issue_id}' found in {os.path.basename(sp_path)}")
            seen_issues.add(issue_id)

            if status not in valid_statuses:
                print(f"WARNING [SoloRail]: Invalid status '{status}' for {issue_id}")

            if status == "DONE" and act == 0.0:
                print(f"WARNING [SoloRail]: Issue {issue_id} is DONE but has 0.0h actual time logged.")

            if status == "CUT":
                total_cut += est
                cut_count += 1
            else:
                total_est_active += est
                active_count += 1
                if status == "DONE":
                    done_count += 1
                epic_est[epic_id] = epic_est.get(epic_id, 0.0) + est

            total_actual += act
            epic_act[epic_id] = epic_act.get(epic_id, 0.0) + act

        summary_marker = "## Time & Velocity Summary"
        sum_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith(summary_marker):
                sum_idx = i
                break

        new_summary = [
            "## Time & Velocity Summary\n",
            f"- **Total Estimated (Active):** {total_est_active:.1f}h\n",
            f"- **Total Cut:** {total_cut:.1f}h\n",
            f"- **Total Actual:** {total_actual:.1f}h\n",
            f"- **Completed / Total Active Issues:** {done_count} / {active_count}\n",
            f"- **Scope Changes (Cut Issues):** {cut_count}\n",
        ]

        if sum_idx is not None:
            lines = lines[:sum_idx] + new_summary
        else:
            lines.extend(["\n"] + new_summary)

        with open(sp_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"SoloRail synced {os.path.basename(sp_path)}: Est={total_est_active:.1f}h, Act={total_actual:.1f}h, Done={done_count}/{active_count}")

    if os.path.exists(roadmap_path):
        with open(roadmap_path, "r", encoding="utf-8") as f:
            r_lines = f.readlines()

        _, _, r_rows = parse_markdown_table(r_lines, "| Epic ID |")
        for line_idx, cells in r_rows:
            if len(cells) < 6:
                continue
            eid = cells[0].strip()
            est_val = epic_est.get(eid, parse_hours(cells[3]))
            act_val = epic_act.get(eid, parse_hours(cells[4]))
            cells[3] = f"{est_val:.1f}h"
            cells[4] = f"{act_val:.1f}h"
            r_lines[line_idx] = "| " + " | ".join(cells) + " |\n"

        with open(roadmap_path, "w", encoding="utf-8") as f:
            f.writelines(r_lines)
        print("SoloRail synced ROADMAP.md")


if __name__ == "__main__":
    sync()
