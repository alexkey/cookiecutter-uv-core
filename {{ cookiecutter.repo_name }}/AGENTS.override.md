# General Agent Instructions

Codex reads this file in place of `AGENTS.md` in the same directory. Read `AGENTS.md`
before starting any task and follow it. Skip this read in Claude Code: it loads
`AGENTS.md` through the symlink `CLAUDE.md`. The project instructions in `AGENTS.md`
take precedence over these general instructions when they conflict.

Edit only `AGENTS.override.md`. `CLAUDE.local.md` is a symlink to it.

## Output Formatting

Use plain ASCII in everything you produce: responses, code, comments, documentation,
commit messages, and pull request descriptions.

- Use `-` for all dashes, never en or em dashes.
- Use straight quotes `'` and `"`, never typographic quotes or apostrophes.
- Use `...` for ellipses and `->` or `=>` for arrows.
- Use regular spaces only, never non-breaking or zero-width spaces.
- Never use emojis, text emoticons such as `:)`, check marks, box-drawing characters, or
  other decorative symbols.

Use non-ASCII characters only when the content requires them, such as string literals,
localized text, test data, formal specifications, or verbatim quotations. When editing
files, leave existing non-ASCII text outside the scope of the change as is.

Follow these line width guidelines unless project conventions, style rules, or formatter
settings define otherwise. Treat them as guidelines, not hard limits.

- Prefer an 88-character line width for all text sources and documents.
- Use 79 characters for legacy sources and sources that follow a traditional
  79-character convention.
- Allow up to 120 characters for long comments or other content where wrapping at 88
  characters reduces readability.

## Technical Writing

Apply these rules to all technical text you produce: responses, code comments,
docstrings, documentation, commit messages, pull request descriptions, agent
instructions of any kind (such as `AGENTS.md` and `CLAUDE.md` files, prompts, skill
sources, and plugin or agent manifests), specifications of any kind, and any other
technical source text.

- Use precise, professional, declarative language, and the imperative mood for
  instructions and recommendations.
- Avoid casual, conversational, anecdotal, humorous, or apologetic phrasing, such as
  "feel free to", "let's", "hopefully", and "unfortunately".
- Do not use informal connectors and discourse markers, such as "so" in any role,
  "anyway", "that said", and "which means". State a cause with "because", "therefore",
  or "as a result", or in a separate sentence. State a purpose with "to".
- Omit minimizers that make a task sound easy or small, such as "just", "simply",
  "merely", and "easily".
- Omit words that presume the reader agrees or knows, such as "obviously", "clearly",
  "of course", and "needless to say".
- Omit intensifiers and meta-commentary, such as "very", "really", "actually", and
  "note that".
- Replace wordy constructions with short forms, such as "to" for "in order to" and
  "because" for "due to the fact that". Drop padding such as "in terms of" and
  "the fact that".
- Omit time-relative words that make text go stale, such as "today", "currently",
  "recently", and "for now".
- Avoid unverifiable claims such as "this never fires".
- Avoid vague hedging, such as "basically", "kind of", "seems", and "arguably". When
  something is unknown or unverified, state that explicitly and specifically.
- Keep a word from these categories where it carries precise technical meaning, such
  as "only when", "if ... then", or "the file already exists".
- Limit each sentence to one idea. Split a sentence that combines a condition, an
  exception, and an action.
- In an instruction, put the action first and its condition or exception after it:
  write "Read the file before any task unless it is loaded", not "If the file is not
  loaded, read it before any task".
- Avoid double negatives and "neither ... nor" conditions.
- Do not interrupt a sentence with an appositive or a parenthetical aside; give the
  explanation its own sentence.

## Library and API Documentation

Use Context7 to retrieve current documentation whenever a task involves an external
library, framework, SDK, API, CLI tool, or cloud service: writing or changing code that
uses it, installation, setup, configuration, migration, and reference questions. Do this
without being asked, including for well-known libraries and when confident, because
recalled API knowledge can predate the current release.

- Query the version the project uses when the manifest or lockfile identifies it.
- Treat retrieved documentation as more authoritative than recalled knowledge.
- Skip the lookup for code that depends on no external API and for documentation
  already retrieved in the current task.
- If Context7 is unavailable or does not cover the library, use the official
  documentation or the installed package source, and name the source used.

## Python with uv

Invoke the Python interpreter and Python tools only through `uv`, inside and outside
projects, unless the project uses a different Python toolchain.

- Run the interpreter, scripts, and tools with `uv run`, such as `uv run python ...`,
  `uv run script.py`, or `uv run pytest`. Never invoke `python`, `python3`, `pip`, or
  Python tools directly.
- In a project, manage dependencies with `uv add` and `uv remove` (`--dev` for
  development dependencies), not `pip install` or `uv pip install`.
- Outside a project, declare script dependencies inline with
  `uv add --script <script> <package>`, or supply them for a single command with
  `uv run --with <package> ...`.
- Run a tool that the current project does not declare, or any tool outside a project,
  with `uvx <tool>`, only after the user confirms.
- Do not suggest activating a virtual environment or running Python without `uv`
  unless the user asks for it.

## Code Comments and Documentation

Use comments and docstrings to explain what the code cannot express: intent, rationale,
invariants, assumptions, constraints, and non-obvious behavior. Assume the reader knows
the language; explain why the code exists and why the approach is required, not what
each line does. Prefer improving names, structure, and types over adding comments.

For Python, follow the Google Python Style Guide, section 3.8 (Comments and Docstrings):
https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings. For other
languages, follow the equivalent conventions of the language, framework, and project.
Match the style of the surrounding code unless it conflicts with these rules.

Add a comment only when it conveys information the code cannot, such as:

- Non-obvious business rules or domain-specific behavior.
- Algorithmic decisions, tradeoffs, and complexity constraints.
- Complex control flow, concurrency, caching, error handling, or lifecycle behavior.
- Subtle API constraints, framework requirements, or security-sensitive logic.
- Invariants, preconditions, postconditions, and assumptions that must hold.
- Design rationale that the code alone cannot communicate.
- Public interfaces (exported functions, classes, and modules) and configuration that
  require documentation for correct and safe use.

Do not write comments that:

- Restate the code, narrate individual lines, or duplicate type annotations.
- Describe change history, such as code being added, changed, removed, refactored, or
  generated.
- Record TODOs, temporary notes, speculative ideas, or implementation journaling.

Write comments as complete, grammatical sentences. Keep them accurate and timeless:
describe durable intent rather than transient state, mention temporary conditions only
when essential to correct use and state them as explicit assumptions, and update
comments together with the code they describe. An outdated or misleading comment is
worse than none.

Document public APIs by their observable behavior, inputs, outputs, errors, side
effects, and usage constraints. Omit implementation details unless they affect correct
use.

Apply these rules to comments you write or modify; leave unrelated existing comments
unchanged.
