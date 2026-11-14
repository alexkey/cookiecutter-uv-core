# Test Smell Catalog

Use this catalog to diagnose existing tests in `update` mode and as a checklist of
mistakes to avoid in `create` mode. Each entry names the symptom, why it matters, and
the usual remedy. A symptom is a lead, not a verdict: confirm it in context before
changing anything.

## Contents

- [Flakiness and nondeterminism](#flakiness-and-nondeterminism)
- [Redundancy](#redundancy)
- [Coverage gaps](#coverage-gaps)
- [Weak and over-specified assertions](#weak-and-over-specified-assertions)
- [Isolation and structure](#isolation-and-structure)
- [Test doubles](#test-doubles)
- [Fixtures and setup](#fixtures-and-setup)
- [Speed](#speed)
- [Obsolete, invalid, and uncollected tests](#obsolete-invalid-and-uncollected-tests)

## Flakiness and nondeterminism

A flaky test fails without a code change. Each false alarm teaches people to ignore
failures. A flaky test therefore costs more than a missing one.

| Symptom | Remedy |
| --- | --- |
| Fixed sleeps or waits for background work | Wait for the condition itself: await the result, join the worker, use an event or future, or poll with a deadline. Use fake timers for timer-driven code. |
| Reading the wall clock, or depending on time zone, daylight saving, or locale | Inject or freeze the clock. Pin the time zone and locale. Avoid inputs near midnight, month ends, and other boundaries unless they are the subject. |
| Unseeded randomness | Seed a generator owned by the test, report the seed on failure, and derive random data from it. |
| Order dependence through module globals, singletons, caches, registries, class attributes, environment variables, or the working directory | Give each test its own state. Reset shared state in guaranteed teardown. Never rely on an earlier test's side effects. |
| Unawaited asynchronous work, unjoined threads or tasks, data races | Await or join everything the test starts. Synchronize explicitly. Run a race detector where the toolchain has one. |
| Real network calls, shared external services, or fixed ports | Replace external services at the boundary in unit tests. Use local or containerized instances, dynamic ports, and readiness checks with deadlines in integration tests. |
| Fixed file paths, leftover files, or reliance on directory listing order | Use per-test temporary directories. Sort listings before comparing them. |
| Unordered results compared as ordered: sets, hash maps, database rows without an explicit ordering, parallel results | Compare as sets or multisets, or sort by a stable key, unless order is the behavior under test. |
| Exact floating-point equality | Compare with an explicit tolerance. |
| Leaked open handles, connections, or threads that break later tests | Release them in teardown that runs even when the test fails. |
| Parallel workers sharing rows, files, ports, or names | Derive unique resources per worker or per test. |
| Retries, rerun plugins, or inflated timeouts that hide intermittent failures | Fix the cause, then remove the masking. Keep end-to-end retries only as a detection tool whose flaky results are reported. |
| Dependence on the developer machine: absolute paths, installed tools, network access, CI variables | Make the dependency an explicit fixture, or gate the test with the project's markers and a clear reason. |

Run a suspect test repeatedly, in randomized order, and in parallel where the runner
supports it, to confirm the suspicion. Bisect the preceding tests to locate an order
dependency: use the runner's bisection facility when it has one, or rerun in a fixed
order while halving the set of tests that run first.

## Redundancy

Redundant tests slow the suite and multiply the edits each behavior change requires,
without catching additional defects.

- **Copy-paste variants** that differ only in input values: merge them into one
  parametrized test, and keep each distinct input class as a labeled case.
- **Subsumed tests:** a test whose assertions are a subset of another test's on the same
  path and inputs. Remove the weaker one.
- **Duplicated input classes:** several cases that exercise the same partition, such as
  three different positive numbers for a check that only cares about sign. Keep one
  representative per partition, plus the boundaries.
- **Tests of the language, framework, or a library** rather than the project's code,
  such as checking that a plain data class stores its fields. Remove them unless they
  guard configuration the project owns.
- **The same behavior at several levels is not automatically redundant.** Keep the
  lowest-level test for detailed logic and higher-level tests for wiring and
  integration. Remove higher-level tests that only recheck logic details.

Name the test that still covers a behavior before removing another test of it. Compare
coverage reports before and after when coverage tooling is available.

## Coverage gaps

In `update` mode, the code under test is the scope that step 3b of the workflow defines.
Code that no test in `path` exercises is a follow-up there unless the instructions bring
it into scope. Within the code under test, look for behaviors that no test verifies,
prioritized by risk:

- public functions, endpoints, commands, or events without tests;
- error paths: exceptions raised and handled, error responses, rollbacks, retries, and
  cleanup after failure;
- boundaries: empty, zero, one, maximum, one past the maximum, off-by-one indexes,
  Unicode and multibyte text, oversized inputs;
- invalid and malicious input, authorization decisions, and secret handling, such as
  masking in logs and error messages;
- state transitions, including invalid ones;
- configuration combinations and defaults;
- concurrency, cancellation, and timeouts;
- regressions: defects fixed in the past that no test reproduces, as the version history
  and linked issues record them.

Coverage percentages are a map, not a goal: a covered line is not a verified behavior
when no assertion depends on it. Use coverage reports to find unexecuted branches, then
decide by risk which of them deserve tests.

High coverage does not show that the covered code is verified. Test that separately:
break the covered code in small ways and run the tests. Typical defects invert a
condition, shift a boundary by one, drop a side effect or an error check, or return a
constant. A defect that every test survives marks a coverage gap or a weak assertion,
even at full line coverage. Record it as a confirmed finding, together with the defect
that exposed it. Concentrate the defects on the riskiest code rather than spreading them
evenly, and keep the count proportionate to the request. Let mutation tooling generate
and run the defects when the profile lists such tooling, and introduce them by hand
otherwise. Either way, follow the procedure for proving that tests can fail: confirm
that the tests pass first, revert each defect at once, and confirm that the code is
unchanged.

## Weak and over-specified assertions

A weak assertion lets broken code pass. An over-specified one makes correct changes
fail.

Weak:

- no assertion, or only "does not raise";
- truthiness or existence checks where an exact value is known;
- broad exception types, such as catching any exception, or an error check that ignores
  the type or the relevant part of the message;
- asserting that a mock was called instead of asserting the outcome;
- assertions inside callbacks or loops that might never run;
- asynchronous assertions that are not awaited;
- assertions that compare the code with itself, such as expected values computed by the
  same logic as the implementation;
- a test that still passes when the code under test is deleted or inverted.

Over-specified:

- whole-object or snapshot comparisons that include timestamps, generated identifiers,
  or other incidental fields;
- full error-message text where only the type and key detail matter;
- exact call counts or call order on collaborators when only the outcome matters;
- exact log text when the behavior under test is a return value or state change.

## Isolation and structure

- several unrelated behaviors in one test, where one failure hides the others;
- names that do not describe behavior, such as a number, "works", or the bare name of
  the function under test;
- logic in the test body, such as loops and conditionals that compute expected values;
- hidden dependencies: implicitly applied or global fixtures, environment assumptions,
  or data created by other tests;
- unexplained magic values;
- large setup blocks that obscure what the test needs;
- commented-out tests, skips without reasons, and skips whose reasons no longer apply;
- markers left in place that restrict a run to selected tests;
- tests at the wrong level or in the wrong place, such as unit tests that require a
  database, or files outside the layout the project uses;
- oversized test modules mixing unrelated subjects;
- helpers complex enough to need their own tests.

## Test doubles

- mocking the unit under test, or its private internals;
- mocking value objects and plain data structures that are cheap to build;
- deep chains of mocks returning mocks, which encode the implementation's structure;
- doubles that drift from the real interface because the tooling does not check them
  against it;
- verifying interactions when the outcome is observable;
- doubles not restored after the test, leaking into later tests;
- replacing time or randomness at the wrong layer, such as patching a library function
  instead of injecting a clock or seed at the seam.

Prefer, in order: real collaborators, in-memory fakes, stubs, then mocks or spies.

## Fixtures and setup

- mutable fixtures shared across tests through a broad scope;
- function-scoped fixtures rebuilding an expensive resource that no test mutates;
- the same fixture or factory duplicated across files instead of shared at the common
  parent;
- fixture chains deep enough to hide a test's real dependencies;
- teardown that does not run when a test fails;
- setup doing work that most tests using it do not need;
- parametrization opportunities missed, or parametrized fixtures that multiply the test
  count without adding coverage.

## Speed

- real sleeps and real timeouts;
- network or service calls where a boundary double suffices;
- integration or end-to-end tests that verify logic a unit test could;
- expensive setup repeated per test without need;
- test doubles generated per test from a large interface where a minimal double
  suffices;
- oversized datasets where a few representative cases suffice;
- serial-only suites caused by shared state, blocking parallel execution.

Measure with the runner's duration report before and after changes, and compare the
total runtime as well. A small cost repeated in every test stays below the notice of a
duration report and shows only in the total.

## Obsolete, invalid, and uncollected tests

- tests for removed features or superseded behavior;
- tests asserting behavior that contradicts the specification, which need a decision on
  which side is wrong before any change;
- tests that always skip, or are disabled without a tracking reason;
- tests that never run because they do not satisfy the runner's collection rules, such
  as a name, location, or declaration the runner does not recognize, or a missing
  registration. Compare the runner's collected list with the tests defined in the files.
