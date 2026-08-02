"""Loader and site resolver for the LIMA Office dependency pin lock.

Every live dependency pin in this repository is declared once in
``stack.lock.json`` and duplicated into one or more sites. This module is the
single implementation of "where does a pin appear and what does it say", so
the checker and the bumper can never disagree about either question.

Commit hashes in docs, audits, proof packets, and test fixtures are historical
evidence rather than live pins. Nothing here reads or rewrites them: a site is
only ever touched when the lock names it explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any


COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
COMMIT_SHAPED = re.compile(r"\b[0-9a-f]{40}\b")
POLICIES = frozenset({"tracking", "frozen"})
LOCK_NAME = "stack.lock.json"


class LockError(Exception):
    """The lock file is structurally unusable."""


@dataclass(frozen=True)
class Site:
    """One place a dependency's commit is written down."""

    path: str
    pattern: str
    occurrences: int

    @property
    def regex(self) -> re.Pattern[str]:
        return re.compile(self.pattern)


@dataclass(frozen=True)
class Dependency:
    """One pinned dependency and every site that repeats its commit."""

    name: str
    repo: str
    commit: str
    policy: str
    reason: str
    package_name: str | None
    package_version: str | None
    sites: tuple[Site, ...]

    @property
    def clone_url(self) -> str:
        return f"https://github.com/{self.repo}.git"


@dataclass(frozen=True)
class Lock:
    """The parsed contents of ``stack.lock.json``."""

    version: str
    dependencies: tuple[Dependency, ...]

    def dependency(self, name: str) -> Dependency:
        for dependency in self.dependencies:
            if dependency.name == name:
                return dependency
        known = ", ".join(sorted(item.name for item in self.dependencies))
        raise LockError(f"unknown dependency {name!r}; the lock declares: {known}")


def repository_root(start: Path | None = None) -> Path:
    """Find the repository root by walking up to the lock file."""

    current = (start or Path(__file__).resolve().parent).resolve()
    for candidate in (current, *current.parents):
        if (candidate / LOCK_NAME).is_file():
            return candidate
    raise LockError(f"{LOCK_NAME} was not found in any parent directory")


def _require_str(container: dict[str, Any], key: str, where: str) -> str:
    value = container.get(key)
    if not isinstance(value, str):
        raise LockError(f"{where}: {key!r} must be a string")
    return value


def _parse_site(raw: Any, where: str) -> Site:
    if not isinstance(raw, dict):
        raise LockError(f"{where}: every site must be an object")
    path = _require_str(raw, "path", where)
    pattern = _require_str(raw, "pattern", where)
    occurrences = raw.get("occurrences")
    if not isinstance(occurrences, int) or isinstance(occurrences, bool):
        raise LockError(f"{where}: {path} declares a non-integer occurrence count")
    if occurrences < 1:
        raise LockError(f"{where}: {path} must declare at least one occurrence")
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        raise LockError(f"{where}: {path} has an invalid pattern: {exc}") from exc
    if "commit" not in compiled.groupindex:
        raise LockError(
            f"{where}: {path} pattern must capture a group named 'commit' so the "
            "bumper knows exactly which characters to replace"
        )
    return Site(path=path, pattern=pattern, occurrences=occurrences)


def _parse_dependency(name: str, raw: Any) -> Dependency:
    where = f"dependency {name!r}"
    if not isinstance(raw, dict):
        raise LockError(f"{where}: must be an object")
    commit = _require_str(raw, "commit", where)
    if not COMMIT_PATTERN.match(commit):
        raise LockError(
            f"{where}: commit must be a full lowercase 40-character hash, got "
            f"{commit!r}"
        )
    policy = _require_str(raw, "policy", where)
    if policy not in POLICIES:
        raise LockError(
            f"{where}: policy must be one of {sorted(POLICIES)}, got {policy!r}"
        )
    reason = raw.get("reason", "")
    if not isinstance(reason, str):
        raise LockError(f"{where}: reason must be a string")
    if policy == "frozen" and not reason.strip():
        raise LockError(
            f"{where}: a frozen pin must record why it is held behind main"
        )
    package = raw.get("package")
    package_name: str | None = None
    package_version: str | None = None
    if package is not None:
        if not isinstance(package, dict):
            raise LockError(f"{where}: package must be an object or null")
        package_name = _require_str(package, "name", where)
        package_version = _require_str(package, "version", where)
    raw_sites = raw.get("sites")
    if not isinstance(raw_sites, list) or not raw_sites:
        raise LockError(f"{where}: must declare at least one site")
    sites = tuple(_parse_site(site, where) for site in raw_sites)
    return Dependency(
        name=name,
        repo=_require_str(raw, "repo", where),
        commit=commit,
        policy=policy,
        reason=reason,
        package_name=package_name,
        package_version=package_version,
        sites=sites,
    )


def load_lock(root: Path | None = None) -> Lock:
    """Parse and structurally validate the lock."""

    base = root or repository_root()
    path = base / LOCK_NAME
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LockError(f"{path} does not exist") from exc
    except json.JSONDecodeError as exc:
        raise LockError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise LockError(f"{path} must contain a JSON object")
    version = _require_str(raw, "lock_version", "lock")
    dependencies = raw.get("dependencies")
    if not isinstance(dependencies, dict) or not dependencies:
        raise LockError("lock: 'dependencies' must be a non-empty object")
    parsed = tuple(
        _parse_dependency(name, value) for name, value in sorted(dependencies.items())
    )
    return Lock(version=version, dependencies=parsed)


def read_site_text(root: Path, site: Site) -> str:
    """Read a site verbatim, leaving its line endings untouched.

    ``requirements-lab.txt`` uses CRLF. Reading through universal newlines and
    writing back would silently rewrite every line ending in the file, so the
    bumper would produce a diff far larger than the pin it was asked to move.
    """

    path = root / site.path
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_site_text(root: Path, site: Site, text: str) -> None:
    """Write a site back verbatim, leaving its line endings untouched."""

    path = root / site.path
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def site_matches(text: str, site: Site) -> list[re.Match[str]]:
    return list(site.regex.finditer(text))


def site_commits(text: str, site: Site) -> list[str]:
    return [match.group("commit") for match in site_matches(text, site)]


def rewrite_site(text: str, site: Site, commit: str) -> str:
    """Replace only the captured commit characters, leaving the rest alone."""

    pieces: list[str] = []
    cursor = 0
    for match in site_matches(text, site):
        start, end = match.span("commit")
        pieces.append(text[cursor:start])
        pieces.append(commit)
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces)


def check_sites(lock: Lock, root: Path) -> list[str]:
    """Return one failure line per site that disagrees with the lock."""

    failures: list[str] = []
    for dependency in lock.dependencies:
        for site in dependency.sites:
            path = root / site.path
            if not path.is_file():
                failures.append(
                    f"{dependency.name}: site {site.path} does not exist"
                )
                continue
            found = site_commits(read_site_text(root, site), site)
            if len(found) != site.occurrences:
                failures.append(
                    f"{dependency.name}: {site.path} matched {len(found)} "
                    f"occurrence(s), the lock declares {site.occurrences}"
                )
                continue
            for commit in found:
                if commit != dependency.commit:
                    failures.append(
                        f"{dependency.name}: {site.path} pins {commit}, the lock "
                        f"pins {dependency.commit}"
                    )
    return failures


def registered_spans(lock: Lock, root: Path) -> dict[str, list[tuple[int, int]]]:
    """Map each site path to the character spans the lock accounts for."""

    spans: dict[str, list[tuple[int, int]]] = {}
    for dependency in lock.dependencies:
        for site in dependency.sites:
            if not (root / site.path).is_file():
                continue
            text = read_site_text(root, site)
            for match in site_matches(text, site):
                spans.setdefault(site.path, []).append(match.span("commit"))
    return spans
