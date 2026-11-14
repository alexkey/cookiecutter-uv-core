# Test Levels

Use this guide to choose the level for each behavior and to apply the practices specific
to that level. Projects name levels differently. Map these descriptions onto the
project's own terms and locations, as recorded in the project profile.

## Contents

- [Choosing a level](#choosing-a-level)
- [Unit](#unit)
- [Integration](#integration)
- [System](#system)
- [End-to-end](#end-to-end)
- [Complementary techniques](#complementary-techniques)

## Choosing a level

Verify each behavior at the lowest level that can fail for the reasons you care about.
Lower levels are faster, more precise, and more deterministic. Higher levels catch
defects in the wiring between parts that lower levels cannot see.

- Logic, calculations, validation, and state machines belong in unit tests.
- Queries, serialization, migrations, framework configuration, and calls to real
  dependencies belong in integration tests.
- A deployed or fully assembled service's contract belongs in system tests.
- A few critical user journeys belong in end-to-end tests.

Keep the project's existing balance between levels unless it causes problems, such as a
slow or flaky suite dominated by high-level tests. A higher-level test of a behavior
that a lower level already verifies adds value only by checking that the parts are
connected.

The location given to the skill usually fixes the level. Write tests of the level that
the location holds, and report behaviors that need another level as follow-ups instead
of placing them elsewhere.

Some tests need services that the environment may lack, such as a database, a browser,
or credentials. Such tests follow the project's convention when the service is
unavailable. Some projects skip them with a clear reason. Others fail loudly to keep
automation from passing silently. Change that convention only with the user's agreement.

## Unit

- **Verifies:** one unit of behavior, such as a function, class, or small cluster of
  collaborating objects, through its public interface.
- **Real versus replaced:** collaborators inside the unit stay real. Process boundaries
  are replaced, such as the network, the clock, randomness, and third-party services.
- **Speed:** milliseconds per test. The whole unit suite runs on every change.
- **Determinism:** no I/O beyond temporary directories, no real time, and seeded
  randomness.
- **Typical gaps:** error paths, boundary values, and invalid input.

## Integration

- **Verifies:** the code working with a real dependency, such as a database, message
  broker, filesystem, cache, or framework layer.
- **Real versus replaced:** the dependency under test is real and runs locally or in a
  container. Unrelated external services are replaced.
- **Data:** each test creates the data it needs, with unique keys, or runs inside a
  transaction rolled back afterward. Apply schema migrations once per session, not per
  test.
- **Determinism:** dynamic ports, readiness checks with deadlines instead of sleeps,
  explicit ordering in queries, and cleanup that runs on failure.
- **Gating:** mark tests that need services, to let developers run the fast suite alone.

## System

- **Verifies:** an assembled or deployed service through its external interface, such as
  an HTTP API, CLI, or message contract.
- **Real versus replaced:** the service and its own dependencies are real. Third-party
  services outside the team's control are replaced with stubs or sandboxes.
- **Data:** seed through the public interface or dedicated fixtures. Isolate tests by
  unique identifiers rather than by resetting shared environments.
- **Determinism:** wait for observable readiness. Assert on the contract rather than on
  internal state: status codes, payload schemas, and side effects.

## End-to-end

- **Verifies:** a user journey across the whole stack, usually through a browser, mobile
  client, or terminal.
- **Scope:** keep the count small. Reserve end-to-end tests for revenue- or
  safety-critical flows and for wiring that no lower level can observe.
- **Selectors and waiting:** use accessible roles, labels, or dedicated test
  identifiers. Rely on auto-waiting assertions instead of fixed waits.
- **Isolation:** a fresh browser context per test, data created through APIs or
  fixtures, and no dependence on another test's state.
- **Determinism:** stub third-party services, control the clock, disable animations
  where the framework allows, and record traces or screenshots on failure for diagnosis.

## Complementary techniques

These apply across levels and supplement example-based tests rather than replace them.

- **Contract tests** verify the agreement between a consumer and a provider, through
  consumer-driven contracts or validation against a published schema. The services can
  then change independently.
- **Property-based tests** state invariants that hold for all inputs, such as
  round-trips, idempotence, ordering, and conservation laws, and let the framework
  search for counterexamples. Keep seeds reproducible, and record minimized failing
  examples as regular tests.
- **Snapshot and golden-file tests** suit large, stable outputs such as serialized
  formats and rendered text. Keep snapshots small and reviewed, and read the diff before
  updating them. Prefer targeted assertions for logic.
- **Regression tests** reproduce a specific past defect and name it, for example by
  issue reference. The reason for the test then survives.
- **Performance and load tests** need controlled environments and statistical
  thresholds. Keep them out of the regular suites, which must stay fast and
  deterministic.
