# Database access

Read this before writing code that creates sessions, runs queries, or configures the
engine. The helpers live in `src/{{ cookiecutter.repo_name }}/app/db/database.py` and
use asynchronous SQLAlchemy over the `postgresql+asyncpg` driver.

## Rules

1. Use one engine and one session factory for the lifetime of the process. Take the
   session factory from the `AppState` that `app_lifespan()` yields. Do not create an
   engine or a session factory per request, per task, or inside a command body.
2. Run each unit of work inside one `async with create_session(session_maker)` block.
   The block is a single transaction: it commits on a clean exit, rolls back on any
   exception, and always closes the session. Do not call `session.begin()` or
   `session.commit()` inside the block. Raise an exception to roll back.
3. Do not rely on attribute access to load data after a commit or to load a
   relationship. Fetch server-generated values with
   `await session.refresh(obj, ["attr"])` and load relationships eagerly, for example
   with `selectinload()`.
4. Pass the database URL as the `SecretStr` from `get_settings().DATABASE_URL`. Unwrap
   it only where a driver requires a plain string.

## Session lifecycle

```python
async with app_lifespan() as app_state:
    session_maker = app_state["session_maker"]

    async with create_session(session_maker, context="import-job") as session:
        await session.execute(...)
```

- With the default `raise_on_exc=True`, `create_session()` re-raises database errors
  and unexpected errors after the rollback. With `raise_on_exc=False`, it logs them
  and suppresses them.
- `asyncio.CancelledError` always rolls back and propagates. Do not catch it around
  the block.
- `context` labels the session in log records. `verbose=True` logs each lifecycle
  step.

## Engine lifecycle

Follow the order that `app_lifespan()` applies in code outside the lifespan, such as a
script or a test:

- `create_engine(url)` returns `None` when creation fails and logs the error with the
  password masked. Pass `raise_on_exc=True` to fail fast instead.
- `create_sessionmaker(engine)` builds the single session factory for that engine.
- `await dispose_engine(engine)` closes the pooled connections. It logs SQLAlchemy
  errors raised during disposal and suppresses them.

## Defaults and their rationale

`DEFAULT_ASYNC_ENGINE_PARAMS` and `DEFAULT_ASYNC_SESSION_PARAMS` in `database.py` hold
the active values. Override any of them with keyword arguments to `create_engine()`
and `create_sessionmaker()`. Do not edit the defaults for a single caller.

- **`expire_on_commit=False`.** With expiry enabled, the first attribute access after
  a commit triggers an implicit refresh query. Under asyncio, that I/O can run outside
  SQLAlchemy's async bridge and raise `MissingGreenlet`. The cost is that objects are
  not re-fetched after a commit. Server-generated values come from `server_default`,
  `server_onupdate`, and `Computed`. Such a value is present only when SQLAlchemy
  populated it during the flush, typically through `RETURNING`. Otherwise, it stays
  expired or stale. Rule 3 follows from this.
- **`pool_pre_ping=True`** checks a connection when it leaves the pool and replaces
  one that was dropped while idle.
- **`pool_use_lifo=True`** keeps traffic on a small set of connections, which lets the
  surplus ones idle out on the server during quiet periods.
- **`pool_recycle=1800`** caps connection age. Keep it below the shortest idle timeout
  of any component in the connection path, such as PgBouncer, a load balancer, or
  NAT. A component that closes idle connections sooner requires a lower value, such
  as 300 seconds.
- **`pool_reset_on_return="rollback"`** releases locks and transaction resources when
  a connection returns to the pool.

Pool classes outside the `QueuePool` hierarchy reject the queue-pool options.
`NullPool` is one of them. `create_engine()` drops the queue-pool defaults for such a
pool. A queue-pool option passed explicitly still raises `TypeError`.

## Related

- URL validation: `check_database_url()` in `app/core/config.py`.
- Fixtures and fakes for database tests: `testing.md`.
- A local PostgreSQL instance: `infrastructure.md`.
