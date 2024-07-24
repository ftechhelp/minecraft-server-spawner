import os
import yaml
from python_on_whales import docker
import shutil

class Spawn:


    def __init__(self, name: str, port: int, volume: str, type: str, minecraft_version: str, forge_version: str, mods: list, server_properties: list) -> None:
        self.name: str = name
        self.directory: str = f"./spawns/{self.name}"
        self.volume: str = volume
        self.port: int = port
        self.type: str = type
        self.minecraft_version: str = minecraft_version
        self.forge_version: str = forge_version
        self.mods: list = mods
        self.server_properties: list = server_properties
        self.docker_compose_file: str = f"{self.directory}/docker-compose.yml"

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


    def __create_directory(self) -> None:
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)