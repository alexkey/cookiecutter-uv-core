# Infrastructure

Read this before building an image, running the Compose stack, or changing anything
under `docker/`. The files named here define the image tags, versions, and
credentials. Read the values from those files.

## Rules

1. Do not run `make docker-clean` unless the user names that target. It removes every
   container on the host, then prunes all unused images, networks, the build cache,
   and anonymous volumes. The removal covers the whole host, not only the project.
2. Ask before starting or stopping the Compose stack. `make docker-compose` ends with
   `docker compose down --volumes`, which discards the database contents.
3. Keep published ports bound to `127.0.0.1`. Without an explicit address, Docker
   publishes a port on every host interface.
4. Keep `docker/Dockerfile.x86_64`, `docker/Dockerfile.arm64`, and
   `docker/Dockerfile.aarch64` identical. The Makefile selects one by the host's
   `uname -m`. A change to one file therefore belongs in all three.
5. Add a project file to the `ADD` instruction in the Dockerfiles when the image build
   needs it. The build copies `src/` and an explicit list of files, not the whole
   project.

## Image

`make docker-build` builds `{{ cookiecutter.service_name }}:<version>` for the platform
in `DOCKER_BUILD_PLATFORM`. It needs `uv.lock`.

- The image is a development environment, not a deployment artifact: it installs the
  project with `make venv` and `make install`, and its entry point is a shell.
- Inside the container, the project directory is
  `/usr/local/src/{{ cookiecutter.service_name }}` and the virtual environment is
  `{{ cookiecutter.docker_prefix }}/.venv`, set through `UV_PROJECT_ENVIRONMENT`. The
  environment lives outside the project directory because Compose mounts the host
  project there, where a host `.venv` would otherwise collide with it.
- The same `make` targets work inside the container. Sourced with `. ./venv`, the
  `venv` helper script activates the container's environment when it exists and the
  local `.venv` otherwise.

## Compose stack

`docker/docker-compose.yml` defines three services:

| Service | Purpose | Published on the host |
| --- | --- | --- |
| `{{ cookiecutter.service_name }}` | The project image with the host project mounted | `127.0.0.1:${DOCKER_HOST_PORT}` (default 8000) |
| `postgres` | PostgreSQL | `127.0.0.1:5432` |
| `redis` | Redis | not published |

- The service container waits for PostgreSQL with `docker/scripts/wait_for_pg.py`,
  then opens a shell. It does not start the application.
- The container receives its settings from the `environment:` block, including a
  database URL that points at the `postgres` service.
- From the host, the same database is reachable at
  `postgresql+asyncpg://<user>:<password>@localhost:5432/<database>`. The Compose
  file sets all three values to `{{ cookiecutter.postgres_user }}`. Export the URL as
  `{{ cookiecutter.env_prefix }}DATABASE_URL` or put it in `.env.local` to run the
  service or `make autotest` on the host.

## Targets

| Target | Behavior |
| --- | --- |
| `make docker-info` | Lists images, containers, and volumes |
| `make docker-build` | Builds the image; `DOCKER_EXTRA_OPTS=--progress=plain` shows the full build output |
| `make docker-compose` | Starts the stack in the foreground and removes it, volumes included, on exit |
| `make docker-logs` | Follows the logs of the running stack until interrupted |
| `make docker-shell` | Opens `DOCKER_COMMAND` in the running service container; the default command is a shell |
| `make docker-run` | Runs a temporary container from the image with the project mounted; `DOCKER_EXTRA_OPTS="--publish 127.0.0.1:8000:8000"` publishes its port |
| `make docker-clean` | Removes every container and image on the host and prunes anonymous volumes; see rule 1 |

- Build the image with `make docker-build` before `make docker-compose`. The Compose
  file refers to the image and does not build it.
- `make docker-compose` and `make docker-logs` block until interrupted. Run them in a
  separate terminal or as a background process, and issue further commands from
  another shell.
- `make docker-run` and `make docker-shell` are interactive and need an attached
  terminal.
- `make env-show-docker` prints the Docker variables with their values, such as
  `DOCKER_HOST_PORT` and `DOCKER_CONTAINER_PORT`.
