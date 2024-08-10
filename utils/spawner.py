import uuid
from models.spawn import Spawn
import yaml
import os

class Spawner:
    
    def __init__(self):
        self.spawns: dict = {}

    def create_or_modify_spawn(self, name: str = str(uuid.uuid4()), new_port: int = 25565, new_volume: str = "./data", new_type: str = "FORGE", new_minecraftVersion: str = "LATEST", new_forgeVersion: str = "LATEST", mods: list = [], server_properties: dict = {}) -> None:
        spawn = Spawn(name or str(uuid.uuid4()), new_port or 25565, new_volume or "./data", new_type or "FORGE", new_minecraftVersion or "LATEST", new_forgeVersion or "LATEST", mods or [], server_properties or {})
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
        docker_compose['services']['mc']['environment'] += ["INIT_MEMORY=1G"]
        docker_compose['services']['mc']['environment'] += ["MAX_MEMORY=4G"]

        for property in spawn.server_properties:
            docker_compose['services']['mc']['environment'] += [f"{property}"]
        
        if (spawn.mods):
            docker_compose['services']['mc']['environment'] += [f"CURSEFORGE_FILES={" ".join(spawn.mods or [])}"]

        spawn.set_docker_compose_contents(docker_compose)
        print("Docker Compose file updated successfully.")

        spawn.up()
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
                        
                        server_properties = self.__loadServerPropertiesFromDockerCompose(docker_compose, name)
                        
                        spawn = Spawn(name, port, volume, type, minecraft_version, forge_version, mods, server_properties)
                        self.spawns[spawn.name] = spawn
                        print(f"Spawn '{name}' loaded successfully.")
                else:
                    print(f"No docker-compose.yml file found in '{spawn_path}'. Skipping spawn.")
            else:
                print(f"'{spawn_path}' is not a directory. Skipping spawn.")

    def __loadServerPropertiesFromDockerCompose(self, docker_compose: dict, spawnName: str) -> dict:
        server_properties = {
            "MOTD": f"Welcome to {spawnName} the server!",
            "DIFFICULTY": "easy",
            "MAX_PLAYERS": 20,
            "MAX_WORLD_SIZE": None,
            "ALLOW_NETHER": True,
            "ANNOUCE_PLAYER_ACHIEVEMENTS": True,
            "ENABLE_COMMAND_BLOCK": None,
            "FORCE_GAMEMODE": False,
            "GENERATE_STRUCTURES": True,
            "HARDCORE": False,
            "SNOOPER_ENABLED": True,
            "MAX_BUILD_HEIGHT": 256,
            "SPAWN_ANIMALS": True,
            "SPAWN_MONSTERS": True,
            "SPAWN_NPCS": True,
            "VIEW_DISTANCE": None,
            "SEED": None,
            "MODE": None,
            "PVP": True,
            "LEVEL_TYPE": "minecraft:normal",
            "LEVEL": "world",
            "ONLINE_MODE": True,
            "ALLOW_FLIGHT": False,
            "SERVER_NAME": spawnName,
            "PLAYER_IDLE_TIMEOUT": 0
        }

        for key in server_properties:
            if key in [env.split('=')[0] for env in docker_compose['services']['mc']['environment']]:
                for env in docker_compose['services']['mc']['environment']:
                    if env.startswith(key):
                        server_properties[key] = env.split('=')[1]
                        break
        return server_properties