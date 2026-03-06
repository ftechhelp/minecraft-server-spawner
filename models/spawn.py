import os
import yaml
from python_on_whales import docker, Container
import shutil
import tempfile
import zipfile
import socket
import struct
from bs4 import BeautifulSoup
import json

class Spawn:


    def __init__(self, name: str, port: int, volume: str, type: str, minecraft_version: str, forge_version: str) -> None:
        self.base_dir: str = os.environ.get("SPAWNS_DIR", "./spawns")
        self.name: str = name
        self.directory: str = os.path.join(self.base_dir, self.name)
        self.volume: str = volume
        self.port: int = port
        self.type: str = type
        self.minecraft_version: str = minecraft_version
        self.forge_version: str = forge_version
        self.server_properties: str = ""
        self.docker_compose_file: str = os.path.join(self.directory, "docker-compose.yml")
        self.mods_dir: str = os.path.join(self.directory, "data", "mods")
        self.pending_deletions_file: str = os.path.join(self.directory, ".pending_mod_deletions")
        self.backups_dir: str = os.path.join(self.directory, "backups")
        self.backup_settings_file: str = os.path.join(self.directory, ".backup_settings")
        self.backup_settings: dict = self.__load_backup_settings()
        self.pending_mod_deletions: list = self.__load_pending_deletions()

        self.__updateContainerInformation()
        self.__create_directory()


    def get_docker_compose_contents(self) -> dict:
        with open(self.docker_compose_file, 'w+') as file:
            docker_compose = yaml.safe_load(file) or {}

        return docker_compose
    
    def set_docker_compose_contents(self, docker_compose: dict) -> None:
        with open(self.docker_compose_file, 'w') as file:
            yaml.dump(docker_compose, file, default_flow_style=False)

    def up(self) -> None:
        os.chdir(self.directory)
        docker.compose.up(detach=True, force_recreate=True, recreate=True, attach_dependencies=False, build=True)
        print(f"Spawn {self.name} is up.")
        self.__updateContainerInformation()
        os.chdir("../..")
        # Clear pending deletions after successful restart
        self.clear_pending_deletions()

    def stop(self) -> None:
        os.chdir(self.directory)
        docker.compose.stop()
        print(f"Spawn {self.name} is stopped.")
        os.chdir("../..")

    def start(self) -> None:
        os.chdir(self.directory)
        docker.compose.start()
        print(f"Spawn {self.name} is started.")
        os.chdir("../..")

    def purge(self) -> None:
        os.chdir(self.directory)
        docker.compose.down(remove_images="all", volumes=True, remove_orphans=True)
        print(f"Spawn {self.name} down.")
        os.chdir("../..")

        if os.path.exists(self.directory):
            shutil.rmtree(self.directory)
            print(f"Spawn {self.name} directory purged.")
        else:
            print(f"No such spawn directory exists for {self.name}.")

    def archive_latest_backup(self, archive_dir: str) -> tuple:
        """Copy latest backup to archive dir with metadata. Returns (success, message, archive_filename)."""
        try:
            latest_backup = self._get_latest_backup_path()
            if not latest_backup:
                return False, "No backups found to archive", None

            os.makedirs(archive_dir, exist_ok=True)

            source_filename = os.path.basename(latest_backup)
            archive_filename = f"{self.name}__{source_filename}"
            archive_path = os.path.join(archive_dir, archive_filename)

            counter = 1
            while os.path.exists(archive_path):
                archive_filename = f"{self.name}__{counter}__{source_filename}"
                archive_path = os.path.join(archive_dir, archive_filename)
                counter += 1

            shutil.copy2(latest_backup, archive_path)

            metadata = {
                "source_server": self.name,
                "source_backup_file": source_filename,
                "minecraft_version": self.minecraft_version,
                "forge_version": self.forge_version,
                "server_type": self.type,
                "archived_backup_file": archive_filename,
            }

            metadata_path = f"{archive_path}.json"
            with open(metadata_path, "w") as meta_file:
                json.dump(metadata, meta_file, indent=2)

            return True, f"Archived latest backup to {archive_filename}", archive_filename
        except Exception as e:
            print(f"Error archiving latest backup for {self.name}: {str(e)}")
            return False, f"Error: {str(e)}", None

    def get_status(self) -> str:
        if self.container == None:
            return "N/A"
        
        status = self.container.state.status
        return status

    def get_player_count(self):
        server_status = self.get_server_status()
        if not server_status:
            return None

        players = server_status.get("players")
        if not isinstance(players, dict):
            return None

        online = players.get("online")
        if isinstance(online, int):
            return online

        return None

    def get_player_capacity(self):
        server_status = self.get_server_status()
        if not server_status:
            return None

        players = server_status.get("players")
        if not isinstance(players, dict):
            return None

        maximum = players.get("max")
        if isinstance(maximum, int):
            return maximum

        return None

    def get_server_status(self):
        if self.get_status() != "running":
            return None

        try:
            port = int(self.port)
        except (TypeError, ValueError):
            return None

        for host in self.__get_status_hosts():
            try:
                return self.__query_minecraft_status(host, port)
            except Exception:
                continue

        return None

    def _get_latest_backup_path(self) -> str:
        if not os.path.isdir(self.backups_dir):
            return ""

        backup_paths = []
        for filename in os.listdir(self.backups_dir):
            if filename.endswith('.tar.gz'):
                backup_paths.append(os.path.join(self.backups_dir, filename))

        if not backup_paths:
            return ""

        return max(backup_paths, key=os.path.getmtime)
    
    def get_logs(self) -> str:
        self.__updateLogs()
        return self.logs
    
    def refreshContainerInformation(self) -> None:
        self.__updateContainerInformation()
        # Ensure mods directory exists and can be read
        os.makedirs(self.mods_dir, exist_ok=True)

    # --- Backup management ---
    def create_backup(self, backup_name: str = None, is_scheduled: bool = False) -> tuple:
        """Create a backup of entire spawn directory (world, mods, configs, etc).

        Returns (success, message, backup_filename).
        is_scheduled controls naming and retention rules so we can distinguish daily vs manual backups.
        """
        try:
            import tarfile
            from datetime import datetime
            from zoneinfo import ZoneInfo
            
            os.makedirs(self.backups_dir, exist_ok=True)
            
            tz = ZoneInfo("America/Vancouver")
            if not backup_name:
                # Use Vancouver timezone for timestamps and prefix to indicate source
                now_local = datetime.now(tz=tz)
                prefix = "daily" if is_scheduled else "manual"
                backup_name = f"{prefix}_{now_local.strftime('%Y%m%d_%H%M%S')}"
            
            # Ensure backup name doesn't have extension (we'll add .tar.gz)
            backup_name = backup_name.replace('.tar.gz', '').replace('.tar', '')
            backup_path = os.path.join(self.backups_dir, f"{backup_name}.tar.gz")
            
            # Create tar.gz of entire spawn directory (excluding backups to avoid recursive backup)
            parent_dir = os.path.dirname(self.directory)
            spawn_dirname = os.path.basename(self.directory)
            
            with tarfile.open(backup_path, "w:gz") as tar:
                # Add all files except backups directory
                for root, dirs, files in os.walk(self.directory):
                    # Skip backups directory itself
                    dirs[:] = [d for d in dirs if d != 'backups']
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, self.directory)
                        tar.add(file_path, arcname=arcname)
            
            # Update last backup timestamp with Vancouver timezone
            now_local = datetime.now(tz=tz)
            self.backup_settings['last_backup_timestamp'] = now_local.strftime('%Y-%m-%d %H:%M:%S')
            self.__save_backup_settings()
            
            # Cleanup old backups based on retention days
            self.cleanup_old_backups()
            
            size_mb = os.path.getsize(backup_path) / (1024 * 1024)
            print(f"Backup created for {self.name}: {backup_name}.tar.gz ({size_mb:.2f} MB)")
            return True, f"Backup created successfully ({size_mb:.2f} MB)", f"{backup_name}.tar.gz"
        except Exception as e:
            print(f"Error creating backup for {self.name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, f"Error: {str(e)}", None
    
    def list_backups(self) -> list:
        """List all backups with metadata. Returns list of dicts with name, timestamp, size, type"""
        try:
            if not os.path.exists(self.backups_dir):
                return []
            
            backups = []
            for filename in sorted(os.listdir(self.backups_dir), reverse=True):
                if filename.endswith('.tar.gz'):
                    filepath = os.path.join(self.backups_dir, filename)
                    size_mb = os.path.getsize(filepath) / (1024 * 1024)
                    mtime = os.path.getmtime(filepath)
                    from datetime import datetime
                    from zoneinfo import ZoneInfo
                    tz = ZoneInfo("America/Vancouver")
                    timestamp = datetime.fromtimestamp(mtime, tz=tz).strftime('%Y-%m-%d %H:%M:%S')

                    backup_type = "Daily" if filename.startswith("daily_") else "Manual"
                    
                    backups.append({
                        'name': filename,
                        'timestamp': timestamp,
                        'size_mb': f"{size_mb:.2f}",
                        'type': backup_type
                    })
            return backups
        except Exception as e:
            print(f"Error listing backups for {self.name}: {str(e)}")
            return []
    
    def restore_backup(self, backup_filename: str) -> tuple:
        """Restore from backup. Returns (success, message)"""
        try:
            import tarfile
            import time
            
            backup_path = os.path.join(self.backups_dir, backup_filename)
            if not os.path.exists(backup_path):
                return False, "Backup file not found"
            
            # Stop server before restore
            self.stop()
            
            # Remove existing data
            data_dir = os.path.join(self.directory, "data")
            if os.path.exists(data_dir):
                import shutil
                shutil.rmtree(data_dir)
            
            # Extract backup
            os.makedirs(self.directory, exist_ok=True)
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(path=self.directory)

            # Ensure restored backup does not override this spawn's runtime identity
            # (container name, port, and versions for the currently selected spawn).
            self._sync_docker_compose_with_spawn_settings()
            
            # Restart server
            self.up()

            # Validate startup and provide useful diagnostics when startup fails.
            status = "N/A"
            for _ in range(6):
                self.refreshContainerInformation()
                status = self.get_status()
                if status in {"running", "restarting", "created"}:
                    print(f"Restored backup for {self.name}: {backup_filename}")
                    return True, f"Backup restored successfully. Server status: {status}."
                if status in {"exited", "dead"}:
                    break
                time.sleep(1)

            recent_logs = "No logs available."
            try:
                logs = self.get_logs() or ""
                tail_lines = logs.splitlines()[-20:]
                if tail_lines:
                    recent_logs = "\n".join(tail_lines)
            except Exception:
                pass

            return False, f"Backup restored but server did not start (status: {status}). Recent logs:\n{recent_logs}"
        except Exception as e:
            print(f"Error restoring backup for {self.name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, f"Error: {str(e)}"

    def _sync_docker_compose_with_spawn_settings(self) -> None:
        """Keep docker-compose aligned with this spawn's identity after backup extraction."""
        docker_compose = {}
        if os.path.exists(self.docker_compose_file):
            try:
                with open(self.docker_compose_file, "r") as compose_file:
                    docker_compose = yaml.safe_load(compose_file) or {}
            except Exception:
                docker_compose = {}

        if 'services' not in docker_compose:
            docker_compose['services'] = {}
        if 'mc' not in docker_compose['services']:
            docker_compose['services']['mc'] = {}

        data_volume_path = os.path.join(self.directory, "data")

        docker_compose['services']['mc']['container_name'] = self.name
        docker_compose['services']['mc']['ports'] = [f"{self.port}:25565"]
        docker_compose['services']['mc']['volumes'] = [f"{data_volume_path}:/data"]
        docker_compose['services']['mc']['image'] = "itzg/minecraft-server"
        docker_compose['services']['mc']['stdin_open'] = True
        docker_compose['services']['mc']['tty'] = True
        docker_compose['services']['mc']['environment'] = [
            f"TYPE={self.type}",
            f"VERSION={self.minecraft_version}",
            f"FORGE_VERSION={self.forge_version}",
            "EULA=TRUE",
            "INIT_MEMORY=2G",
            "MAX_MEMORY=16G",
        ]

        with open(self.docker_compose_file, 'w') as file:
            yaml.dump(docker_compose, file, default_flow_style=False)
    
    def delete_backup(self, backup_filename: str) -> tuple:
        """Delete a backup. Returns (success, message)"""
        try:
            backup_path = os.path.join(self.backups_dir, backup_filename)
            if not os.path.exists(backup_path):
                return False, "Backup file not found"
            
            os.remove(backup_path)
            print(f"Deleted backup for {self.name}: {backup_filename}")
            return True, f"Backup deleted successfully"
        except Exception as e:
            print(f"Error deleting backup for {self.name}: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def cleanup_old_backups(self) -> None:
        """Delete old backups based on retention_days setting"""
        try:
            from datetime import datetime, timedelta
            import time
            
            if not os.path.exists(self.backups_dir):
                return
            
            retention_days = self.backup_settings.get('retention_days', 7)
            cutoff_time = time.time() - (retention_days * 86400)  # 86400 seconds in a day
            
            for filename in os.listdir(self.backups_dir):
                if filename.endswith('.tar.gz'):
                    filepath = os.path.join(self.backups_dir, filename)
                    if os.path.getmtime(filepath) < cutoff_time:
                        try:
                            os.remove(filepath)
                            print(f"Cleaned up old backup: {filename} (older than {retention_days} days)")
                        except Exception as e:
                            print(f"Error cleaning up backup {filename}: {str(e)}")
        except Exception as e:
            print(f"Error during backup cleanup for {self.name}: {str(e)}")

    def load_server_properties(self) -> None:
        try:
            with open(f"{self.directory}/data/server.properties", 'r') as file:
                self.server_properties = file.read()
        except FileNotFoundError:
            # File doesn't exist yet, which can happen when the container is first created
            # Set default empty properties or wait until file is created
            self.server_properties = ""
            print(f"Warning: server.properties file not found for {self.name}. This is normal for new servers.")

    def write_server_properties(self, server_properties) -> None:
        try:
            # Make sure the data directory exists
            os.makedirs(f"{self.directory}/data", exist_ok=True)
            
            with open(f"{self.directory}/data/server.properties", 'w') as file:
                file.write(server_properties)
                self.server_properties = server_properties
        except Exception as e:
            print(f"Error writing server.properties for {self.name}: {str(e)}")
        
        self.up()

    def send_console_command(self, command: str) -> None:
        docker.execute(container=self.name, command=["rcon-cli", command])
        self.__updateLogs(20)

    def __create_directory(self) -> None:
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        # Ensure data/mods directory exists
        os.makedirs(self.mods_dir, exist_ok=True)

    def __get_status_hosts(self) -> list:
        hosts = ["127.0.0.1", "localhost", "host.docker.internal", self.name]
        unique_hosts = []

        for host in hosts:
            if host and host not in unique_hosts:
                unique_hosts.append(host)

        return unique_hosts

    def __query_minecraft_status(self, host: str, port: int) -> dict:
        address = host.encode("utf-8")
        handshake_payload = b"".join([
            self.__pack_varint(0),
            self.__pack_varint(754),
            self.__pack_varint(len(address)),
            address,
            struct.pack(">H", port),
            self.__pack_varint(1),
        ])

        with socket.create_connection((host, port), timeout=1.5) as sock:
            sock.sendall(self.__pack_varint(len(handshake_payload)) + handshake_payload)
            sock.sendall(self.__pack_varint(1) + self.__pack_varint(0))

            self.__read_varint(sock)
            packet_id = self.__read_varint(sock)
            if packet_id != 0:
                raise ValueError("Unexpected Minecraft status packet")

            payload_length = self.__read_varint(sock)
            payload = self.__recv_exact(sock, payload_length)
            return json.loads(payload.decode("utf-8"))

    def __pack_varint(self, value: int) -> bytes:
        data = bytearray()

        while True:
            current_byte = value & 0x7F
            value >>= 7
            if value:
                current_byte |= 0x80
            data.append(current_byte)
            if not value:
                break

        return bytes(data)

    def __read_varint(self, sock) -> int:
        result = 0
        shift = 0

        while True:
            raw_byte = sock.recv(1)
            if not raw_byte:
                raise ConnectionError("Connection closed while reading Minecraft status")

            current_byte = raw_byte[0]
            result |= (current_byte & 0x7F) << shift

            if not (current_byte & 0x80):
                return result

            shift += 7
            if shift >= 35:
                raise ValueError("Minecraft status varint is too large")

    def __recv_exact(self, sock, size: int) -> bytes:
        chunks = bytearray()

        while len(chunks) < size:
            chunk = sock.recv(size - len(chunks))
            if not chunk:
                raise ConnectionError("Connection closed while reading Minecraft status payload")
            chunks.extend(chunk)

        return bytes(chunks)

    def __updateContainerInformation(self) -> None:
        try:
            self.container: Container = docker.container.inspect(self.name)
        except:
            self.container = None
        
        self.__updateLogs(20)

    def __updateLogs(self, tail: int = None) -> None:
        try:
            raw_logs = self.container.logs(tail=tail, timestamps=True)
            if isinstance(raw_logs, bytes):
                raw_logs = raw_logs.decode('utf-8')
            
            # Convert UTC timestamps to Vancouver time
            from datetime import datetime
            from zoneinfo import ZoneInfo
            import re
            
            tz = ZoneInfo("America/Vancouver")
            lines = raw_logs.split('\n')
            converted_lines = []
            
            for line in lines:
                # Docker timestamp format: 2025-12-30T22:38:30.197177550Z [22:38:30]
                # Match ISO8601 timestamp at start of line
                match = re.match(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+(.*)$', line)
                if match:
                    utc_time_str = match.group(1)
                    rest_of_line = match.group(2)
                    
                    # Parse UTC time and convert to Vancouver time
                    utc_time = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))
                    local_time = utc_time.astimezone(tz)
                    local_time_str = local_time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    converted_lines.append(f"{local_time_str} {rest_of_line}")
                else:
                    converted_lines.append(line)
            
            self.logs = '\n'.join(converted_lines)
        except:
            self.logs = "No logs available."

    def __load_backup_settings(self) -> dict:
        """Load backup settings from file"""
        default_settings = {
            'daily_backup_enabled': True,
            'daily_backup_hour': 2,  # 2 AM
            'daily_backup_minute': 0,
            'retention_days': 3,
            'last_backup_timestamp': None
        }
        try:
            if os.path.exists(self.backup_settings_file):
                import json
                with open(self.backup_settings_file, 'r') as f:
                    settings = json.load(f)
                    return {**default_settings, **settings}
        except Exception as e:
            print(f"Error loading backup settings for {self.name}: {str(e)}")
        return default_settings

    def reload_backup_settings(self) -> None:
        """Reload backup settings from file into memory"""
        self.backup_settings = self.__load_backup_settings()

    def __save_backup_settings(self) -> None:
        """Save backup settings to file"""
        try:
            import json
            os.makedirs(os.path.dirname(self.backup_settings_file), exist_ok=True)
            with open(self.backup_settings_file, 'w') as f:
                json.dump(self.backup_settings, f, indent=2)
        except Exception as e:
            print(f"Error saving backup settings for {self.name}: {str(e)}")

    def update_backup_settings(self, daily_enabled: bool = None, hour: int = None, minute: int = None, retention_days: int = None) -> tuple:
        """Update backup settings. Returns (success, message)"""
        try:
            if daily_enabled is not None:
                self.backup_settings['daily_backup_enabled'] = daily_enabled
            if hour is not None and 0 <= hour <= 23:
                self.backup_settings['daily_backup_hour'] = hour
            if minute is not None and 0 <= minute <= 59:
                self.backup_settings['daily_backup_minute'] = minute
            if retention_days is not None and retention_days > 0:
                self.backup_settings['retention_days'] = retention_days
            
            self.__save_backup_settings()
            return True, "Backup settings updated successfully"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def __load_pending_deletions(self) -> list:
        """Load pending mod deletions from file"""
        try:
            if os.path.exists(self.pending_deletions_file):
                with open(self.pending_deletions_file, 'r') as f:
                    return [line.strip() for line in f.readlines() if line.strip()]
        except Exception:
            pass
        return []

    def __save_pending_deletions(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.pending_deletions_file), exist_ok=True)
            with open(self.pending_deletions_file, 'w') as f:
                for mod in self.pending_mod_deletions:
                    f.write(f"{mod}\n")
        except Exception as e:
            print(f"Error saving pending deletions for {self.name}: {str(e)}")

    def clear_pending_deletions(self) -> None:
        """Clear pending deletions list after restart"""
        self.pending_mod_deletions = []
        try:
            if os.path.exists(self.pending_deletions_file):
                os.remove(self.pending_deletions_file)
        except Exception:
            pass

    # --- Mods management based on filesystem ---
    def list_mods(self) -> list:
        try:
            if not os.path.exists(self.mods_dir):
                return []
            return sorted([f for f in os.listdir(self.mods_dir) if os.path.isfile(os.path.join(self.mods_dir, f))])
        except Exception:
            return []

    def replace_mods_from_uploads(self, files: list) -> None:
        try:
            print(f"[replace_mods_from_uploads] Received {len(files) if files else 0} files for {self.name}")
            os.makedirs(self.mods_dir, exist_ok=True)
            
            # Remove current mods
            removed_count = 0
            for f in os.listdir(self.mods_dir):
                fp = os.path.join(self.mods_dir, f)
                if os.path.isfile(fp):
                    os.remove(fp)
                    removed_count += 1
            print(f"[replace_mods_from_uploads] Removed {removed_count} existing mods")
            
            # Save uploaded mods
            saved_count = 0
            for upload in files or []:
                filename = os.path.basename(upload.filename)
                print(f"[replace_mods_from_uploads] Processing file: {filename}")
                if not filename:
                    continue
                # Only accept jar files for mods
                if not filename.lower().endswith(".jar"):
                    print(f"[replace_mods_from_uploads] Skipping non-jar file: {filename}")
                    continue
                dest = os.path.join(self.mods_dir, filename)
                upload.save(dest, overwrite=True)
                saved_count += 1
                print(f"[replace_mods_from_uploads] Saved: {filename}")
            
            print(f"[replace_mods_from_uploads] Saved {saved_count} mods, restarting server...")
            # Restart to apply changes
            self.up()
        except Exception as e:
            print(f"Error replacing mods for {self.name}: {str(e)}")
            import traceback
            traceback.print_exc()

    def add_mod_file(self, file_upload) -> None:
        try:
            os.makedirs(self.mods_dir, exist_ok=True)
            filename = os.path.basename(file_upload.filename)
            if not filename:
                return
            if not filename.lower().endswith(".jar"):
                return
            dest = os.path.join(self.mods_dir, filename)
            file_upload.save(dest, overwrite=True)
            self.up()
        except Exception as e:
            print(f"Error adding mod for {self.name}: {str(e)}")

    def remove_mod_file(self, filename: str) -> None:
        try:
            fp = os.path.join(self.mods_dir, filename)
            if os.path.exists(fp) and os.path.isfile(fp):
                os.remove(fp)
                # Track pending deletion without restarting
                if filename not in self.pending_mod_deletions:
                    self.pending_mod_deletions.append(filename)
                    self.__save_pending_deletions()
                print(f"Deleted mod {filename} for {self.name} (restart required)")
        except Exception as e:
            print(f"Error removing mod {filename} for {self.name}: {str(e)}")