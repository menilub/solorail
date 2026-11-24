#!/usr/bin/env python3
"""Parse the allowlisted-files section of a SoloRail spec receipt (E03-ISS-09).

The gate used to substring-match the whole spec file:

    if rel_path not in spec_content and basename not in spec_content:

so ANY filename mentioned anywhere in a spec became writable. The E03-ISS-07
spec argued against a markdown exemption with the words "would unlock
`README.md`" -- and thereby authorised README.md. The no-go list inverted
outright: naming a file as forbidden granted write access to it. Basename
matching widened it further, authorising any path ending in a mentioned name.

This module reads paths from the allowlist *section*, and only from *bullet
lines* within it, so prose cannot authorise anything. Matching is exact on the
normalized relative path.
"""

import re

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
# '## Allowlisted Files', '## 3. Allowlisted Files to Create/Modify',
# '### 2.2 Allowlisted Files to Create/Modify' -- all shapes in use.
ALLOWLIST_TITLE_RE = re.compile(
    r"^(?:[\d.]+\s+)?allowlisted\s+files", re.IGNORECASE
)
BULLET_RE = re.compile(r"^\s*[-*]\s+")
BACKTICK_RE = re.compile(r"`([^`]+)`")

ALLOWLIST_HEADING_HINT = "## Allowlisted Files to Create/Modify"


def _looks_like_path(token: str) -> bool:
    """True for a token that plausibly names a file.

    Requires a path separator or a dotted filename, so prose tokens such as
    `SomeClassName` or `--force` are not mistaken for targets.
    """
    token = token.strip()
    if not token or token.startswith("-"):
        return False
    if " " in token:
        return False
    if "/" in token:
        return True
    return bool(re.match(r"^[\w.\-]+\.[A-Za-z0-9]+$", token))


def find_allowlist_section(lines: list[str]) -> list[str] | None:
    """Lines of the allowlist section, or None when the spec declares none.

    The section ends at the next heading of the same or shallower level, so a
    '### Allowlist amendment' subsection nested under a '##' allowlist heading
    is retained -- E03-ISS-02 and E03-ISS-04 both record mid-build amendments
    that way, and their added files must stay authorised.
    """
    start = None
    start_level = 0

    for index, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if not match:
            continue
        level, title = len(match.group(1)), match.group(2).strip()
        if ALLOWLIST_TITLE_RE.match(title):
            start, start_level = index + 1, level
            break

    if start is None:
        return None

    end = len(lines)
    for index in range(start, len(lines)):
        match = HEADING_RE.match(lines[index])
        if match and len(match.group(1)) <= start_level:
            end = index
            break

    return lines[start:end]


def parse_allowlist(spec_text: str) -> list[str] | None:
    """Allowlisted paths, or None when the spec declares no allowlist section.

    An empty list means the section exists but lists nothing -- which blocks
    everything -- and is deliberately distinct from None.
    """
    section = find_allowlist_section(spec_text.splitlines(keepends=True))
    if section is None:
        return None

    paths = []
    for line in section:
        if not BULLET_RE.match(line):
            continue
        tokens = BACKTICK_RE.findall(line)
        if not tokens:
            continue
        # Only the FIRST backticked token: the rest of a bullet is description,
        # e.g. "- `hooks/hooks.json` *(modify)* — add the `Bash` matcher".
        candidate = tokens[0].strip()
        if _looks_like_path(candidate) and candidate not in paths:
            paths.append(candidate)

    return paths


def is_allowlisted(rel_path: str, spec_text: str) -> tuple[bool, str]:
    """(allowed, reason) for a path against a spec's allowlist.

    Exact match on the normalized relative path. Basename matching is
    deliberately unsupported: it authorised any path ending in a mentioned
    filename.
    """
    paths = parse_allowlist(spec_text)

    if paths is None:
        return False, (
            f"the spec declares no allowlist section. Add a "
            f"'{ALLOWLIST_HEADING_HINT}' heading listing each file as a "
            f"bullet, e.g. '- `scripts/thing.py` *(modify)*'."
        )

    normalized = (rel_path or "").replace("\\", "/").strip()
    if normalized in paths:
        return True, "allowlisted"

    if not paths:
        return False, "the spec's allowlist section lists no files."

    return False, f"not in the spec's allowlist ({len(paths)} file(s) listed)."
