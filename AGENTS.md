# Agent Instructions

## Architecture

- **Docker-in-Docker**: The app runs inside a privileged Docker container and manages other Docker containers via `python-on-whales`. Requires `privileged: true` in compose.
- **Server types** are validated in `utils/validators.py` (`ALLOWED_SERVER_TYPES`) and passed as `TYPE=` env var to the `itzg/minecraft-server` Docker image, which handles the actual server setup.
- **Spawn lifecycle**: Each server is a directory under `spawns/` containing `docker-compose.yml`, `data/` (world/mods), and `backups/`. The app generates compose files dynamically.
- **Templates** use Bottle's SimpleTemplate syntax (`%if`, `{{var}}`, `%include`).

## Running the App

```bash
docker compose down --remove-orphans && docker compose up --build
```

- Web UI: `http://localhost:8889` (dev port mapping)
- Minecraft servers: ports `25565-25665` (mapped to `26665-26765` in dev)
- No test suite exists. Verify changes manually or with `python3 -m py_compile <file>`.
- **Always rebuild after changes**: Run `docker compose down --remove-orphans && docker compose up --build` after making changes to test them. The app runs inside Docker, so code changes require a rebuild to take effect.
- **Container name conflicts**: If you get "container name already in use" errors, run `docker rm -f <container-name>` to force remove the conflicting container, then rebuild.
- **Dev and prod side by side**: Compose targets containers by project name, which defaults to the directory basename — identical for the dev and prod checkouts. `COMPOSE_PROJECT_NAME` must be set in `.env` (`minecraft-spawner-dev` in dev, `minecraft-spawner` in prod), otherwise `docker compose down` in one checkout tears down the other's container.

## Key Files

- `app.py` - Bottle routes and request handling
- `models/spawn.py` - `Spawn` class: represents one Minecraft server instance
- `utils/spawner.py` - `Spawner` class: manages all spawns, creates/loads them
- `utils/validators.py` - Input validation (server types, versions, ports, names)
- `templates/*.tpl` - Bottle SimpleTemplate HTML files

## Environment Variables

Set in `.env` (copy from `.env.example`):
- `GEMINI_API_KEY` - Optional, enables AI log analysis
- `WEB_PANEL_URL` - URL shown in UI (default: `http://localhost:8888`)
- `SERVER_CONNECTION_HOST` - Host shown to players (default: `localhost`)
- `IS_TEST` - Set to `true` to show "TEST SITE" banner in UI (default: `false`)
- `WEB_PORT` - Host port for the web UI (default: `8888`)
- `MC_PORT_START` / `MC_PORT_END` - Host port range for Minecraft servers (default: `25565`-`25665`)
- `CONTAINER_NAME` - Docker container name (default: `minecraft-spawner`)

Runtime vars in `docker-compose.yml`:
- `SPAWNS_DIR=/app/spawns`
- `ARCHIVED_BACKUPS_DIR=/app/backups`
- `TZ=America/Vancouver` (backup scheduler uses this)

## Server Type Implementation

When adding a new server type (e.g., NEOFORGE, FABRIC):
1. Add to `ALLOWED_SERVER_TYPES` in `utils/validators.py`
2. Update `validate_forge_version()` to handle type-specific version formats
3. Add `<option>` to the type dropdown in `templates/index.tpl`
4. Update `utils/spawner.py` to set the correct Docker env var (e.g., `NEOFORGE_VERSION` vs `FORGE_VERSION`)
5. Update `models/spawn.py` `_sync_docker_compose_with_spawn_settings()` for the same env var
6. Update `utils/spawner.py` `loadSpawns()` to parse the env var by key name (not index)
7. Update `templates/spawn.tpl` to show/hide version fields conditionally
8. Update `templates/documentation.tpl`

The `itzg/minecraft-server` image supports many types natively via `TYPE=` env var.

## Gotchas

- **No tests**: Run `python3 -m py_compile <file>` to check syntax. Manual verification required.
- **Threaded server**: The app runs under waitress with 8 worker threads (wsgiref wedged on stalled clients). The cwd is process-global, so compose operations that chdir must use the `_compose_dir()` context manager in `models/spawn.py` (lock + cwd restore).
- **Startup ensure-up**: on every startup the panel runs a non-forced `compose up` for each spawn (`Spawner.ensure_all_spawns_up()`). This is required because the inner dind daemon's `/var/lib/docker` is an anonymous volume — recreating the panel container wipes all Minecraft containers, and the persisted compose files in `spawns/` are what restores them. Non-forced means running servers are not bounced.
- **Env var order matters**: `loadSpawns()` now parses by key name, but older code assumed index-based parsing. Always use key-based lookup.
- **Backup archival**: When a spawn is deleted, the app archives its latest backup. Metadata includes server type and versions.
- **Mod uploads**: Bulk uploads stage files in batches, then swap the mods directory. Single uploads use a lightweight restart flow.
- **Port range**: Hardcoded to `25565-25665`. Validation prevents ports outside this range.
- **Spawn names**: Must be unique, alphanumeric + hyphens/underscores, no path traversal (`..`, `/`, `\`).
