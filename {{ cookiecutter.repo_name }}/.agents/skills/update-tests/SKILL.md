---
name: update-tests
description: >-
  Create new tests or update existing ones in the project, at any test level,
  without assuming a language, framework, or layout. Takes a mode and a required
  path that names where the tests live. Mode `create` writes tests at that path
  for the code or behavior named in the instructions. Mode `update` audits and
  refactors the tests found there to close coverage gaps, remove redundancy,
  strengthen weak assertions, and eliminate flakiness and nondeterminism. Tooling,
  conventions, and test infrastructure are learned from the project itself. Use
  whenever the user asks to write, add, generate, extend, review, clean up,
  refactor, deduplicate, speed up, stabilize, or de-flake tests, raise coverage,
  fix order-dependent or intermittently failing tests, or bring tests up to
  current best practices, even when the skill is not named. Not for debugging a
  production defect behind a single failing test.
argument-hint: "<create|update> <path> [instructions]"
---

# Update Tests

Create and maintain automated tests that people can trust: each test fails when
the behavior it guards breaks, passes when it does not, runs quickly, and earns
its place. The skill has two modes, `create` and `update`, and holds both to
the same quality bar.

The skill carries no knowledge of particular languages, frameworks, or project
layouts. It works from two inputs: the `path` it is given, which is the only
place where it locates and changes tests, and a profile of the surrounding
project, which it builds from evidence before planning anything.

## Agent compatibility

This skill uses the open Agent Skills format and runs unchanged in Claude Code
and OpenAI Codex. The canonical copy lives in `.agents/skills/update-tests/`,
which Codex reads; `.claude/skills/update-tests` is a symlink to it, which
Claude Code reads. Edit only the canonical copy.

Every step relies only on capabilities both agents share: running shell
commands and searching, reading, and editing files. Paths such as
`references/test-smells.md` are relative to the directory containing this file.
When the host offers extras such as structured questions, task lists, or a
documentation tool, use them, but do not depend on them.

## Arguments

```text
<mode> <path> [instructions]
```

- `mode` (required): `create` or `update`.
  - `create` writes new tests at `path` for the code or behavior that the
    instructions name.
  - `update` analyzes the tests at `path` and improves their coverage,
    redundancy, determinism, reliability, and maintainability. It adds tests
    where it finds gaps.
- `path` (required): one directory or one test file. It is where the tests
  live, and the only place where the skill locates, reviews, creates, and
  changes tests.
  - In `update` mode it must exist and hold tests.
  - In `create` mode it may name a directory or file that does not exist yet,
    provided its parent directory exists.
- `instructions` (optional): free text. In `create` mode it names the code or
  behavior to test. In `update` mode it narrows or directs the work, for
  example toward a specific problem.

Where the arguments come from:

- Claude Code: the text after `/update-tests`, appended to this file's content
  as an `ARGUMENTS:` line.
- Codex: the text accompanying `$update-tests` in the user's message.
- Implicit activation, when the agent selected the skill from the request: the
  request itself.

Parse them in this order:

1. **Mode.** If the first token is `create` or `update` in any letter case, it
   is the mode. Otherwise infer it: new tests for code or behavior that lacks
   them mean `create`; improving, auditing, or fixing existing tests means
   `update`; a request for both means `update`. If the request still supports
   both readings, ask; when no one can answer, choose the closer reading.
2. **Path.** The next token, resolved relative to the current working
   directory. A path that contains spaces is quoted.
3. **Instructions.** Everything after the path.

When the path is missing or doubtful:

- **No path.** Do not search the project for tests. Ask for the path. When no
  one can answer, stop with the usage line above and change nothing. On
  implicit activation, a location that the request names is the path; if the
  request names several, ask which one this run covers.
- **A path that resolves to nothing.** In `update` mode, or in `create` mode
  when the parent directory is also missing, the path is more likely a typo
  than an intention: report it and ask instead of guessing.
- **A path where tests may not belong.** Whether a location is a place for
  tests depends on the project. Step 1 checks the path against the project's
  own conventions.

Open the response by restating the resolved mode, path, and instructions in one
or two lines, so a misreading surfaces before any work is done.

Examples. The paths illustrate different project layouts; none is assumed:

```text
create tests/billing cover invoice rounding and currency conversion
create e2e/signup add a signup journey test, including the email confirmation
update internal/cache focus on the intermittent timeouts in automation
update spec/parser
```

## Ground rules

These rules apply in both modes. Project conventions override this skill's
stylistic defaults, such as layout, naming, fixture style, and assertion style;
they never relax determinism, isolation, or honest verification.

1. **`path` is the boundary.** Locate, review, create, and change tests only
   inside `path`. Read anything else in the project for context, including
   tests elsewhere as examples of convention, but do not review or change
   them, and do not look for more tests to work on. When the work needs a
   change outside `path`, such as a shared fixture higher up, test
   configuration, or a new dependency, propose it in the report with the exact
   change and the reason, and apply it only after the user approves. Until
   then, the tests in `path` must work without it.
2. **Discover, do not assume.** Take every decision about tooling, layout,
   naming, and technique from the project profile built in step 1. Anything
   remembered about a tool is a hypothesis until it is confirmed against the
   version installed in this project.
3. **Leave production code alone,** including production code inside `path`
   in projects that keep tests beside the code. A change for testability, such
   as injecting a clock or exposing a seam, is a proposal that needs approval.
   Never change production code or weaken an assertion only to make a test
   pass.
4. **Treat a failing test as possibly correct.** When a test exposes a real
   defect, do not rewrite it to match the defect. Report the defect with
   evidence, and mark the test as an expected failure only where the project
   has a convention for that, saying so explicitly.
5. **Add no dependencies** without the user's approval. Use what is installed;
   when a missing tool would help substantially, propose it.
6. **Make every test earn its place.** Add tests only for coverage value, and
   remove tests only when they are redundant, obsolete, or invalid, with a
   stated reason for each.
7. **Scale the process to the request.** A single test for a small function
   needs a short profile and one verification run, not a full audit.
8. **Resolve conflicts openly.** When a request conflicts with these rules, for
   example by asking for a test that pins buggy behavior or for a sleep that
   hides a race, explain the risk and propose a compliant alternative, then
   follow the user's decision.
9. **Leave the environment as you found it.** Start a service that the tests
   need, such as a database, only with the user's approval and only through
   the means the project provides for it, such as a task-runner target or a
   service definition in the repository. When asking, name the command and
   what it starts; record what you start. Before the run ends, including a
   run that stops early, stop and remove what you started, together with the
   resources it created, unless the user asks to keep it running. Leave
   anything that was running before untouched.

## Workflow

### 1. Discover the project

Build a project profile before planning. Answer each question below from
evidence in the project, and record where each answer came from.

1. **Project.** What is this project: its languages, its build and dependency
   tooling, its architecture, and its module boundaries? Read the manifests
   and build definitions, the directory layout, the entry points, and the
   documentation.
2. **Guidance.** What do `AGENTS.md`, `CLAUDE.md`, the contributor
   documentation, and any testing documentation prescribe? Rules found there
   take precedence over this skill's defaults.
3. **Running tests.** How does this project run its tests, linters,
   formatters, type checks, and coverage? Look for the project's own entry
   points, such as task-runner targets and package or build scripts, and for
   what its automation runs. Prefer these entry points to invoking tools
   directly: they carry the flags, environment, and paths the project depends
   on. Note which services or environment the tests in `path` need.
4. **Collection.** How does the runner decide what counts as a test: by
   configuration, naming, location, or registration? Confirm the answer by
   having the runner list what it collects in `path`, and compare that list
   with the tests defined there.
5. **Infrastructure.** Which shared fixtures, helpers, data builders, test
   doubles, and tags exist, and which of them apply to `path`? How are slow or
   service-dependent tests gated?
6. **Conventions.** Which layout, naming, structure, assertion style, and use
   of test doubles do the tests follow? Learn this from the tests in `path`
   first, then from their nearest neighbors, then from the rest of the
   project.
7. **Capabilities.** What can the installed tools do: list tests, select a
   subset, repeat tests, randomize order reproducibly, run in parallel,
   measure coverage, inject defects for mutation testing, report durations,
   detect leaks or races? Establish each capability from the tools
   themselves: their help output, their configuration, the extensions the
   project has installed, or a documentation tool when the host offers one.
8. **Code under test.** In `update` mode, which production code do the tests
   in `path` exercise, and which code do the instructions name? Which code
   does the project's layout assign to `path` that no test there exercises?
   In `create` mode, which code or behavior do the instructions name, and
   where does it live?

Every answer cites a file or the output of a command. When an answer cannot be
established, record it as unknown together with a fallback; do not fill the gap
from memory. Typical fallbacks: repeat tests by rerunning the command in a
loop; without order randomization, run each test alone and run the files or
cases in reverse; without a coverage tool, reason from the code paths and from
deliberately broken code; without mutation tooling, introduce defects by hand;
without a duration report, time the command.

Write the profile as a short block, each line ending with its evidence:

```markdown
## Project profile
- Stack: <languages, build and dependency tooling, architecture> (<evidence>)
- Guidance: <rules that apply to tests> (<evidence>)
- Test entry points: <commands for tests and other checks> (<evidence>)
- Collection: <how tests are recognized; what is collected in the path> (<evidence>)
- Infrastructure: <shared fixtures, helpers, doubles, tags, gating> (<evidence>)
- Conventions: <layout, naming, structure, assertion style> (<evidence>)
- Capabilities: <what the tools can and cannot do> (<evidence>)
- Code under test: <modules or behaviors> (<evidence>)
- Unknown: <open question> -> <fallback>
```

The depth of the profile follows the request: a single test for a small
function needs a few lines. Present the profile ahead of the plan.

Then check `path` against the profile:

- In `update` mode, if `path` holds no tests, meaning that the runner collects
  nothing there and no test definitions exist, report what was found, stop, and
  suggest `create` mode. Test definitions that the runner does not collect are
  a finding to fix, not a reason to stop.
- In `create` mode, if the project's conventions place tests somewhere other
  than `path`, for example when `path` holds only production code while the
  tests live in a separate tree, say so, name the location the conventions
  point to, and ask before creating anything. When no one can answer, stop and
  change nothing.
- If the profile cannot establish how tests are run, ask. When no one can
  answer, stop before editing; do not guess a runner.
- If the project has no test tooling yet, use what the installed toolchain
  already provides. If that would need a new dependency, propose it and stop.

### 2. Record a baseline

Before editing, run the tests in `path` once, and the project's linters,
formatters, and type checks, through the entry points from the profile. Record
failures, skips, findings, and duration, so the final report separates
pre-existing problems from your changes. When the tests need a service that is
not running, ask to start it as ground rule 9 describes. If the tests still
cannot run, for example because the project provides no means to start a
required service, the start is declined, no one can answer, or the environment
is broken, record what is missing, continue with static analysis, and treat
verification as partial. For a service left unstarted, name the command that
would start it, so the report can propose it.

### 3a. Analyze for `create`

1. **Pin down the target.** Determine the behavior to test from the
   instructions and from whatever they point to: requirements, issue or
   change-request text, specifications, documentation, and the code itself.
   When the instructions name behavior but not code, search the project for
   it. If several candidates remain, ask; when no one can answer, choose the
   most likely one and state the assumption. Without instructions: when `path`
   already holds tests, extend the coverage of the code they exercise; when
   `path` is empty or new, ask what to test, and when no one can answer, stop
   with the usage line.
2. **Read the code under test.** Map its public contract, input domains and
   their partitions, boundaries, error paths, state transitions, side effects,
   external dependencies, concurrency and timing, and configuration.
3. **Build a behavior inventory.** List the behaviors worth verifying,
   prioritized by risk: core rules, error handling, boundaries, and recently
   changed or historically buggy areas first. Assign each behavior a test
   level. `path` usually fixes the level: tests created there should be of the
   kind that lives there, according to the profile.
   `references/test-levels.md` describes the levels in stack-neutral terms. A
   behavior that needs a level `path` does not hold goes into the follow-ups,
   not into another location.
4. **Check existing coverage.** Find the tests in `path` that already verify
   these behaviors, and the fixtures and helpers available for reuse. Tests
   elsewhere in the project that already cover a behavior are a reason not to
   duplicate it: mention them, and leave them unchanged.

### 3b. Analyze for `update`

1. **Map tests to code.** Pair each test file in `path` with the code it
   exercises, and read both. Gaps in that code, and in code the instructions
   name, are in scope. Code that the layout assigns to `path` but no test
   there exercises is in scope only when the instructions name it or ask for
   broader coverage; otherwise list it in the follow-ups with the `create`
   invocation that would cover it.
2. **Diagnose.** Review each test against the catalog in
   `references/test-smells.md`: flakiness and nondeterminism, redundancy,
   coverage gaps, weak assertions, isolation and structure, test doubles,
   fixtures and setup, speed, and obsolete or uncollected tests.
3. **Gather evidence** with the capabilities recorded in the profile, or their
   fallbacks.
   - Compare what the runner collects in `path` with the tests defined there,
     to catch tests that never run.
   - Run in randomized order and repeat suspect tests, to confirm order
     dependence and flakiness.
   - Measure coverage of the code under test, to locate untested branches; then
     break covered code as in step 5, to find behavior no assertion depends on.
   - Report durations, to find slow tests.

   Mark each finding as confirmed by evidence or inferred from reading.
4. **Prioritize.** Rank findings by impact: tests that cannot fail or that give
   false confidence first, then flakiness, coverage gaps, maintainability, and
   speed.

### 4. Plan

Write a concrete plan before editing anything.

- For `create`: the files to create inside `path`, located and named as the
  profile's conventions dictate; each test with the behavior it verifies and
  its level; the fixtures and helpers to reuse or add, with their scope;
  parametrization tables; tags; and how each test relates to existing
  coverage.
- For `update`: the tests to remove, merge, rewrite, and add, each with its
  reason; fixture changes; and file moves or splits within `path`. For every
  test removed or merged, name the test that still covers its behavior, or
  explain why the behavior no longer exists.
- For both: the changes the work needs outside `path`, as proposals.

Share the plan together with the profile. Then:

- Proceed without waiting when every change stays inside `path` and keeps
  every existing behavior covered. Consolidation of this kind is the job
  itself: merging duplicates, renaming tests, moving or splitting files within
  `path`, and deleting a file once its tests are ported.
- Wait for the user's confirmation before dropping coverage of behavior that
  still exists, changing production code, adding a dependency, or applying any
  proposal outside `path`.
- When no one can respond, as in a non-interactive run, carry out everything
  that needs no confirmation and list the rest in the report as proposals.

### 5. Implement

- Apply the quality standards below, expressed through the conventions and
  infrastructure recorded in the profile.
- Work in small steps: change one file, run its tests, then move on, so each
  failure points at a single change.
- Keep the intent of every rewritten test: it verifies the same behavior, more
  precisely or more reliably, unless the plan says otherwise.
- Prove that the important tests can fail. For each key new or rewritten test,
  confirm that it passes on the unmodified code, then temporarily introduce a
  small defect in the code under test, such as an inverted condition or an
  off-by-one boundary. The test must fail with a clear message from an
  assertion about the broken behavior; a failure in setup, collection, or
  unrelated code proves nothing, and neither does a test that failed before
  the defect. A test that cannot fail protects nothing. The defect is never
  part of the change: revert it at once, confirm with the project's version
  control, or against a saved copy, that the code under test is unchanged,
  and rerun the test to see it pass.

### 6. Verify

Use the entry points and capabilities from the profile, in this order:

1. Run the new and changed tests. They must pass.
2. Run everything in `path` and compare the result with the baseline: no new
   failures and no unintended new skips. When the project's entry point also
   runs tests outside `path` at little cost, run it too, because a change
   inside `path` can break tests that share its helpers. Compare the total
   runtime of the same command as well: duration reports miss a small cost
   repeated in many tests, such as an expensive test double or setup step.
   Trace growth beyond run-to-run variation to its cause, and remove the
   cause unless the coverage it buys justifies it.
3. Check the new and changed tests for determinism: run them repeatedly and in
   randomized order, using the capabilities from the profile or their
   fallbacks. Ten repetitions suit fast tests; tests that involve concurrency,
   time, or I/O deserve more.
4. Run the project's linters, formatters, and type checks through its own
   entry points, over the whole scope those entry points cover, not only on
   the changed files. Some checks relate files to each other, such as
   duplicated code across modules or type errors at call sites, and a run
   limited to the changed files misses them. Prefer modes that report without
   rewriting files. Compare the findings with the baseline, and fix every
   finding your changes introduce, including one reported in a file you did
   not touch: resolve it inside `path`, or propose the change outside it.
5. Review the working tree: every changed file lies inside `path`, and no
   stray artifacts remain, such as coverage data, temporary files, or
   unintentionally updated snapshots.
6. If coverage was measured during analysis, measure it again for comparison.
7. Stop and remove the services and background processes you started, as
   ground rule 9 requires, and confirm that none of them remain.

When a check fails, fix the cause and rerun it. When a check cannot run, state
exactly what was not verified and why. Report only results you observed.

### 7. Report

Deliver the report as the last message, once all work has finished, and make
it self-contained: a reader who sees only the report must find every section
in it. Restate content that earlier messages already showed, instead of
referring back to it with phrases such as "as given above".

Follow the template for the mode in `references/report-templates.md`, omitting
sections that do not apply; the project profile always applies. Keep it
factual and specific: name files, tests, commands, and numbers.

## Test quality standards

All new and changed test code meets these standards. They are stack-neutral:
express each one through the mechanisms the profile found in this project.

- **Behavior over implementation.** Exercise the public interface and assert
  observable outcomes: return values, state changes, emitted events, persisted
  data, and errors. Tests coupled to private helpers or internal call order
  break on every refactor without catching more defects.
- **One behavior per test,** named for the behavior, condition, and expected
  outcome in the project's naming style, so a failure reads as a violated
  specification.
- **Visible Arrange-Act-Assert.** Show the details that matter to the test and
  move incidental setup into fixtures, factories, or builders with sensible
  defaults. Keep loops and conditionals out of test bodies; they hide which
  case failed and tend to mirror the implementation.
- **Precise assertions.** Assert the exact expected value, state, or error
  type, with the relevant part of its message. Avoid assertions that can barely
  fail, such as truthiness checks, "does not raise", or broad error types, and
  assertions that over-specify incidental details, such as timestamps,
  generated identifiers, or full object dumps. Compare floating-point values
  with a tolerance.
- **Explicit data.** Use meaningful values and name the significant ones, so a
  reader sees why an input produces its output. Generate unique data when tests
  share an external store.
- **Isolation and determinism.** No test depends on another test, on execution
  order, or on shared mutable state. Control every source of nondeterminism:
  time through a fake or injected clock; randomness through a seeded generator
  whose seed is reported; concurrency through explicit synchronization instead
  of sleeps; and the environment through temporary locations and scoped,
  restored changes to environment variables and configuration. Release
  resources even when a test fails.
- **Test doubles at boundaries.** Replace what is slow, nondeterministic, or
  outside your control, such as network services, clocks, and third-party
  interfaces. Prefer real collaborators, then fakes, then stubs; use mocks
  only when the interaction itself is the behavior, such as a message being
  sent. Keep doubles faithful to the real interface, using whatever interface
  checking the project's tooling provides, and restore them after each test.
- **Parametrized cases** for one behavior across inputs, each with a readable
  label. Do not fold unrelated behaviors into one table.
- **Right-sized fixtures.** Use the narrowest scope that keeps tests isolated,
  and widen it only for expensive resources that tests do not mutate.
  Guarantee teardown.
- **Lowest sufficient level.** Verify logic with unit tests, wiring and real
  dependencies with integration tests, and critical user journeys with a few
  end-to-end tests. Gate slow or service-dependent tests the way the project
  does.
- **Readable over clever.** Remove copy-paste with parametrization and
  fixtures, but tolerate some repetition: three similar lines beat a premature
  helper, and a test should read top to bottom without jumping between
  abstractions.
- **No masking.** Do not treat flakiness with retries, longer sleeps, or larger
  timeouts; find and remove the cause. Never leave a marker in place that
  restricts a run to selected tests, and give every skip a reason.
- **Regression tests reproduce the failure.** A test for a fixed defect fails
  on the code before the fix.
