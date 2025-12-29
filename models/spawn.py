import os
import yaml
from python_on_whales import docker, Container
import shutil
import tempfile
import zipfile
import os
from bs4 import BeautifulSoup

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

    def get_status(self) -> str:
        if self.container == None:
            return "N/A"
        
        status = self.container.state.status
        return status
    
    def get_logs(self) -> str:
        self.__updateLogs()
        return self.logs
    
    def refreshContainerInformation(self) -> None:
        self.__updateContainerInformation()
        # Ensure mods directory exists and can be read
        os.makedirs(self.mods_dir, exist_ok=True)

    # Removed old CurseForge/slug-based mod management; using filesystem now

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

    def __updateContainerInformation(self) -> None:
        try:
            self.container: Container = docker.container.inspect(self.name)
        except:
            self.container = None
        
        self.__updateLogs(20)

    def __updateLogs(self, tail: int = None) -> None:
        try:
            self.logs = self.container.logs(tail=tail, timestamps=True)
        except:
            self.logs = "No logs available."

    def __load_pending_deletions(self) -> list:
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