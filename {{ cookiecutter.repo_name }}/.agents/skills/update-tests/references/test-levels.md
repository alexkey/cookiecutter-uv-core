# Test Levels

Use this guide to choose the level for each behavior and to apply the practices
specific to that level. Projects name levels differently; map these
descriptions onto the project's own terms and locations, as recorded in the
project profile.

## Contents

- [Choosing a level](#choosing-a-level)
- [Unit](#unit)
- [Integration](#integration)
- [System](#system)
- [End-to-end](#end-to-end)
- [Complementary techniques](#complementary-techniques)

## Choosing a level

Verify each behavior at the lowest level that can fail for the reasons you care
about. Lower levels are faster, more precise, and more deterministic; higher
levels catch defects in the wiring between parts that lower levels cannot see.

- Logic, calculations, validation, and state machines belong in unit tests.
- Queries, serialization, migrations, framework configuration, and calls to
  real dependencies belong in integration tests.
- A deployed or fully assembled service's contract belongs in system tests.
- A few critical user journeys belong in end-to-end tests.

Keep the project's existing balance between levels unless it causes real
problems, such as a slow or flaky suite dominated by high-level tests. When a
behavior is already verified at a lower level, a higher-level test adds value
only by checking that the parts are connected.

The location given to the skill usually fixes the level: where it holds tests
of one level, write tests of that level there, and report behaviors that need
another level as follow-ups instead of placing them elsewhere.

Tests that need services the environment may lack, such as a database, a
browser, or credentials, follow the project's convention when the service is
unavailable. Some projects skip such tests with a clear reason; others fail
loudly so that automation never passes silently. Do not change that convention
without the user's agreement.

## Unit

- **Verifies:** one unit of behavior, such as a function, class, or small
  cluster of collaborating objects, through its public interface.
- **Real versus replaced:** collaborators inside the unit stay real; process
  boundaries are replaced, such as the network, the clock, randomness, and
  third-party services.
- **Speed:** milliseconds per test; the whole unit suite runs on every change.
- **Determinism:** no I/O beyond temporary directories, no real time, and
  seeded randomness.
- **Typical gaps:** error paths, boundary values, and invalid input.

## Integration

- **Verifies:** the code working with a real dependency, such as a database,
  message broker, filesystem, cache, or framework layer.
- **Real versus replaced:** the dependency under test is real, running locally
  or in a container; unrelated external services are replaced.
- **Data:** each test creates the data it needs, with unique keys, or runs
  inside a transaction rolled back afterward. Apply schema migrations once per
  session, not per test.
- **Determinism:** dynamic ports, readiness checks with deadlines instead of
  sleeps, explicit ordering in queries, and cleanup that runs on failure.
- **Gating:** mark tests that need services, so developers can run the fast
  suite alone.

## System

- **Verifies:** an assembled or deployed service through its external
  interface, such as an HTTP API, CLI, or message contract.
- **Real versus replaced:** the service and its own dependencies are real;
  third-party services outside the team's control are replaced with stubs or
  sandboxes.
- **Data:** seed through the public interface or dedicated fixtures; isolate
  tests by unique identifiers rather than by resetting shared environments.
- **Determinism:** wait for observable readiness; assert on the contract, such
  as status codes, payload schemas, and side effects, rather than on internal
  state.

## End-to-end

- **Verifies:** a user journey across the whole stack, usually through a
  browser, mobile client, or terminal.
- **Scope:** keep the count small; reserve end-to-end tests for revenue- or
  safety-critical flows and for wiring that no lower level can observe.
- **Selectors and waiting:** use accessible roles, labels, or dedicated test
  identifiers; rely on auto-waiting assertions instead of fixed waits.
- **Isolation:** a fresh browser context per test, data created through APIs or
  fixtures, and no dependence on another test's state.
- **Determinism:** stub third-party services, control the clock, disable
  animations where the framework allows, and record traces or screenshots on
  failure for diagnosis.

## Complementary techniques

These apply across levels and supplement example-based tests rather than
replace them.

- **Contract tests** verify the agreement between a consumer and a provider,
  using consumer-driven contracts or validation against a published schema, so
  services can change independently.
- **Property-based tests** state invariants that hold for all inputs, such as
  round-trips, idempotence, ordering, and conservation laws, and let the
  framework search for counterexamples. Keep seeds reproducible and record
  minimized failing examples as regular tests.
- **Snapshot and golden-file tests** suit large, stable outputs such as
  serialized formats and rendered text. Keep snapshots small and reviewed;
  never update them without reading the diff. Prefer targeted assertions for
  logic.
- **Regression tests** reproduce a specific past defect and name it, for
  example by issue reference, so the reason for the test survives.
- **Performance and load tests** need controlled environments and statistical
  thresholds. Keep them out of the regular suites, which must stay fast and
  deterministic.
