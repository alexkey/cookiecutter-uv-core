# Execution Plans

Read this when writing a plan in stage 1, when saving and maintaining it in
stage 2, and whenever a run starts from an existing plan. The format adapts
OpenAI's ExecPlans methodology: a plan is a living, self-contained document
from which a reader who has only the working tree and the plan can finish
the work.

## Contents

- When a plan is required
- Location and naming
- Principles
- Skeleton
- Living sections
- Status and lifecycle
- Resuming
- Tech-debt tracker

## When a plan is required

Write a full execution plan for complex work: a new project, a port, an
import, a reimplementation, or an integration; a feature that involves a
design decision, more than one milestone, or a change to a public
interface, the data model, or the dependencies; and any work that may span
sessions.

A small change with no design decision gets a lightweight plan instead: the
requirements, the files to change, the validation, the documentation
impact, and the test targets, in a few lines. It passes gate 1 like any
plan but is not saved, unless a plan path was given; then it is saved in the
skeleton below, with short sections. Without a saved plan, the stage 2
report carries what the living sections would hold.

## Location and naming

- The plan path is, in order of precedence: the explicit `plan-path`
  argument, the location that project guidance prescribes, or
  `docs/exec-plans/active/`.
- The default hierarchy:

  ```text
  docs/exec-plans/
    active/                 plans in progress
    completed/              completed and cancelled plans
    tech-debt-tracker.md    deferred work and known shortcuts
  ```

- Create the missing parts of the default hierarchy when a plan is first
  saved there. Never create directories for an explicit plan path; the
  Arguments section of the skill describes that guard.
- Write every date and time in a plan and in the tracker in UTC, read from
  the system clock rather than assumed: dates as `YYYY-MM-DD`, times as
  `HH:MMZ`. A single time zone keeps the file name, the status, Progress,
  the Decision Log, and the tracker consistent with one another.
- Name a new plan `YYYY-MM-DD-<slug>.md`: the creation date followed by a
  short descriptive slug of lowercase words joined by hyphens, such as
  `2026-11-12-report-export.md`. When the name is taken, choose another
  slug; never overwrite an existing plan.
- A file that only keeps an empty directory under version control is a
  placeholder, not a plan.
- Plans are project files that belong under version control with the
  change they describe. Leave them in the working tree with the rest of the
  change; commit only when the user asks.

## Principles

- **Self-contained.** The plan holds everything needed to finish the work.
  It does not rely on the conversation, on earlier plans, or on outside
  documents that it does not summarize, and every revision still stands
  alone.
- **Purpose first.** Begin with what a user can do after the change and how
  to see it working. State acceptance as observable behavior, such as a
  command and its output or a request and its response, not as the
  presence of internal artifacts.
- **Plain language.** Define each term of art where it first appears, or
  avoid it. Name files by their repository-relative paths and code by its
  exact module and function names, and give the working directory of every
  command.
- **Living document.** Revise the plan as the work proceeds, discoveries
  occur, and decisions are made, within the limits that Living sections
  sets.
- **Verifiable milestones.** Divide the work into milestones that each
  leave the project working and can be verified on their own. Describe
  each one by its goal, its work, its result, and the proof.
- **Validation is mandatory.** Every milestone and every requirement names
  the commands to run and the expected result, beyond a successful build.
- **Idempotence and recovery.** Make steps safe to repeat. For a risky
  step, name the backup or the way back.
- **Prototypes and parallel paths.** Label a prototyping milestone as such,
  keep it additive, and state when it is promoted or discarded. Two
  implementations may run side by side during a migration when the plan
  validates both and retires one.
- **Prose first.** Write the sections as prose, and use checkboxes only in
  Progress. Show commands, output, and code as indented blocks, so the plan
  never nests fenced blocks.

## Skeleton

Use these sections, in this order. Depth follows the task: a section that
does not apply holds one line saying so.

```markdown
# <Short, action-oriented title>

Status: draft | approved YYYY-MM-DD | implemented YYYY-MM-DD |
completed YYYY-MM-DD | cancelled YYYY-MM-DD

This is a living execution plan, implemented under the `develop` skill.
Keep Progress, Surprises & Discoveries, Decision Log, and Outcomes &
Retrospective current. The status records which gate the plan passed and
never grants approval; the testing stage needs its own approval.

## Purpose / Big Picture
What a user can do after this change, and how to see it working. The
numbered requirements, the constraints, and what is out of scope.

## Progress
- [x] (YYYY-MM-DD HH:MMZ) A completed step.
- [ ] The next step.

## Surprises & Discoveries
Each observation, with the evidence that shows it.

## Decision Log
Each decision, with its rationale and date: the alternatives rejected in
planning, the approval of the plan, and each deviation with its approval.

## Outcomes & Retrospective
Results against the purpose, remaining gaps, and lessons, at major
milestones and at completion.

## Context and Orientation
The current state, for a reader who knows nothing of the project: the key
files by path, and every term the plan uses.

## Plan of Work
Prose per milestone: each edit, its file and location, and what changes;
the documentation to update; the existing tests expected to change, each
with the approved behavior change that requires it.

## Concrete Steps
Exact commands, their working directory, and the expected output.

## Validation and Acceptance
Per requirement, how to observe it working. The proposed test targets for
the testing stage, in priority order.

## Idempotence and Recovery
How to repeat the steps safely, and how to retry or roll back a risky one.

## Artifacts and Notes
Short transcripts, diffs, or snippets that prove success.

## Interfaces and Dependencies
The interfaces, modules, and signatures that must exist at the end, and
the dependencies they use.
```

## Living sections

Progress, Surprises & Discoveries, Decision Log, and Outcomes &
Retrospective record the work as it happens:

- **Progress:** one checkbox per step, with the UTC time of completion in
  the form `(YYYY-MM-DD HH:MMZ)`. Split a step that is partly done into its
  done and remaining parts. Progress always matches the actual state.
- **Surprises & Discoveries:** unexpected behavior, defects, and
  constraints, each with its evidence.
- **Decision Log:** every decision with its rationale and date, including
  the approval of the plan, each deviation, and each deviation's approval.
- **Outcomes & Retrospective:** results, gaps, and lessons, compared with
  the purpose, at major milestones and at completion.

Whether an update keeps the approval depends on what it changes, not on
the section it is written in:

- An update is bookkeeping only when it preserves the approved scope,
  behavior, and design: checking off or splitting an approved step,
  recording an observation, logging a minor deviation under the deviation
  rule, applying a logged minor deviation to the steps it affects, or
  summarizing outcomes.
- Apply a minor deviation wherever the plan describes the affected work,
  such as a corrected command, path, or example in the Plan of Work,
  Concrete Steps, or Validation and Acceptance. A completed plan is the
  durable record of the work, and a step known to fail breaks the
  self-contained principle. The correction stays bookkeeping while no
  requirement, acceptance criterion, interface, or design decision
  changes.
- Anything else is a substantive change wherever it is written, living
  sections included: a new milestone or step in Progress, a Decision Log
  entry that alters an approved design decision, or a changed requirement
  or acceptance criterion. It needs explicit approval under the deviation
  rule.

## Status and lifecycle

| Status | Meaning | Set |
| --- | --- | --- |
| `draft` | Written, not approved | At gate 1 in a non-interactive run |
| `approved` | Passed gate 1 | On entry to stage 2 |
| `implemented` | Stage 2 done; testing decision pending | At gate 2 |
| `completed` | Tested, or testing declined | When the plan closes |
| `cancelled` | Abandoned at the user's request | When the user cancels |

A plan in `active/` moves to the sibling `completed/` directory when it is
completed or cancelled; a plan at another location stays where it is. The
status records which gate the plan passed; it never grants approval.

## Resuming

Read the whole plan, then establish authorization before acting on it. The
saved status records which gate the plan passed; it never grants approval.

- Approval evidence is the host's plan-approval action or an explicit
  approval statement, visible in the current conversation and tied to the
  plan's current content. Bookkeeping updates, as Living sections defines
  them, and revisions approved under the deviation rule keep the approved
  version. Any other change, in any section, is an unapproved change.
- Return to gate 1 for a `draft`, for an `approved` plan without such
  evidence, and for a plan with an unapproved change. This covers a new
  session, a cleared context, and a summary of the conversation that does
  not show what was approved. Present the current version with its
  Progress, and wait.
- With the evidence, check Progress against the working tree, record any
  mismatch in Surprises & Discoveries, and continue at the first open item.
  The check locates the resume point; it never establishes authorization.
- An `implemented` plan returns to gate 1 when it has an unapproved change,
  and otherwise to gate 2, unless a gate 2 approval of this plan is visible
  in the current conversation.
- A `completed` or `cancelled` plan is not resumed: report its status and
  ask what to do. New work gets a new plan.

## Tech-debt tracker

The tracker lists work that was knowingly deferred. It lives in the plans
directory as `tech-debt-tracker.md`, unless project guidance names another
location, and is created on first use.

- **What belongs there:** shortcuts taken on purpose, follow-ups outside a
  plan's scope, findings noticed but not fixed, and test targets that the
  user declined.
- **What does not:** a defect that blocks the current work, which is fixed
  or reported, and work that has an active plan.
- **Entry format,** under the tracker's Entries heading:

  ```markdown
  ### <Short title>

  - Recorded: YYYY-MM-DD
  - Source: <execution plan or task that recorded the debt>
  - Location: <files or components>
  - Debt: <what is missing or wrong, and its consequence>
  - Remedy: <the change that resolves it>
  ```

- Remove an entry in the change that resolves it, and record the removal in
  that change's plan.
