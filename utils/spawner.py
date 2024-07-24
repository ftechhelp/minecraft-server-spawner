import yaml
from python_on_whales import docker
import uuid
import os
import shutil

class Spawner:
    
    def __init__(self, file_name):
        self.file_name = file_name

    def create_or_modify_spawn(self, name: str = None, new_port: int = None, new_volume: str = None, new_type: str = None, new_minecraftVersion: str = None, new_forgeVersion: str = None, mods: list = None, server_properties: list = None):
        
        spawn_name = name or str(uuid.uuid4())
        spawn_directory = f"./spawns/{spawn_name}"
        docker_compose_file_path = f"{spawn_directory}/{self.file_name}"

        if not os.path.exists(spawn_directory):
            os.makedirs(spawn_directory)

        with open(docker_compose_file_path, 'w+') as file:
            docker_compose = yaml.safe_load(file) or {}

        if 'services' not in docker_compose:
            docker_compose['services'] = {}
        if 'mc' not in docker_compose['services']:
            docker_compose['services']['mc'] = {}

        docker_compose['services']['mc']['container_name'] = spawn_name
        docker_compose['services']['mc']['ports'] = [f"{new_port or 25565}:25565"]
        docker_compose['services']['mc']['volumes'] = [f"{new_volume or f"./data"}:/data"]
        docker_compose['services']['mc']['image'] = "itzg/minecraft-server"
        docker_compose['services']['mc']['stdin_open'] = True
        docker_compose['services']['mc']['tty'] = True

        docker_compose['services']['mc']['environment'] = [f"TYPE={new_type or "FORGE"}"]
        docker_compose['services']['mc']['environment'] += [f"VERSION={new_minecraftVersion or "LATEST"}"]
        docker_compose['services']['mc']['environment'] += [f"FORGE_VERSION={new_forgeVersion or "LATEST"}"]
        docker_compose['services']['mc']['environment'] += ["CF_API_KEY=${CF_API_KEY}"] # Make sure you have a .env file with the CF_API_KEY variable
        docker_compose['services']['mc']['environment'] += ["EULA=TRUE"]
        docker_compose['services']['mc']['environment'] += ["REMOVE_OLD_MODS=TRUE"]
        docker_compose['services']['mc']['environment'] += ["INIT_MEMORY=1G"]
        docker_compose['services']['mc']['environment'] += ["MAX_MEMORY=4G"]

        for property in server_properties or []:
            docker_compose['services']['mc']['environment'] += [f"{property}"]
        
        mods_list = mods or []
        if (mods_list):
            docker_compose['services']['mc']['environment'] += [f"CURSEFORGE_FILES={" ".join(mods_list)}"]


        # Write the modified configuration back to the file
        with open(docker_compose_file_path, 'w') as file:
            yaml.dump(docker_compose, file, default_flow_style=False)

        print("Docker Compose file updated successfully.")

        os.chdir(spawn_directory)
        docker.compose.up(detach=True, force_recreate=True, recreate=True, attach_dependencies=False, build=True)

    def purge_spawn(self, name: str):

        os.chdir(f"./spawns/{name}")

        docker.compose.down(remove_images="all", volumes=True, remove_orphans=True)

        spawn_directory = f"../{name}"

        if os.path.exists(spawn_directory):
            shutil.rmtree(spawn_directory)
            print("spawn directory purged.")
        else:
            print("No such spawn exists.")
