# Documentation

Read this when naming the affected documentation in the plan during stage 1, and when
updating that documentation in stage 2. Documentation that disagrees with the code
misleads both people and agents. It therefore changes together with the behavior it
describes.

## Contents

- Rules
- User-facing documentation
- Project agent instructions
- Execution plans and the tracker

## Rules

1. **Update documentation in the same change** as the behavior it describes, never as a
   later task.
2. **Discover the documentation set** in stage 1: the user-facing documents, such as the
   readme, guides, reference pages, help texts, and the changelog; the project's agent
   instructions, such as `AGENTS.md`, `CLAUDE.md`, and the files they index; and the
   execution plans. Follow the project's own rules for maintaining each. They override
   the defaults in this file.
3. **Edit the canonical copy.** Change the target of a symlink or the source of a
   generated file, not the file itself.
4. **Describe the current behavior,** not its history. Words such as "now", "new", and
   "previously" date the text. Only documents that record history use them, such as a
   changelog.
5. **Run what you document.** Run every command and example as written, and confirm that
   the output matches what the text says.
6. **Keep each fact in one place,** and link to it instead of copying it.

## User-facing documentation

Document:

- new features and capabilities;
- new commands, flags, and options;
- new interfaces and endpoints;
- new configuration options;
- changed behavior that affects users;
- new dependencies and system requirements;
- breaking changes, with the migration path.

Leave unchanged for:

- internal refactoring with no visible effect;
- defect fixes that restore the documented behavior;
- test additions;
- changes of code style.

## Project agent instructions

Agent instructions hold what an agent cannot infer from the code: rules, rationale,
pitfalls, and where things belong. Point to the code or the configuration for anything
they already state precisely. Respect the size and organization rules that the
instructions set for themselves. Delete an instruction that the change makes obsolete.

Document:

- new architectural patterns that the change establishes;
- new conventions and coding standards;
- new commands for building, checking, or testing;
- new libraries and tools;
- changes to the project structure;
- changes to development workflows;
- non-obvious debugging techniques and pitfalls discovered during the work.

Leave unchanged for:

- code that follows existing patterns;
- simple defect fixes;
- tests that follow existing patterns.

## Execution plans and the tracker

The plan is the record of the work, and `references/exec-plans.md` defines its format.
Update it:

- on entry to stage 2, when it is saved with its approval;
- during stage 2, as each step completes, each discovery occurs, and each decision is
  made, within the bookkeeping limits of the living sections;
- when a significant deviation is approved, by revising the affected sections and
  logging the decision with its approval;
- at each major milestone and at completion, in Outcomes & Retrospective;
- when the plan closes, by setting its status and moving it if it lives in `active/`.

Update the tech-debt tracker when work is knowingly deferred, when a finding outside the
scope is not fixed, and when the user declines proposed test targets. Remove an entry in
the change that resolves it.
