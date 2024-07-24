import uuid
from models.spawn import Spawn

class Spawner:
    
    def __init__(self):
        self.spawns: list = []

    def create_or_modify_spawn(self, name: str = str(uuid.uuid4()), new_port: int = 25565, new_volume: str = "./data", new_type: str = "FORGE", new_minecraftVersion: str = "LATEST", new_forgeVersion: str = "LATEST", mods: list = [], server_properties: list = []) -> None:
        spawn = Spawn(name, new_port, new_volume, new_type, new_minecraftVersion, new_forgeVersion, mods, server_properties)
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
            docker_compose['services']['mc']['environment'] += [f"CURSEFORGE_FILES={" ".join(spawn.mods)}"]

        spawn.set_docker_compose_contents(docker_compose)
        print("Docker Compose file updated successfully.")

        spawn.up()
        self.spawns.append(spawn)

    def purge_spawn(self, name: str):
        for spawn in self.spawns:
            if spawn.name == name:
                spawn.purge()
                self.spawns.remove(spawn)
                break
