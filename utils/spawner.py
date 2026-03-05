import uuid
from models.spawn import Spawn
import yaml
import os

class Spawner:
    
    def __init__(self):
        self.spawns: dict = {}
        self._startup_sentinel = "/app/tmp/startup_recreate_done"

    def spawn_name_exists(self, name: str) -> bool:
        return name in self.spawns

    def spawn_directory_exists(self, name: str) -> bool:
        spawn_folder = os.environ.get("SPAWNS_DIR", "./spawns")
        return os.path.isdir(os.path.join(spawn_folder, name))

    def create_or_modify_spawn(self, name: str = None, new_port: int = 25565, new_volume: str = "./data", new_type: str = "FORGE", new_minecraftVersion: str = "LATEST", new_forgeVersion: str = "LATEST") -> None:
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

        docker_compose['services']['mc']['environment'] = [f"TYPE={spawn.type}"]
        docker_compose['services']['mc']['environment'] += [f"VERSION={spawn.minecraft_version}"]
        docker_compose['services']['mc']['environment'] += [f"FORGE_VERSION={spawn.forge_version}"]
        docker_compose['services']['mc']['environment'] += ["EULA=TRUE"]
        docker_compose['services']['mc']['environment'] += ["INIT_MEMORY=2G"]
        docker_compose['services']['mc']['environment'] += ["MAX_MEMORY=16G"]

        spawn.set_docker_compose_contents(docker_compose)
        print("Docker Compose file updated successfully.")

        spawn.up()

        try:
            spawn.load_server_properties()
        except Exception as e:
            print(f"Warning: Could not load server properties for {spawn.name}: {str(e)}")
            print("This is normal for new servers and will be resolved when the server finishes starting.")
        
        self.spawns[spawn.name] = spawn
    
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
                        type = docker_compose['services']['mc']['environment'][0].split("=")[1]
                        minecraft_version = docker_compose['services']['mc']['environment'][1].split("=")[1]
                        forge_version = docker_compose['services']['mc']['environment'][2].split("=")[1]

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

    def recreate_all_spawns_once(self):
        try:
            os.makedirs(os.path.dirname(self._startup_sentinel), exist_ok=True)
            if os.path.exists(self._startup_sentinel):
                return
            # Ensure spawns are loaded
            if not self.spawns:
                self.loadSpawns()
            # Migrate and recreate all spawns
            for name, spawn in self.spawns.items():
                try:
                    print(f"Migrating and recreating spawn '{name}' at startup...")
                    # Regenerate docker-compose with absolute paths
                    self.create_or_modify_spawn(
                        name=spawn.name,
                        new_port=spawn.port,
                        new_type=spawn.type,
                        new_minecraftVersion=spawn.minecraft_version,
                        new_forgeVersion=spawn.forge_version
                    )
                except Exception as e:
                    print(f"Failed to recreate spawn '{name}': {str(e)}")
            # Mark done
            with open(self._startup_sentinel, 'w') as f:
                f.write('done')
        except Exception as e:
            print(f"Startup recreate step encountered an error: {str(e)}")