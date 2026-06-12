# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

A lightweight web panel (Python + Bottle + Bulma CSS) for deploying and managing Minecraft server containers. Each managed server runs as its own Docker container using the `itzg/minecraft-server` image.

## Commands

**After EVERY code change, rebuild and recreate the container** — the app runs inside Docker, so edits do not apply until you do. Always finish a change by running the rebuild command below so the user can immediately test it.

```bash
# Rebuild and recreate after every code change (-d to not block the terminal)
docker compose down --remove-orphans && docker compose up --build -d

# Syntax check (there is NO test suite; verify changes manually)
python3 -m py_compile app.py

# Fix "container name already in use" errors
docker rm -f <container-name>
```

- Web UI: `http://localhost:8889` in dev (`8888` default, set via `WEB_PORT` in `.env`)
- Minecraft server ports: `25565-25665` (mapped to `26665-26765` in dev)
- Config comes from `.env` (copy `.env.example`); `GEMINI_API_KEY` is optional and only enables AI log analysis and the "Ask the docs" assistant. `ADMIN_USERNAME`/`ADMIN_PASSWORD` seed the first admin account on first start; `panel_data/` holds the users db and cookie secret (never commit it)

## Architecture

**Docker-in-Docker**: The app itself runs in a privileged container (`docker-compose.yml` at repo root) and manages sibling Minecraft containers via `python-on-whales` over the mounted Docker socket. Volume paths in generated compose files must be absolute so the inner Docker daemon can resolve them.

**Core flow** (three layers):
- `app.py` — single-file Bottle app holding all routes. Creates one global `Spawner`, starts the `BackupScheduler` daemon thread, and serves Bottle SimpleTemplate files from `templates/` (`%if`, `{{var}}`, `%include` syntax).
- `utils/spawner.py` (`Spawner`) — registry of all spawns. Generates each spawn's `docker-compose.yml`, loads existing spawns from disk at startup (`loadSpawns()`), finds free ports, and handles archived-backup restore. On every startup, `ensure_all_spawns_up()` runs a non-forced `compose up` per spawn — required because the inner dind daemon's state is on an anonymous volume, so recreating the panel container wipes all MC containers and they must be restored from the persisted `spawns/` compose files (running servers are not bounced).
- `models/spawn.py` (`Spawn`) — one Minecraft server instance. Wraps docker compose up/stop/start/purge, server.properties editing, mod management, backups, RCON console commands, and player-count queries.

**Spawn lifecycle**: each server is a directory under `spawns/<name>/` containing `docker-compose.yml` (generated, the source of truth for type/version/port), `data/` (world, mods, server.properties), and `backups/`. Deleting a spawn archives its latest backup into `backups/` (repo root, `ARCHIVED_BACKUPS_DIR`) with a `.json` metadata sidecar used for restore. **Never commit or hand-edit `spawns/` or `backups/` — they hold live server data.**

**Supporting utils**: `utils/validators.py` (`ALLOWED_SERVER_TYPES` = FORGE, NEOFORGE, VANILLA; port/name/username/version validation), `utils/backup_scheduler.py` (daily backups, timezone hardcoded to `America/Vancouver`), `utils/log_analyzer.py` (Gemini API via raw urllib: log analysis + docs Q&A), `utils/users.py` (accounts and auth — see below).

**Auth and eggs**: accounts live in `panel_data/users.json` (volume-mounted; all access goes through `utils/users.py` under its module lock — never touch the file elsewhere). Passwords are stdlib scrypt; sessions are Bottle signed cookies (secret from `COOKIE_SECRET` env or auto-persisted at `panel_data/.cookie_secret`, so logins survive rebuilds). The first admin is seeded from `ADMIN_USERNAME`/`ADMIN_PASSWORD` only when `users.json` doesn't exist. New accounts (including the seeded admin) carry `must_change_password`; a `before_request` hook in `app.py` locks flagged users to `/password` (and `/logout`) until they set their own password. Each spawn has a `.owner` JSON sidecar (absent = unowned); it's read in `Spawn.__init__`, so `loadSpawns()`/`ensure_all_spawns_up()` preserve ownership — only POST /spawn, archived restore, and admin user-deletion write it. Eggs are capacity slots: a user's `eggs` balance = max concurrently *running* servers they own; anonymous visitors share one slot over unowned spawns. Enforcement lives in `check_egg_capacity()` in `app.py`, called under `_capacity_lock` (check + container start in one critical section) from create/start/recreate/archived-restore. Permissions: owned spawns manageable by owner + admins only (`require_spawn_permission` decorator on all mutating spawn routes); unowned spawns manageable by anyone; viewing is open to all.

## Adding a new server type

The `itzg/minecraft-server` image supports many types natively via `TYPE=` env var. To expose one:
1. Add to `ALLOWED_SERVER_TYPES` in `utils/validators.py`; update `validate_forge_version()` for type-specific version formats
2. Add `<option>` to the type dropdown in `templates/index.tpl`
3. Set the correct version env var (e.g. `NEOFORGE_VERSION` vs `FORGE_VERSION`) in `utils/spawner.py` `create_or_modify_spawn()` and `models/spawn.py` `_sync_docker_compose_with_spawn_settings()`
4. Parse it in `Spawner.loadSpawns()` — always by env key name, never by list index
5. Show/hide version fields in `templates/spawn.tpl`; update `templates/documentation.tpl`

## Gotchas

- The app serves requests on multiple threads (waitress, `threads=8`), but the cwd is process-global. Any compose operation that needs to chdir into a spawn directory must go through the `_compose_dir()` context manager in `models/spawn.py`, which holds a process-wide lock and restores the previous cwd.
- Env vars in generated compose files are a list of `KEY=value` strings — always look up by key, not position.
- Port range `25565-25665` is hardcoded in validation and port auto-selection.
- Spawn names must be unique, alphanumeric plus hyphens/underscores; validation blocks path traversal.
- Dev and prod checkouts share the same directory basename, so the default compose project name collides — `COMPOSE_PROJECT_NAME` must stay set in `.env` (`minecraft-spawner-dev` in dev, `minecraft-spawner` in prod) or `docker compose down` in one checkout tears down the other's container. Prod lives at `/SSD/apps/minecraft-server-spawner/minecraft-server-spawner`.
- The compose service is named `panel`, not `minecraft-spawner` — compose publishes the service name as a DNS alias on the shared external `private`/`public` networks, and a service named `minecraft-spawner` collided with prod's container name, making the reverse proxy round-robin prod traffic to the dev panel. The reverse proxy must route by `CONTAINER_NAME` (unique per env), never by service name.- Bulk mod uploads stage files in batches under `.mod_upload_batches/`, then swap the mods directory and do a lightweight restart; single uploads restart directly.

## Conventions

- Stack is fixed: Python, Bottle, Bulma CSS, Docker (see `.windsurf/rules/stack.md`). Reference docs: [itzg image](https://docker-minecraft-server.readthedocs.io/en/latest/), [Bottle](https://bottlepy.org/docs/dev/), [Bulma](https://bulma.io/documentation/).
- Never use Bulma's `is-light` modifier — the panel is viewed on a dark background and `is-light` forces glaring near-white elements. Use the default element (theme-aware grey) or the solid color variant (`is-info`, `is-danger`, …) instead.
- When changing user-facing behavior, update both `README.md` and the in-app docs (`templates/documentation.tpl`).
- `AGENTS.md` carries the same agent guidance — keep the two files in sync when editing either.
