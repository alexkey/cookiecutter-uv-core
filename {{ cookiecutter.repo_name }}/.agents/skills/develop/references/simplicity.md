# Simplicity

Read this while designing in stage 1, and again in stage 2 before adding an
abstraction, an option, a fallback, or an optimization. Code that works but
is more complex than the problem requires costs every later reader and every
later change.

Each rule names the simple default and the condition that justifies the
heavier form. Choose the default unless the condition holds now, not in an
anticipated future. When the heavier form is justified, record the reason
in the plan's Decision Log, so that the next reader does not undo it.

## Contents

- Abstraction layers
- Generalization
- Indirection
- Future-proofing
- Fallbacks
- Optimization

## Abstraction layers

- **Wrappers.** Call the underlying function directly. Add a wrapper only
  when it changes the contract that callers see, for example by validating,
  translating, mapping errors, or narrowing the interface.
- **Factories.** Construct the single implementation directly. Introduce a
  factory when several implementations are selected at run time.
- **Interfaces.** Define an interface where it is consumed, not beside its
  implementation, and only when the consumer needs to substitute
  implementations, including test doubles at a boundary.
- **Layers.** Give each layer its own responsibility. A chain such as
  handler, service, and repository in which each step passes the call
  through collapses into the layer that does the work.
- **Data types.** Use one type per concept. Add a second representation
  with conversions only at a boundary where the formats truly differ, such
  as a wire format and a domain model.

## Generalization

- **Generic mechanisms.** Solve the specific problem. An event bus for one
  event type, or a registry with one entry, is a direct call.
- **Option objects.** Pass two or three options as parameters. Use an
  options object or a builder when the options are many, optional, and
  combined in varying ways.
- **Plugin architecture.** Build an extension point only for extensions
  that exist or that the approved plan requires. Fixed functionality needs
  no plugin mechanism.
- **Catch-all types.** Model distinct variants as distinct types or as a
  closed set of cases, not as one type with many optional fields that only
  some variants use.

## Indirection

- **Pass-through methods.** Do not add a method that only delegates to a
  dependency; let callers use the dependency.
- **Builders and chaining.** Construct a simple value directly. Use a
  builder when construction takes many steps or must enforce invariants
  along the way.
- **Wrapped primitives.** Use the standard types. A custom type is
  justified when it enforces an invariant or prevents a real confusion
  between values of the same representation.
- **Stacked middleware.** Merge processing stages that always run together
  and serve one concern into one stage.

## Future-proofing

- **Unused extension points.** Add no hook, callback, or plugin slot
  without a caller.
- **Versioned internal interfaces.** Keep a single version of an internal
  interface. Versions are for interfaces whose external consumers migrate
  at their own pace.
- **Feature flags.** Use a flag for a decision that changes at run time or
  during a staged rollout, and remove it once the decision is permanent. A
  flag that is always on or always off is dead code.

## Fallbacks

- **Fallbacks that never trigger.** Do not write a default path for a
  condition that cannot occur; state the invariant instead, and fail
  loudly if it is ever violated.
- **Legacy modes.** Remove an old code path that is always disabled, unless
  the plan keeps it for a migration and schedules its retirement.
- **Dual implementations.** Remove the old implementation once nothing
  calls it. During a planned migration, keep both only with validation for
  each and a retirement step.
- **Silent fallbacks.** Fail fast with a clear error instead of catching a
  failure and continuing with a substitute. Fall back only when the
  fallback is specified behavior, and make it visible, for example in a
  log entry or a result that callers can inspect.

## Optimization

- **Caches.** Do not cache data that is read once, such as at startup, or
  rarely. Add a cache for a measured need, with a defined invalidation.
- **Custom data structures.** Use the standard collections. A custom
  structure needs a measured bottleneck that the standard ones cannot
  meet.
- **Worker pools.** Run occasional tasks directly. Pool workers when
  measured throughput requires it.
- **Connection pooling.** Use the simplest connection handling that the
  workload needs, and the pooling the project already has, before adding
  another layer of it.
