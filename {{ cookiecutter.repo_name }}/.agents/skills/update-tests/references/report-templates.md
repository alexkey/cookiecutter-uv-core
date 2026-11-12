# Report Templates

Use the template for the mode to structure the final report described in step 7
of the workflow. Each template lists the report's sections in order, with what
each section holds.

## `create` mode

```markdown
## Request
Mode, path, target behavior, and assumptions.

## Project profile
The profile from step 1, each line with its evidence.

## Existing coverage
What was tested before this change.

## Tests added
Per file: each test and the behavior it verifies.

## Verification
Commands and results: baseline and final run with their total runtimes,
repetition and random-order runs, linters, and failure checks. Services
started for verification, and how they were stopped.

## Coverage summary
Behaviors now covered, and known gaps with reasons.

## Proposed changes outside path
Each with the exact change and its reason. None is applied without approval.

## Follow-ups
Defects found, deferred changes, and issues outside the path.
```

## `update` mode

```markdown
## Request
Mode, path, focus, and assumptions.

## Project profile
The profile from step 1, each line with its evidence.

## Findings
Grouped by category; each marked confirmed or inferred, with evidence.

## Changes
Tests removed, merged, rewritten, and added, plus fixture and file changes,
each with its reason.

## Verification
Commands and results: baseline and final run with their total runtimes,
repetition and random-order runs, linters, and failure checks. Services
started for verification, and how they were stopped.

## Improvements
Test count, runtime, coverage, injected defects caught, and stability before
and after, measured where possible.

## Proposed changes outside path
Each with the exact change and its reason. None is applied without approval.

## Follow-ups
Defects found, deferred changes, untested code with the `create` invocation
for each, and issues outside the path.
```
