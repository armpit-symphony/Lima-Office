#!/usr/bin/env python3
"""Check local Markdown links in the LIMA Office repo."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
IGNORED_SCHEMES = {"http", "https", "mailto", "tel", "app", "plugin"}

INLINE_LINK_RE = re.compile(r"!?\[[^\]\n]+\]\(([^)\n]+)\)")
REFERENCE_LINK_RE = re.compile(r"^\s*\[[^\]]+\]:\s+(\S+)", re.MULTILINE)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def markdown_files() -> list[Path]:
    return sorted(path for path in ROOT.rglob("*.md") if ".git" not in path.parts)


def normalize_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if " " in target and not raw_target.strip().startswith("<"):
        target = target.split(" ", 1)[0]
    return target.strip()


def is_external_or_ignored(target: str) -> bool:
    if not target or target.startswith("#"):
        return True
    parsed = urlparse(target)
    return parsed.scheme.lower() in IGNORED_SCHEMES


def link_path(source: Path, target: str) -> Path:
    path_part = target.split("#", 1)[0]
    path_part = path_part.split("?", 1)[0]
    path_part = unquote(path_part)
    if not path_part:
        return source
    candidate = Path(path_part)
    if candidate.is_absolute():
        return ROOT / path_part.lstrip("/\\")
    return source.parent / candidate


def extract_links(text: str) -> list[tuple[int, str]]:
    links: list[tuple[int, str]] = []
    for regex in (INLINE_LINK_RE, REFERENCE_LINK_RE):
        for match in regex.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            links.append((line_no, normalize_target(match.group(1))))
    return links


def check_links() -> int:
    failures: list[str] = []
    files = markdown_files()
    checked_links = 0
    ignored_links = 0

    for source in files:
        text = source.read_text(encoding="utf-8")
        for line_no, target in extract_links(text):
            if is_external_or_ignored(target):
                ignored_links += 1
                continue
            checked_links += 1
            resolved = link_path(source, target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                failures.append(f"{rel(source)}:{line_no}: local link escapes repo: {target}")
                continue
            if not resolved.exists():
                failures.append(f"{rel(source)}:{line_no}: broken local link: {target}")

    print("LIMA Office markdown link check")
    print(f"- markdown files scanned: {len(files)}")
    print(f"- local links checked: {checked_links}")
    print(f"- external/anchor links ignored: {ignored_links}")
    print(f"- failures: {len(failures)}")
    for failure in failures:
        print(f"FAIL: {failure}")

    if failures:
        print("Result: FAIL")
        return 1

    print("Result: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(check_links())
