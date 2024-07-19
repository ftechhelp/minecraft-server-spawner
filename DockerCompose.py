import yaml

class DockerCompose:
    
    def __init__(self, file_path):
        self.file_path = file_path

    def modify_docker_compose(self, name: str = None, new_port: int = None, new_volume: str = None, new_type: str = None, new_minecraftVersion: str = None, new_forgeVersion: str = None, mods: list = None):
        
        with open(self.file_path, 'w+') as file:
            docker_compose = yaml.safe_load(file) or {}

        if 'services' not in docker_compose:
            docker_compose['services'] = {}
        if 'mc' not in docker_compose['services']:
            docker_compose['services']['mc'] = {}

        docker_compose['services']['mc']['container_name'] = f'{name or "default"}-{new_port or 25565}-{new_minecraftVersion or "LATEST"}-{new_forgeVersion or "LATEST"}-{new_type or "FORGE"}'
        docker_compose['services']['mc']['ports'] = [f"{new_port or 25565}:25565"]
        docker_compose['services']['mc']['volumes'] = [f"{new_volume or "./data"}:/data"]
        docker_compose['services']['mc']['image'] = "itzg/minecraft-server"
        docker_compose['services']['mc']['stdin_open'] = True
        docker_compose['services']['mc']['tty'] = True

        docker_compose['services']['mc']['environment'] = [f"TYPE={new_type or "FORGE"}"]
        docker_compose['services']['mc']['environment'] += [f"MINECRAFT_VERSION={new_minecraftVersion or "LATEST"}"]
        docker_compose['services']['mc']['environment'] += [f"FORGE_VERSION={new_forgeVersion or "LATEST"}"]
        docker_compose['services']['mc']['environment'] += ["CF_API_KEY=${CF_API_KEY}"] # Make sure you have a .env file with the CF_API_KEY variable
        

        mods_list = mods or []
        if (mods_list):
            docker_compose['services']['mc']['environment'] += [f"CURSEFORGE_FILES={" ".join(mods_list)}"]


        # Write the modified configuration back to the file
        with open(self.file_path, 'w') as file:
            yaml.dump(docker_compose, file, default_flow_style=False)

        print("Docker Compose file updated successfully.")
        
        self.__run_docker_compose()

    def __run_docker_compose(self):
        import subprocess
        subprocess.run(f'docker compose up --build --force-recreate --no-deps', shell=True)

dc = DockerCompose('docker-compose.yml')
dc.modify_docker_compose(new_minecraftVersion="1.20.1", mods=['https://www.curseforge.com/minecraft/mc-mods/dragon-ball-mod-1-16-5/files/5541977'])
