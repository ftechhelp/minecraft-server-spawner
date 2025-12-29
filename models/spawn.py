import os
import yaml
from python_on_whales import docker, Container
import shutil
import tempfile
import zipfile
import os
from bs4 import BeautifulSoup

class Spawn:


    def __init__(self, name: str, port: int, volume: str, type: str, minecraft_version: str, forge_version: str, mods: list) -> None:
        self.base_dir: str = os.environ.get("SPAWNS_DIR", "./spawns")
        self.name: str = name
        self.directory: str = os.path.join(self.base_dir, self.name)
        self.volume: str = volume
        self.port: int = port
        self.type: str = type
        self.minecraft_version: str = minecraft_version
        self.forge_version: str = forge_version
        self.mods: list = mods
        self.virtualMods: list = mods[:]
        self.unloadedRemovedMods: list = []
        self.unloadedAddedMods: list = []
        self.server_properties: str = ""
        self.docker_compose_file: str = os.path.join(self.directory, "docker-compose.yml")

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

    def removeMod(self, mod: str) -> None:
        self.unloadedRemovedMods.append(mod)
        self.unloadedAddedMods = [m for m in self.unloadedAddedMods if m != mod]
        self.virtualMods = [m for m in self.virtualMods if m != mod]
        print(self.virtualMods)

    def addMod(self, mod: str) -> None:
        self.unloadedAddedMods.append(mod)
        self.unloadedRemovedMods = [m for m in self.unloadedRemovedMods if m != mod]
        self.virtualMods.append(mod)

    def syncMods(self) -> None:
        self.mods = self.virtualMods[:]
        self.unloadedRemovedMods = []
        self.unloadedAddedMods = []

    def uploadMods(self, zip_file) -> None:
        try:
            # Create a temporary directory to extract the zip file
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save the uploaded file to the temp directory
                zip_path = os.path.join(temp_dir, "modpack.zip")
                zip_file.save(zip_path)
                
                # Extract the zip file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Find the modlist.html file
                modlist_path = None
                for root, dirs, files in os.walk(temp_dir):
                    if "modlist.html" in files:
                        modlist_path = os.path.join(root, "modlist.html")
                        break
                
                if not modlist_path:
                    print(f"Error: modlist.html not found in the uploaded zip file for {self.name}")
                    return
                
                # Parse the HTML file to extract URLs
                with open(modlist_path, 'r', encoding='utf-8') as file:
                    html_content = file.read()
                
                # Use BeautifulSoup to parse the HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Find all links in the HTML
                mod_links = []
                for a_tag in soup.find_all('a', href=True):
                    url = a_tag['href']
                    # Check if it's a valid URL
                    if url.startswith('http') and 'curseforge.com' in url:
                        mod_links.append(url)
                
                # Add each mod URL
                for mod_url in mod_links:
                    # Extract the project slug according to CurseForge format
                    # CurseForge URLs typically follow this pattern:
                    # https://www.curseforge.com/minecraft/mc-mods/[project-slug]
                    
                    # Check if it's a CurseForge URL
                    if 'curseforge.com/minecraft/mc-mods/' in mod_url:
                        # Parse the URL to extract just the project slug
                        # Remove trailing slash if present
                        parts = mod_url.rstrip('/').split('/')
                        
                        # The slug should be the last part of the URL for project pages
                        # For file pages, we need to handle differently
                        if 'files' in parts:
                            # This is a file page URL, get the project slug which is before 'files'
                            try:
                                slug_index = parts.index('mc-mods') + 1
                                if slug_index < len(parts):
                                    slug = parts[slug_index]
                                    self.addMod(slug)
                            except (ValueError, IndexError):
                                print(f"Could not parse file URL: {mod_url}")
                        else:
                            # This is a project page URL, get the last part
                            slug = parts[-1]
                            self.addMod(slug)
                    else:
                        # Not a CurseForge URL or doesn't match expected pattern
                        print(f"Skipping URL that doesn't match expected CurseForge pattern: {mod_url}")
                
                print(f"Successfully processed modpack for {self.name}. Added {len(mod_links)} mods.")
                
        except Exception as e:
            print(f"Error processing modpack for {self.name}: {str(e)}")

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