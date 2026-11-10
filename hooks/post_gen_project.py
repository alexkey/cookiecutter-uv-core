"""Links the shared agent skills into the Claude Code skills directory.

The generated project stores each agent skill once, in `.agents/skills`, which OpenAI
Codex reads. Claude Code reads only `.claude/skills`, where each shared skill appears as
a relative symlink.

Cookiecutter does not reproduce directory symlinks from a template; This hook creates
the links after generation instead of storing them in the template.
"""

from __future__ import annotations

import sys
from pathlib import Path

SHARED_SKILLS_DIR = Path(".agents", "skills")
CLAUDE_SKILLS_DIR = Path(".claude", "skills")


def link_skills() -> None:
    """Creates `.claude/skills/<name>` symlinks for every shared skill.

    Replaces symlinks left by an earlier generation into the same output directory,
    which Cookiecutter permits only with `--overwrite-if-exists`.

    Leaves any other file or directory at a link location in place and reports it on
    standard error.
    """
    if not SHARED_SKILLS_DIR.is_dir():
        return

    CLAUDE_SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    for skill_dir in sorted(SHARED_SKILLS_DIR.iterdir()):
        if not (skill_dir / "SKILL.md").is_file():
            continue

        link = CLAUDE_SKILLS_DIR / skill_dir.name
        if link.is_symlink():
            link.unlink()
        elif link.exists():
            print(
                f"Skipping {link}: a non-symlink entry already exists.", file=sys.stderr
            )
            continue

        # A relative target keeps the link valid after the project is moved or cloned.
        target = Path("..", "..", *skill_dir.parts)
        link.symlink_to(target, target_is_directory=True)


if __name__ == "__main__":
    link_skills()
