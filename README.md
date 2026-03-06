![image](https://img.shields.io/badge/Bulma-00D1B2?style=for-the-badge&logo=Bulma&logoColor=white) ![image](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)  ![image](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)
# minecraft-server-spawner
Deploy and manage Minecraft server containers from a lightweight web interface.

This project is made with Python for the backend, [Bottle](https://bottlepy.org/docs/dev/) and [Bulma CSS](https://bulma.io/) for the frontend. It uses [itzg's docker image](https://hub.docker.com/r/itzg/minecraft-server) through Docker to spawn Minecraft instances based on the parameters provided from the web interface. The UI is designed to keep multi-server management simple while still exposing the day-to-day actions needed to run and recover servers.

The point of this project was to keep everything as light and simple as possible while utilizing python.

## Features

- Deploy multiple Minecraft server instances from one panel.
- Supports both `VANILLA` and `FORGE` server types.
- Create servers with validated names, validated versions, and automatic port selection when no port is provided.
- Start, stop, recreate, and delete server instances from the UI.
- View live status, current player counts, and server logs.
- Send console commands directly to a running server.
- Edit `server.properties` from the web interface and restart the server with the updated configuration.
- Upload a single mod file or replace the full mods folder for Forge servers.
- Create manual backups, enable daily backups, and configure retention days per server.
- Archive the latest backup automatically before deleting a spawn.
- Restore archived backups into a brand new server with a new name and next available port.
- Optional AI-assisted log analysis when Gemini is configured.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/ftechhelp/minecraft-server-spawner.git
    cd minecraft-server-spawner
    ```

2. Create and activate a virtual environment:
    ```sh
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. Copy the example environment file and configure it:
    ```sh
    cp .env.example .env
    # Optional: set GEMINI_API_KEY to enable log analysis
    ```

## Recommended Deployment

The recommended way to run the app is with Docker Compose:

```sh
docker compose up --build
```

This starts the web panel on `http://localhost:8888` and exposes the Minecraft server port range `25565-25665`.

Persistent data is stored in:

- `./spawns` for per-server definitions, world data, mods, and local backups
- `./backups` for archived backups preserved after spawn deletion

If you prefer to run the Bottle app directly with Python, make sure Docker is available to the process and that the same runtime environment variables used in `docker-compose.yml` are available to the app process.

## Environment Variables

The current Docker Compose configuration sets these runtime environment variables:

- `SPAWNS_DIR` - directory where spawn folders are stored. Default: `./spawns`
- `ARCHIVED_BACKUPS_DIR` - directory for archived backups preserved after server deletion. Default: `./backups`
- `GEMINI_API_KEY` - optional API key used for log analysis
- `GEMINI_MODEL` - optional Gemini model name for log analysis
- `TZ` - timezone used by the app and backup scheduler. Current configuration: `America/Vancouver`

Only `GEMINI_API_KEY` is expected in the `.env` file in the current setup. The other values are already defined in `docker-compose.yml`.

If `GEMINI_API_KEY` is not set, the app still works normally, but the log analysis feature will return a configuration error instead of an analysis.

## Usage

### Start the app

Using Docker Compose:

```sh
docker compose up --build
```

Using Python directly:

```sh
python app.py
```

Then access the web interface at `http://localhost:8888`.

### Create a server

From the home page you can create a spawn with:

- `name` - optional; if blank the app generates a UUID-based name
- `port` - optional; if blank the app assigns the next free port in `25565-25665`
- `type` - `FORGE` or `VANILLA`
- `minecraft_version` - accepts `LATEST`, `X.Y`, or `X.Y.Z`
- `forge_version` - accepts `LATEST`, `X.Y.Z`, or `X.Y.Z.W` for Forge servers

Validation currently prevents duplicate names, duplicate spawn directories, duplicate ports, invalid name characters, and invalid version formats.

### Manage a server

Each spawn page currently supports:

- start, stop, recreate, refresh, and delete operations
- live logs with manual refresh and streaming
- AI log analysis when Gemini is configured
- console command execution
- mod uploads and full mod-folder replacement
- direct editing of `server.properties`
- manual backups, restore, delete, and daily backup scheduling

### Backups

- Manual backups are stored inside each spawn folder under its local backups directory.
- Daily backups use the configured Vancouver timezone and run through a background scheduler.
- Retention cleanup removes backups older than the configured `retention_days`.
- When a spawn is deleted, the app attempts to archive the latest backup into the root archived backups directory before purging the live server files.
- Archived backups can be restored into a new server. The app chooses a new name if needed and always assigns the next available port.

### Notes and operational caveats

- On startup, the app recreates loaded spawns once so their compose definitions use the correct absolute data paths.
- Player counts are only available when the Minecraft server responds to status queries.
- Updating `server.properties` triggers a restart flow.
- Restoring a backup replaces the target spawn's current `data` directory before restarting the container.

## License

This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request. \
Refer to the TODO section for ideas on how to contribute.

## TODO

- Admin/authentication interface to give people an account and a limit of how many servers they can spawn (through some kind of token system)
- Bukkit/Spigot support
- Fabric support
- Magma/Ketting/Mohist support
- Adding more parameters such as min and max of RAM and different versions of Java
- Nice UI for server properties that synch through the docker-compose instead of read/write the server.properties file
- Support for changing configuration files for mods
- Actual error handling
- Cluster/Server information on the home page
- Create dockerfile for project

## Contact

For any inquiries, please contact the author at `ftechhelp@gmail.com`.

## Acknowledgements

- [Bottle](https://bottlepy.org/docs/dev/) - A fast, simple and lightweight WSGI micro web-framework for Python.
- [Bulma CSS](https://bulma.io/) - A modern CSS framework based on Flexbox.
- [itzg's docker image](https://hub.docker.com/r/itzg/minecraft-server) - Docker image for running Minecraft servers.
- [python-on-whales](https://gabrieldemarmiesse.github.io/python-on-whales/) - A Python library for Docker.
