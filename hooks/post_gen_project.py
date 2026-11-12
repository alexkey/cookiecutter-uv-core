"""Links the shared agent assets into the locations that Claude Code reads.

The generated project stores each agent asset once, in the location that OpenAI Codex
reads: the project instructions in `AGENTS.md` and each skill in `.agents/skills`.
Claude Code reads `CLAUDE.md` and `.claude/skills`, where each asset appears as a
relative symlink to its canonical copy.

Cookiecutter does not reproduce symlinks from a template; this hook creates the links
after generation instead of storing them in the template.
"""

from __future__ import annotations

import sys
from pathlib import Path

SHARED_INSTRUCTIONS = Path("AGENTS.md")
CLAUDE_INSTRUCTIONS = Path("CLAUDE.md")

SHARED_SKILLS_DIR = Path(".agents", "skills")
CLAUDE_SKILLS_DIR = Path(".claude", "skills")


def _link(link: Path, target: Path, *, target_is_directory: bool) -> None:
    """Creates the symlink `link` pointing at `target`.

    Replaces a symlink left by an earlier generation into the same output directory,
    which Cookiecutter permits only with `--overwrite-if-exists`.

    Leaves any other file or directory at the link location in place and reports it on
    standard error.

    Args:
        link: Location of the symlink.
        target: Link target, relative to the directory that contains `link`. A relative
            target keeps the link valid after the project is moved or cloned.
        target_is_directory: Whether `target` is a directory.
    """
    if link.is_symlink():
        link.unlink()
    elif link.exists():
        print(f"Skipping {link}: a non-symlink entry already exists", file=sys.stderr)
        return

    link.symlink_to(target, target_is_directory=target_is_directory)


def link_instructions() -> None:
    """Creates the `CLAUDE.md` symlink to the shared project instructions.

    Claude Code reads `AGENTS.md` directly only when no `CLAUDE.md` or `CLAUDE.local.md`
    exists in the project directory or above it. The symlink makes the instructions
    load regardless of such files.
    """
    if not SHARED_INSTRUCTIONS.is_file():
        return

    _link(CLAUDE_INSTRUCTIONS, SHARED_INSTRUCTIONS, target_is_directory=False)


def link_skills() -> None:
    """Creates `.claude/skills/<name>` symlinks for every shared skill."""
    if not SHARED_SKILLS_DIR.is_dir():
        return

    CLAUDE_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    for skill_dir in sorted(SHARED_SKILLS_DIR.iterdir()):
        if not (skill_dir / "SKILL.md").is_file():
            continue

        _link(
            CLAUDE_SKILLS_DIR / skill_dir.name,
            Path("..", "..", *skill_dir.parts),
            target_is_directory=True,
        )


if __name__ == "__main__":
    link_instructions()
    link_skills()
