import uuid
from models.spawn import Spawn
import yaml
import os
import json
import shutil
from datetime import datetime
from zoneinfo import ZoneInfo

class Spawner:
    
    def __init__(self):
        self.spawns: dict = {}
        self.archived_backups_dir = os.environ.get("ARCHIVED_BACKUPS_DIR", "./backups")

    def spawn_name_exists(self, name: str) -> bool:
        return name in self.spawns

    def spawn_directory_exists(self, name: str) -> bool:
        spawn_folder = os.environ.get("SPAWNS_DIR", "./spawns")
        return os.path.isdir(os.path.join(spawn_folder, name))

    def create_or_modify_spawn(self, name: str = None, new_port: int = 25565, new_volume: str = "./data", new_type: str = "FORGE", new_minecraftVersion: str = "LATEST", new_forgeVersion: str = "LATEST", force_recreate: bool = True) -> Spawn:
        spawn_name = name or str(uuid.uuid4())
        spawn = Spawn(spawn_name, new_port or 25565, new_volume or "./data", new_type or "FORGE", new_minecraftVersion or "LATEST", new_forgeVersion or "LATEST")
        docker_compose = spawn.get_docker_compose_contents()

        if 'services' not in docker_compose:
            docker_compose['services'] = {}
        if 'mc' not in docker_compose['services']:
            docker_compose['services']['mc'] = {}

        # Use absolute path for volume so Docker-in-Docker can access it
        data_volume_path = os.path.join(spawn.directory, "data")
        
        docker_compose['services']['mc']['container_name'] = spawn.name
        docker_compose['services']['mc']['ports'] = [f"{spawn.port}:25565"]
        docker_compose['services']['mc']['volumes'] = [f"{data_volume_path}:/data"]
        docker_compose['services']['mc']['image'] = "itzg/minecraft-server"
        docker_compose['services']['mc']['stdin_open'] = True
        docker_compose['services']['mc']['tty'] = True

        version_env_key = "NEOFORGE_VERSION" if spawn.type == "NEOFORGE" else "FORGE_VERSION"
        docker_compose['services']['mc']['environment'] = [f"TYPE={spawn.type}"]
        docker_compose['services']['mc']['environment'] += [f"VERSION={spawn.minecraft_version}"]
        docker_compose['services']['mc']['environment'] += [f"{version_env_key}={spawn.forge_version}"]
        docker_compose['services']['mc']['environment'] += ["EULA=TRUE"]
        docker_compose['services']['mc']['environment'] += ["INIT_MEMORY=2G"]
        docker_compose['services']['mc']['environment'] += ["MAX_MEMORY=16G"]

        spawn.set_docker_compose_contents(docker_compose)
        print("Docker Compose file updated successfully.")

        spawn.up(force_recreate=force_recreate)

        try:
            spawn.load_server_properties()
        except Exception as e:
            print(f"Warning: Could not load server properties for {spawn.name}: {str(e)}")
            print("This is normal for new servers and will be resolved when the server finishes starting.")
        
        self.spawns[spawn.name] = spawn
        return spawn

    def _find_next_available_port(self, start_port: int = 25565, end_port: int = 25665):
        used_ports = set()
        for spawn in self.spawns.values():
            try:
                used_ports.add(int(spawn.port))
            except (TypeError, ValueError):
                continue

        for port in range(start_port, end_port + 1):
            if port not in used_ports:
                return port

        return None

    def list_archived_backups(self) -> list:
        os.makedirs(self.archived_backups_dir, exist_ok=True)
        backups = []
        tz = ZoneInfo("America/Vancouver")

        for filename in sorted(os.listdir(self.archived_backups_dir), reverse=True):
            if not filename.endswith('.tar.gz'):
                continue

            backup_path = os.path.join(self.archived_backups_dir, filename)
            metadata_path = f"{backup_path}.json"
            metadata = {}
            if os.path.isfile(metadata_path):
                try:
                    with open(metadata_path, "r") as meta_file:
                        metadata = json.load(meta_file)
                except Exception:
                    metadata = {}

            size_mb = os.path.getsize(backup_path) / (1024 * 1024)
            timestamp = datetime.fromtimestamp(os.path.getmtime(backup_path), tz=tz).strftime('%Y-%m-%d %H:%M:%S')

            backups.append({
                "file": filename,
                "timestamp": timestamp,
                "size_mb": f"{size_mb:.2f}",
                "source_server": metadata.get("source_server", "Unknown"),
                "server_type": metadata.get("server_type", "FORGE"),
                "minecraft_version": metadata.get("minecraft_version", "LATEST"),
                "forge_version": metadata.get("forge_version", "LATEST"),
            })

        return backups

    def delete_archived_backup(self, archive_filename: str) -> tuple:
        safe_name = os.path.basename(archive_filename)
        backup_path = os.path.join(self.archived_backups_dir, safe_name)
        metadata_path = f"{backup_path}.json"

        if not os.path.isfile(backup_path):
            return False, "Archived backup not found"

        try:
            os.remove(backup_path)
            if os.path.isfile(metadata_path):
                os.remove(metadata_path)
            return True, "Archived backup deleted"
        except Exception as e:
            return False, f"Failed to delete archived backup: {str(e)}"

    def restore_archived_backup(self, archive_filename: str, restored_name: str = None, owner=None) -> tuple:
        safe_name = os.path.basename(archive_filename)
        archive_path = os.path.join(self.archived_backups_dir, safe_name)
        metadata_path = f"{archive_path}.json"

        if not os.path.isfile(archive_path):
            return False, "Archived backup not found", None

        metadata = {}
        if os.path.isfile(metadata_path):
            try:
                with open(metadata_path, "r") as meta_file:
                    metadata = json.load(meta_file)
            except Exception:
                metadata = {}

        source_server = metadata.get("source_server", "restored-server")
        base_name = (restored_name or f"{source_server}-restored").strip() or f"{source_server}-restored"

        candidate_name = base_name
        suffix = 1
        while self.spawn_name_exists(candidate_name) or self.spawn_directory_exists(candidate_name):
            suffix += 1
            candidate_name = f"{base_name}-{suffix}"

        restore_port = self._find_next_available_port()
        if restore_port is None:
            return False, "No available ports left in the allowed range (25565-25665)", None

        server_type = metadata.get("server_type", "FORGE")
        minecraft_version = metadata.get("minecraft_version", "LATEST")
        forge_version = metadata.get("forge_version", "LATEST")

        try:
            self.create_or_modify_spawn(
                name=candidate_name,
                new_port=restore_port,
                new_type=server_type,
                new_minecraftVersion=minecraft_version,
                new_forgeVersion=forge_version,
            )

            restored_spawn = self.spawns[candidate_name]
            restored_spawn.set_owner(owner)
            os.makedirs(restored_spawn.backups_dir, exist_ok=True)

            copied_backup_name = f"archived_restore_{safe_name}"
            copied_backup_path = os.path.join(restored_spawn.backups_dir, copied_backup_name)
            copy_suffix = 1
            while os.path.exists(copied_backup_path):
                copied_backup_name = f"archived_restore_{copy_suffix}_{safe_name}"
                copied_backup_path = os.path.join(restored_spawn.backups_dir, copied_backup_name)
                copy_suffix += 1

            shutil.copy2(archive_path, copied_backup_path)
            restore_success, restore_message = restored_spawn.restore_backup(copied_backup_name)
            if not restore_success:
                try:
                    restored_spawn.purge()
                except Exception:
                    pass
                self.spawns.pop(candidate_name, None)
                return False, restore_message, None

            return True, f"Archived backup restored into new server '{candidate_name}'", candidate_name
        except Exception as e:
            return False, f"Failed to restore archived backup: {str(e)}", None
    
    def loadSpawns(self):
        self.spawns = {}
        spawn_folder = os.environ.get("SPAWNS_DIR", "./spawns")
        os.makedirs(spawn_folder, exist_ok=True)  # Ensure the spawn directory exists to avoid startup failures
        spawn_names = os.listdir(spawn_folder)

        for name in spawn_names:
            spawn_path = os.path.join(spawn_folder, name)
            if os.path.isdir(spawn_path):
                docker_file = os.path.join(spawn_path, "docker-compose.yml")
                if os.path.isfile(docker_file):
                    with open(docker_file, "r") as f:
                        docker_compose = yaml.safe_load(f)
                        port = docker_compose['services']['mc']['ports'][0].split(":")[0]
                        volume_raw = docker_compose['services']['mc']['volumes'][0].split(":")[0]
                        # For display purposes, keep it simple
                        volume = "./data" if volume_raw.endswith("/data") else volume_raw
                        env_vars = {}
                        for env_entry in docker_compose['services']['mc']['environment']:
                            key, _, value = env_entry.partition("=")
                            env_vars[key] = value
                        type = env_vars.get("TYPE", "FORGE")
                        minecraft_version = env_vars.get("VERSION", "LATEST")
                        forge_version = env_vars.get("FORGE_VERSION") or env_vars.get("NEOFORGE_VERSION", "LATEST")

                        spawn = Spawn(name, port, volume, type, minecraft_version, forge_version)
                        self.spawns[spawn.name] = spawn

                        try:
                            spawn.load_server_properties()
                            print(f"Spawn '{name}' loaded successfully.")
                        except Exception as e:
                            print(f"Failed to load server properties for spawn '{name}': {str(e)}")
                else:
                    print(f"No docker-compose.yml file found in '{spawn_path}'. Skipping spawn.")
            else:
                print(f"'{spawn_path}' is not a directory. Skipping spawn.")
