import uuid
from models.spawn import Spawn
import yaml
import os

class Spawner:
    
    def __init__(self):
        self.spawns: dict = {}

    def create_or_modify_spawn(self, name: str = str(uuid.uuid4()), new_port: int = 25565, new_volume: str = "./data", new_type: str = "FORGE", new_minecraftVersion: str = "LATEST", new_forgeVersion: str = "LATEST", mods: list = []) -> None:
        spawn = Spawn(name or str(uuid.uuid4()), new_port or 25565, new_volume or "./data", new_type or "FORGE", new_minecraftVersion or "LATEST", new_forgeVersion or "LATEST", mods or [])
        docker_compose = spawn.get_docker_compose_contents()

        if 'services' not in docker_compose:
            docker_compose['services'] = {}
        if 'mc' not in docker_compose['services']:
            docker_compose['services']['mc'] = {}

        docker_compose['services']['mc']['container_name'] = spawn.name
        docker_compose['services']['mc']['ports'] = [f"{spawn.port}:25565"]
        docker_compose['services']['mc']['volumes'] = [f"{spawn.volume}:/data"]
        docker_compose['services']['mc']['image'] = "itzg/minecraft-server"
        docker_compose['services']['mc']['stdin_open'] = True
        docker_compose['services']['mc']['tty'] = True

        docker_compose['services']['mc']['environment'] = [f"TYPE={spawn.type}"]
        docker_compose['services']['mc']['environment'] += [f"VERSION={spawn.minecraft_version}"]
        docker_compose['services']['mc']['environment'] += [f"FORGE_VERSION={spawn.forge_version}"]
        docker_compose['services']['mc']['environment'] += ["CF_API_KEY=${CF_API_KEY}"] # Make sure you have a .env file with the CF_API_KEY variable
        docker_compose['services']['mc']['environment'] += ["EULA=TRUE"]
        docker_compose['services']['mc']['environment'] += ["REMOVE_OLD_MODS=TRUE"]
        docker_compose['services']['mc']['environment'] += ["INIT_MEMORY=2G"]
        docker_compose['services']['mc']['environment'] += ["MAX_MEMORY=16G"]
        
        if (spawn.mods):
            # Format the mods list according to CurseForge documentation
            # Each mod should be a valid project slug, and they should be space-separated
            # Filter out any empty strings that might be in the list
            valid_mods = [mod for mod in spawn.mods if mod.strip()]
            if valid_mods:
                docker_compose['services']['mc']['environment'] += [f"CURSEFORGE_FILES={' '.join(valid_mods)}"]

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
        spawn_folder = "./spawns"
        spawn_names = os.listdir(spawn_folder)

        for name in spawn_names:
            spawn_path = os.path.join(spawn_folder, name)
            if os.path.isdir(spawn_path):
                docker_file = os.path.join(spawn_path, "docker-compose.yml")
                if os.path.isfile(docker_file):
                    with open(docker_file, "r") as f:
                        docker_compose = yaml.safe_load(f)
                        port = docker_compose['services']['mc']['ports'][0].split(":")[0]
                        volume = docker_compose['services']['mc']['volumes'][0].split(":")[0]
                        type = docker_compose['services']['mc']['environment'][0].split("=")[1]
                        minecraft_version = docker_compose['services']['mc']['environment'][1].split("=")[1]
                        forge_version = docker_compose['services']['mc']['environment'][2].split("=")[1]

                        mods = []
                        if 'CURSEFORGE_FILES' in [env.split('=')[0] for env in docker_compose['services']['mc']['environment']]:
                            for env in docker_compose['services']['mc']['environment']:
                                if env.startswith('CURSEFORGE_FILES'):
                                    mods = env.split('=')[1].split(' ')
                                    break
                        
                        spawn = Spawn(name, port, volume, type, minecraft_version, forge_version, mods)
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