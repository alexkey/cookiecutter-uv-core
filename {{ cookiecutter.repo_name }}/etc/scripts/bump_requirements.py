#!/usr/bin/env -S uv run --no-progress --script
# /// script
# requires-python = "~={{ cookiecutter.python_version }}"
# dependencies = ["packaging~=26.3", "tomlkit~=0.15.2"]
# ///

"""Raise the `~=` and `>=` bounds of outdated requirements in a project file.

Reads `NAME VERSION` lines from standard input, where VERSION is the latest release of
the direct dependency NAME, and rewrites the matching PEP 508 requirements of
`project.dependencies`, `project.optional-dependencies`, and `dependency-groups` in
place.

Only the version of each `~=` and `>=` clause changes; spelling, extras, other clauses,
markers, quoting, and comments are preserved.

After versions are raised, a requirement must still accept the latest release.
Otherwise, the requirement is left unchanged and a warning is logged. For example,
with 15.0.0 as the latest release, `rich>=13,<15` is kept as is, because
`rich>=15.0.0,<15` would reject it.
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import tomlkit
from packaging.requirements import InvalidRequirement, Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version
from tomlkit.items import Array, String, StringType

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

    from packaging.utils import NormalizedName
    from tomlkit.toml_document import TOMLDocument

# Locates the version of each `~=` and `>=` clause in the original text, which
# `packaging` parses but cannot reproduce with the author's formatting intact. A
# version ends at whitespace, `,`, `;`, or the `)` of a parenthesized specifier.
RAISABLE_CLAUSE = re.compile(r"(?P<operator>~=|>=)(?P<space>\s*)(?P<version>[^\s,;)]+)")
LITERAL_STRINGS = (StringType.SLL, StringType.MLL)
MULTILINE_STRINGS = (StringType.MLB, StringType.MLL)
# Disabling newline translation preserves the original line endings.
TEXT_OPTIONS = {"encoding": "utf-8", "newline": ""}

logger = logging.getLogger(Path(__file__).name)


def read_latest_versions(lines: Iterable[str]) -> dict[NormalizedName, Version]:
    """Parses `NAME VERSION` lines into latest versions keyed by normalized name.

    Raises:
        ValueError: If a line is not a name followed by a PEP 440 version.
    """
    latest: dict[NormalizedName, Version] = {}

    for line in lines:
        fields = line.split()

        if not fields:
            continue

        if len(fields) != 2:
            raise ValueError(f"expected `NAME VERSION`, got {line.strip()!r}")

        latest[canonicalize_name(fields[0])] = Version(fields[1])
    return latest


def raise_bound(operator: str, current: Version, latest: Version) -> Version | None:
    """Returns the raised bound of a clause, or None if it would not increase.

    A `>=` bound becomes the latest release without its local version label, which
    PEP 440 permits only with `==` and `!=`.

    A `~=` bound keeps its number of release segments: `~=0.4` becomes `~=0.6` rather
    than `~=0.6.2`, which would narrow the compatible range.

    A `~=` bound also takes the prerelease, post-release, or dev suffix of the latest
    release if its segments represent that whole release: `~=1.2.0.post1` becomes
    `~=1.2.0.post2`.
    """
    if operator == "~=":
        size = len(current.release)
        release = ".".join(map(str, (*latest.release, *(0,) * size)[:size]))
        epoch = f"{latest.epoch}!" if latest.epoch else ""
        candidate = Version(f"{epoch}{release}")

        # A suffix belongs to the full release and applies only if the kept segments
        # still equal that release. With `~=1.2`, 1.2.0.post1 gives `~=1.2.post1`, while
        # 1.2.5.post1 leaves the bound unchanged.
        if candidate == Version(latest.base_version):
            suffix = latest.public.removeprefix(latest.base_version)
            candidate = Version(f"{candidate}{suffix}")
    else:
        candidate = Version(latest.public)
    return candidate if candidate > current else None


def bump_requirement(text: str, latest: Mapping[NormalizedName, Version]) -> str | None:
    """Returns `text` with its `~=` and `>=` bounds raised, or None if unchanged.

    Logs a warning for an invalid requirement and for one whose raised bounds would
    exclude the latest release.
    """
    try:
        requirement = Requirement(text)
    except InvalidRequirement as exc:
        logger.warning("Skipped invalid requirement `%s`: %r", text, exc)
        return None

    version = latest.get(canonicalize_name(requirement.name))
    if version is None or requirement.url:
        return None

    def substitute(match: re.Match[str]) -> str:
        bound = raise_bound(match["operator"], Version(match["version"]), version)
        if bound is None:
            return match[0]
        return f"{match['operator']}{match['space']}{bound}"

    # Version specifiers never contain `;`, which therefore separates the name, extras,
    # and clauses of a name-based requirement from its marker.
    clauses, separator, marker = text.partition(";")
    bumped = RAISABLE_CLAUSE.sub(substitute, clauses) + separator + marker
    if bumped == text:
        return None

    if not Requirement(bumped).specifier.contains(version, prereleases=True):
        logger.warning(
            "Skipped `%s`: the raised bounds would exclude %s", text, version
        )
        return None

    return bumped


def iter_requirement_arrays(document: TOMLDocument) -> Iterator[Array]:
    """Yields the TOML arrays that hold the project's requirements."""
    project = document.get("project", {})

    candidates = [
        project.get("dependencies"),
        *project.get("optional-dependencies", {}).values(),
        *document.get("dependency-groups", {}).values(),
    ]
    yield from (array for array in candidates if isinstance(array, Array))


def bump_document(
    document: TOMLDocument, latest: Mapping[NormalizedName, Version]
) -> bool:
    """Bumps the outdated requirements of `document` in place and logs each change.

    Returns:
        True if any requirement changed.
    """
    changed = False

    for array in iter_requirement_arrays(document):
        for index, item in enumerate(array):
            # Dependency groups also hold `{ include-group = ... }` tables.
            if not isinstance(item, String):
                continue

            bumped = bump_requirement(str(item), latest)
            if bumped is None:
                continue

            array[index] = tomlkit.string(
                bumped,
                literal=item.type in LITERAL_STRINGS,
                multiline=item.type in MULTILINE_STRINGS,
            )

            logger.info("Raised `%s` to `%s`", item, bumped)
            changed = True

    return changed


def main() -> int:
    """Bumps the project file named on the command line and returns the exit status."""
    if len(sys.argv) != 2:
        logger.error("Usage: %s PROJECT_FILE < NAME_VERSION_LINES", Path(__file__).name)
        return 2

    path = Path(sys.argv[1])
    try:
        latest = read_latest_versions(sys.stdin)
    except ValueError as exc:
        logger.error("Invalid input: %r", exc)
        return 1

    if not latest:
        return 0

    document = tomlkit.parse(path.read_text(**TEXT_OPTIONS))

    if bump_document(document, latest):
        path.write_text(tomlkit.dumps(document), **TEXT_OPTIONS)

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
