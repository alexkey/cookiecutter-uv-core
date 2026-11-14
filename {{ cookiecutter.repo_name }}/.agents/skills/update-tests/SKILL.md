---
name: update-tests
description: >-
  Create new tests or update existing ones in the project, at any test level, without
  assuming a language, framework, or layout. Takes a mode and a required path that names
  where the tests live. Mode `create` writes tests at that path for the code or behavior
  named in the instructions. Mode `update` audits and refactors the tests found there to
  close coverage gaps, remove redundancy, strengthen weak assertions, and eliminate
  flakiness and nondeterminism. The skill learns the tooling, conventions, and test
  infrastructure from the project. Use whenever the user asks to write, add, generate,
  extend, review, clean up, refactor, deduplicate, speed up, stabilize, or de-flake
  tests, raise coverage, fix order-dependent or intermittently failing tests, or bring
  tests up to best practices, even when the skill is not named. Not for debugging a
  production defect behind a single failing test.
argument-hint: "<create|update> <path> [instructions]"
---

# Update Tests

Create and maintain automated tests that people can trust: each test fails when the
behavior it guards breaks, passes when it does not, runs quickly, and earns its place.
The skill has two modes, `create` and `update`. Both meet the same quality bar.

The skill carries no knowledge of particular languages, frameworks, or project layouts.
It works from two inputs. The first is the given `path`, the only place where it locates
and changes tests. The second is a profile of the surrounding project, built from
evidence before any planning.

## Agent compatibility

This skill uses the open Agent Skills format and runs unchanged in Claude Code and
OpenAI Codex. Codex reads the canonical copy in `.agents/skills/update-tests/`. Claude
Code reads `.claude/skills/update-tests`, a symlink to it. Edit only the canonical copy.

Every step relies only on capabilities both agents share: running shell commands and
searching, reading, and editing files. Paths such as `references/test-smells.md` are
relative to the directory containing this file. Use the extras that a host offers, but
do not depend on them. Such extras include structured questions, task lists, and a
documentation tool.

## Arguments

```text
<mode> <path> [instructions]
```

- `mode` (required): `create` or `update`.
  - `create` writes new tests at `path` for the code or behavior that the instructions
    name.
  - `update` analyzes the tests at `path` and improves their coverage, redundancy,
    determinism, reliability, and maintainability. It adds tests where it finds gaps.
- `path` (required): one directory or one test file. It is where the tests live, and the
  only place where the skill locates, reviews, creates, and changes tests.
  - In `update` mode, it must exist and hold tests.
  - In `create` mode, it may name a directory or file that does not exist yet, provided
    that its parent directory exists.
- `instructions` (optional): free text. In `create` mode, it names the code or behavior
  to test. In `update` mode, it narrows or directs the work, for example toward a
  specific problem. It can also extend the work to code that no test in `path`
  exercises.

Where the arguments come from:

- Claude Code: the text after `/update-tests`, appended to this file's content as an
  `ARGUMENTS:` line.
- Codex: the text accompanying `$update-tests` in the user's message.
- Implicit activation, when the agent selected the skill from the request: the request
  itself.

Parse them in this order:

1. **Mode.** The first token is the mode when it is `create` or `update` in any letter
   case. Otherwise, infer the mode from the request. Use `create` for new tests of code
   or behavior that lacks them. Use `update` for improving, auditing, or fixing existing
   tests, and for a request that asks for both. Ask when the request still supports both
   readings. Choose the closer reading when no one can answer.
2. **Path.** The next token, resolved relative to the current working directory. A path
   that contains spaces is quoted.
3. **Instructions.** Everything after the path.

When the path is missing or doubtful:

- **No path.** Do not search the project for tests. Ask for the path. Stop with the
  usage line above and change nothing when no one can answer. On implicit activation, a
  location that the request names is the path. Ask which one this run covers when the
  request names several.
- **A path that resolves to nothing.** Such a path is more likely a typo than an
  intention in `update` mode, and in `create` mode when its parent directory is also
  missing. Report it and ask instead of guessing.
- **A path where tests may not belong.** Whether a location is a place for tests depends
  on the project. Step 1 checks the path against the project's own conventions.

Open the response with a restatement of the resolved mode, path, and instructions in one
or two lines. A misreading then surfaces before any work is done.

Examples. The paths illustrate different project layouts, and the skill assumes none of
them:

```text
create tests/billing cover invoice rounding and currency conversion
create e2e/signup add a signup journey test, including the email confirmation
update internal/cache focus on the intermittent timeouts in automation
update spec/parser
```

## Ground rules

These rules apply in both modes. Project conventions override this skill's stylistic
defaults, such as layout, naming, fixture style, and assertion style. They never relax
determinism, isolation, or honest verification.

1. **`path` is the boundary.** Locate, review, create, and change tests only inside
   `path`. Read anything else in the project for context, including tests elsewhere as
   examples of convention. Do not review or change those tests, and do not look for more
   tests to work on. Propose a change that the work needs outside `path` in the report,
   with the exact change and the reason. Examples are a shared fixture higher up, test
   configuration, and a new dependency. Apply such a change only after the user approves
   it. Until then, the tests in `path` must work without it.
2. **Discover, do not assume.** Take every decision about tooling, layout, naming, and
   technique from the project profile built in step 1. Anything remembered about a tool
   is a hypothesis until it is confirmed against the version installed in this project.
3. **Leave production code alone,** including production code inside `path` in projects
   that keep tests beside the code. A change for testability is a proposal that needs
   approval, for example injecting a clock or exposing a seam. Never change production
   code or weaken an assertion only to make a test pass.
4. **Treat a failing test as possibly correct.** Do not rewrite a test that exposes a
   real defect to match the defect. Report the defect with evidence. Mark the test as an
   expected failure only where the project has a convention for that, and state the
   marking explicitly in the report.
5. **Add no dependencies** without the user's approval. Use what is installed, and
   propose a missing tool when it would help substantially.
6. **Make every test earn its place.** Add tests only for coverage value, and remove
   tests only when they are redundant, obsolete, or invalid, with a stated reason for
   each.
7. **Scale the process to the request.** A single test for a small function needs a
   short profile and one verification run, not a full audit.
8. **Resolve conflicts openly.** Explain the risk when a request conflicts with these
   rules, propose a compliant alternative, and then follow the user's decision. Examples
   are a request for a test that pins buggy behavior and a request for a sleep that
   hides a race.
9. **Leave the environment as you found it.** Start a service that the tests need only
   with the user's approval and only through the means the project provides for it, such
   as a task-runner target or a service definition in the repository. Name the command
   and what it starts when asking, and record what you start. Stop and remove what you
   started, together with the resources it created, before the run ends or stops early,
   unless the user asks to keep it running. Leave anything that was running before
   untouched.

## Workflow

### 1. Discover the project

Build a project profile before planning. Answer each question below from evidence in the
project, and record where each answer came from.

1. **Project.** What is this project: its languages, its build and dependency tooling,
   its architecture, and its module boundaries? Read the manifests and build
   definitions, the directory layout, the entry points, and the documentation.
2. **Guidance.** What do `AGENTS.md`, `CLAUDE.md`, the contributor documentation, and
   any testing documentation prescribe? Rules found there take precedence over this
   skill's defaults.
3. **Running tests.** How does this project run its tests, linters, formatters, type
   checks, and coverage? Look for the project's own entry points, such as task-runner
   targets and package or build scripts, and for what its automation runs. Prefer these
   entry points to invoking tools directly, because they carry the flags, environment,
   and paths the project depends on. Note which services or environment the tests in
   `path` need.
4. **Collection.** How does the runner decide what counts as a test: by configuration,
   naming, location, or registration? Confirm the answer by having the runner list what
   it collects in `path`, and compare that list with the tests defined there.
5. **Infrastructure.** Which shared fixtures, helpers, data builders, test doubles, and
   tags exist, and which of them apply to `path`? How are slow or service-dependent
   tests gated?
6. **Conventions.** Which layout, naming, structure, assertion style, and use of test
   doubles do the tests follow? Learn this from the tests in `path` first, then from
   their nearest neighbors, then from the rest of the project.
7. **Capabilities.** What can the installed tools do: list tests, select a subset,
   repeat tests, randomize order reproducibly, run in parallel, measure coverage, inject
   defects for mutation testing, report durations, detect leaks or races? Establish each
   capability from the tools themselves: their help output, their configuration, the
   extensions the project has installed, or a documentation tool when the host offers
   one.
8. **Code under test.** In `update` mode, which production code do the tests in `path`
   exercise, and which code do the instructions name? Which code does the project's
   layout assign to `path` that no test there exercises? In `create` mode, which code or
   behavior do the instructions name, and where does it live?

Every answer cites a file or the output of a command. Record an answer that cannot be
established as unknown, together with a fallback. Do not fill the gap from memory.
Typical fallbacks:

- Repeat tests by rerunning the command in a loop.
- Replace order randomization by running each test alone and by running the files or
  cases in reverse.
- Replace a coverage tool by reasoning from the code paths and from deliberately broken
  code.
- Replace mutation tooling by introducing defects by hand.
- Replace a duration report by timing the command.

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

The depth of the profile follows the request: a single test for a small function needs a
few lines. Present the profile ahead of the plan.

Then check `path` against the profile:

- In `update` mode, `path` holds no tests when the runner collects nothing there and no
  test definitions exist. Report what was found in that case, stop, and suggest `create`
  mode. Test definitions that the runner does not collect are a finding to fix, not a
  reason to stop.
- In `create` mode, the project's conventions may place tests somewhere other than
  `path`, for example in a separate tree while `path` holds only production code. Report
  the mismatch, name the location that the conventions point to, and ask before creating
  anything. Stop and change nothing when no one can answer.
- Ask when the profile cannot establish how tests are run. Stop before editing when no
  one can answer, and do not guess a runner.
- Use what the installed toolchain provides when the project has no test tooling.
  Propose a new dependency and stop when the toolchain provides nothing suitable.

### 2. Record a baseline

Run the tests in `path` once before editing, together with the project's linters,
formatters, and type checks, through the entry points from the profile. Record failures,
skips, findings, and duration to let the final report separate pre-existing problems
from your changes. Ask to start a service that the tests need and that is not running,
as ground rule 9 describes. Record what is missing, continue with static analysis, and
treat verification as partial when the tests still cannot run. The causes include a
project that provides no means to start a required service, a declined start, a run in
which no one can answer, and a broken environment. Name the command that would start a
service left unstarted, to let the report propose it.

### 3a. Analyze for `create`

1. **Pin down the target.** Determine the behavior to test from the instructions and
   from whatever they point to: requirements, issue or change-request text,
   specifications, documentation, and the code itself. Search the project for the code
   when the instructions name behavior but not code. Ask when several candidates remain.
   Choose the most likely candidate and state the assumption when no one can answer.
   Extend the coverage of the code that the tests in `path` exercise when the request
   gives no instructions. Ask what to test when `path` is empty or new, and stop with
   the usage line when no one can answer.
2. **Read the code under test.** Map its public contract, input domains and their
   partitions, boundaries, error paths, state transitions, side effects, external
   dependencies, concurrency and timing, and configuration.
3. **Build a behavior inventory.** List the behaviors worth verifying, prioritized by
   risk: core rules, error handling, boundaries, and recently changed or historically
   buggy areas first. Assign each behavior a test level. `path` usually fixes the level:
   tests created there are of the kind that lives there, according to the profile.
   `references/test-levels.md` describes the levels in stack-neutral terms. A behavior
   that needs a level that `path` does not hold goes into the follow-ups, not into
   another location.
4. **Check existing coverage.** Find the tests in `path` that already verify these
   behaviors, and the fixtures and helpers available for reuse. Do not duplicate a
   behavior that tests elsewhere in the project already cover. Mention those tests, and
   leave them unchanged.

### 3b. Analyze for `update`

1. **Map tests to code.** Pair each test file in `path` with the code it exercises, and
   read both. Gaps in that code and in code the instructions name are in scope. Code
   that the layout assigns to `path` but no test there exercises is in scope only when
   the instructions name it or ask for broader coverage. Otherwise, list it in the
   follow-ups with the `create` invocation that would cover it.
2. **Diagnose.** Review each test against the catalog in `references/test-smells.md`:
   flakiness and nondeterminism, redundancy, coverage gaps, weak assertions, isolation
   and structure, test doubles, fixtures and setup, speed, and obsolete or uncollected
   tests.
3. **Gather evidence** with the capabilities recorded in the profile, or their
   fallbacks.
   - Compare what the runner collects in `path` with the tests defined there, to catch
     tests that never run.
   - Run in randomized order and repeat suspect tests, to confirm order dependence and
     flakiness.
   - Measure coverage of the code under test, to locate untested branches. Then break
     covered code as in step 5, to find behavior that no assertion depends on.
   - Report durations, to find slow tests.

   Mark each finding as confirmed by evidence or inferred from reading.
4. **Prioritize.** Rank findings by impact: tests that cannot fail or that give false
   confidence first, then flakiness, coverage gaps, maintainability, and speed.

### 4. Plan

Write a concrete plan before editing anything.

- For `create`: the files to create inside `path`, located and named as the profile's
  conventions dictate; each test with the behavior it verifies and its level; the
  fixtures and helpers to reuse or add, with their scope; parametrization tables; tags;
  and how each test relates to existing coverage.
- For `update`: the tests to remove, merge, rewrite, and add, each with its reason;
  fixture changes; and file moves or splits within `path`. For every test removed or
  merged, name the test that still covers its behavior, or explain why the behavior no
  longer exists.
- For both: the changes the work needs outside `path`, as proposals.

Share the plan together with the profile. Then:

- Proceed without waiting when every change stays inside `path` and keeps every existing
  behavior covered. Consolidation of this kind is the job itself: merging duplicates,
  renaming tests, moving or splitting files within `path`, and deleting a file once its
  tests are ported.
- Wait for the user's confirmation before dropping coverage of behavior that still
  exists, changing production code, adding a dependency, or applying any proposal
  outside `path`.
- Carry out everything that needs no confirmation in a non-interactive run, where no one
  can respond. List the rest in the report as proposals.

### 5. Implement

- Apply the quality standards below, expressed through the conventions and
  infrastructure recorded in the profile.
- Work in small steps: change one file, run its tests, then move on. Each failure then
  points at a single change.
- Keep the intent of every rewritten test: it verifies the same behavior, more precisely
  or more reliably, unless the plan says otherwise.
- Prove that the important tests can fail. Confirm that each key new or rewritten test
  passes on the unmodified code. Then temporarily introduce a small defect in the code
  under test, such as an inverted condition or an off-by-one boundary. The test must
  fail with a clear message from an assertion about the broken behavior. A failure in
  setup, collection, or unrelated code proves nothing, and a test that failed before the
  defect proves nothing either. A test that cannot fail protects nothing. The defect is
  never part of the change: revert it at once, and confirm that the code under test is
  unchanged against the project's version control or a saved copy. Then rerun the test
  to see it pass.

### 6. Verify

Use the entry points and capabilities from the profile, in this order:

1. Run the new and changed tests. They must pass.
2. Run everything in `path` and compare the result with the baseline: no new failures
   and no unintended new skips. Also run the project's entry point when it covers tests
   outside `path` at little cost, because a change inside `path` can break tests that
   share its helpers. Compare the total runtime of the same command as well, because
   duration reports miss a small cost repeated in many tests, such as an expensive test
   double or setup step. Trace growth beyond run-to-run variation to its cause, and
   remove the cause unless the coverage it buys justifies it.
3. Check the new and changed tests for determinism: run them repeatedly and in
   randomized order, using the capabilities from the profile or their fallbacks. Ten
   repetitions suit fast tests. Tests that involve concurrency, time, or I/O deserve
   more.
4. Run the project's linters, formatters, and type checks through its own entry points,
   over the whole scope those entry points cover, not only on the changed files. Some
   checks relate files to each other, and a run limited to the changed files misses
   their findings, such as duplicated code across modules or type errors at call sites.
   Prefer modes that report without rewriting files. Compare the findings with the
   baseline, and fix every finding your changes introduce, including one reported in a
   file you did not touch: resolve it inside `path`, or propose the change outside it.
5. Review the working tree: every changed file lies inside `path`, and no stray
   artifacts remain, such as coverage data, temporary files, or unintentionally updated
   snapshots.
6. Measure coverage again for comparison when the analysis measured it.
7. Stop and remove the services and background processes you started, as ground rule 9
   requires, and confirm that none of them remain.

Fix the cause of a failing check and rerun it. State exactly what was not verified and
why when a check cannot run. Report only results you observed.

### 7. Report

Deliver the report as the last message, after all work has finished. Make it
self-contained: a reader who sees only the report must find every section in it. Restate
content that earlier messages already showed instead of referring back to it with
phrases such as "as given above".

Follow the template for the mode in `references/report-templates.md`, and omit the
sections that do not apply. The project profile always applies. Keep the report factual
and specific: name files, tests, commands, and numbers.

## Test quality standards

All new and changed test code meets these standards. They are stack-neutral: express
each one through the mechanisms the profile found in this project.

- **Behavior over implementation.** Exercise the public interface and assert observable
  outcomes: return values, state changes, emitted events, persisted data, and errors.
  Tests coupled to private helpers or internal call order break on every refactor
  without catching more defects.
- **One behavior per test,** named for the behavior, condition, and expected outcome in
  the project's naming style. A failure then reads as a violated specification.
- **Visible Arrange-Act-Assert.** Show the details that matter to the test, and move
  incidental setup into fixtures, factories, or builders with sensible defaults. Keep
  loops and conditionals out of test bodies, because they hide which case failed and
  tend to mirror the implementation.
- **Precise assertions.** Assert the exact expected value, state, or error type, with
  the relevant part of its message. Avoid assertions that can barely fail: truthiness
  checks, "does not raise", and broad error types. Avoid assertions that over-specify
  incidental details as well: timestamps, generated identifiers, and full object dumps.
  Compare floating-point values with a tolerance.
- **Explicit data.** Use meaningful values and name the significant ones. A reader then
  sees why an input produces its output. Generate unique data when tests share an
  external store.
- **Isolation and determinism.** No test depends on another test, on execution order, or
  on shared mutable state. Control every source of nondeterminism: time through a fake
  or injected clock; randomness through a seeded generator whose seed is reported;
  concurrency through explicit synchronization instead of sleeps; and the environment
  through temporary locations and scoped, restored changes to environment variables and
  configuration. Release resources even when a test fails.
- **Test doubles at boundaries.** Replace what is slow, nondeterministic, or outside
  your control, such as network services, clocks, and third-party interfaces. Prefer
  real collaborators, then fakes, then stubs. Use mocks only when the interaction is the
  behavior, such as a message being sent. Keep doubles faithful to the real interface
  with the interface checking that the project's tooling provides, and restore them
  after each test.
- **Parametrized cases** for one behavior across inputs, each with a readable label. Do
  not fold unrelated behaviors into one table.
- **Right-sized fixtures.** Use the narrowest scope that keeps tests isolated, and widen
  it only for expensive resources that tests do not mutate. Guarantee teardown.
- **Lowest sufficient level.** Verify logic with unit tests, wiring and real
  dependencies with integration tests, and critical user journeys with a few end-to-end
  tests. Gate slow or service-dependent tests the way the project does.
- **Readable over clever.** Remove copy-paste with parametrization and fixtures, but
  tolerate some repetition: three similar lines beat a premature helper, and a test
  reads top to bottom without jumping between abstractions.
- **No masking.** Do not treat flakiness with retries, longer sleeps, or larger
  timeouts. Find and remove the cause. Never leave a marker in place that restricts a
  run to selected tests, and give every skip a reason.
- **Regression tests reproduce the failure.** A test for a fixed defect fails on the
  code before the fix.
