import os
import yaml
from python_on_whales import docker, Container
import shutil
import tempfile
import zipfile
import logging
from bs4 import BeautifulSoup
from utils.error_handlers import DockerOperationError, FileOperationError, ValidationError

logger = logging.getLogger(__name__)

class Spawn:


    def __init__(self, name: str, port: int, volume: str, type: str, minecraft_version: str, forge_version: str, mods: list) -> None:
        self.name: str = name
        self.directory: str = f"./spawns/{self.name}"
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
        self.docker_compose_file: str = f"{self.directory}/docker-compose.yml"

        self.__updateContainerInformation()
        self.__create_directory()


    def get_docker_compose_contents(self) -> dict:
        """
        Get docker-compose file contents. Creates default structure if file doesn't exist.
        
        Returns:
            Dictionary containing docker-compose configuration
        """
        try:
            # Check if file exists
            if not os.path.exists(self.docker_compose_file):
                logger.warning(f"Docker compose file not found for {self.name}, creating default structure")
                # Create default docker-compose structure
                default_compose = {
                    'version': '3.8',
                    'services': {
                        self.name: {
                            'image': f'itzg/minecraft-server',
                            'container_name': self.name,
                            'environment': {
                                'EULA': 'TRUE',
                                'TYPE': self.type,
                                'VERSION': self.minecraft_version,
                            },
                            'ports': [f'{self.port}:25565'],
                            'volumes': [f'{self.volume}:/data'],
                            'restart': 'unless-stopped'
                        }
                    }
                }
                
                # Add forge version if applicable
                if self.forge_version:
                    default_compose['services'][self.name]['environment']['FORGE_VERSION'] = self.forge_version
                
                # Save the default structure
                self.set_docker_compose_contents(default_compose)
                return default_compose
            
            with open(self.docker_compose_file, 'r') as file:
                docker_compose = yaml.safe_load(file) or {}
            
            return docker_compose
            
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse docker-compose.yml for {self.name}: {str(e)}")
            raise FileOperationError(
                'read',
                self.docker_compose_file,
                f"Invalid YAML format: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error reading docker-compose file for {self.name}: {str(e)}")
            raise FileOperationError(
                'read',
                self.docker_compose_file,
                str(e)
            )
    
    def set_docker_compose_contents(self, docker_compose: dict) -> None:
        """
        Write docker-compose configuration to file.
        
        Args:
            docker_compose: Dictionary containing docker-compose configuration
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.docker_compose_file), exist_ok=True)
            
            with open(self.docker_compose_file, 'w') as file:
                yaml.dump(docker_compose, file, default_flow_style=False)
                
        except Exception as e:
            logger.error(f"Error writing docker-compose file for {self.name}: {str(e)}")
            raise FileOperationError(
                'write',
                self.docker_compose_file,
                str(e)
            )

    def up(self) -> None:
        """
        Start the spawn container using docker-compose up.
        
        Raises:
            DockerOperationError: If docker-compose up fails
        """
        current_dir = os.getcwd()
        try:
            os.chdir(self.directory)
            docker.compose.up(detach=True, force_recreate=True, recreate=True, attach_dependencies=False, build=True)
            logger.info(f"Spawn {self.name} is up.")
            print(f"Spawn {self.name} is up.")
            self.__updateContainerInformation()
            
        except Exception as e:
            logger.error(f"Failed to start spawn {self.name}: {str(e)}", exc_info=True)
            raise DockerOperationError(
                'up',
                f"Failed to start container: {str(e)}",
                self.name
            )
        finally:
            os.chdir(current_dir)

    def stop(self) -> None:
        """
        Stop the spawn container using docker-compose stop.
        
        Raises:
            DockerOperationError: If docker-compose stop fails
        """
        current_dir = os.getcwd()
        try:
            os.chdir(self.directory)
            docker.compose.stop()
            logger.info(f"Spawn {self.name} is stopped.")
            print(f"Spawn {self.name} is stopped.")
            
        except Exception as e:
            logger.error(f"Failed to stop spawn {self.name}: {str(e)}", exc_info=True)
            raise DockerOperationError(
                'stop',
                f"Failed to stop container: {str(e)}",
                self.name
            )
        finally:
            os.chdir(current_dir)

    def start(self) -> None:
        """
        Start the spawn container using docker-compose start.
        
        Raises:
            DockerOperationError: If docker-compose start fails
        """
        current_dir = os.getcwd()
        try:
            os.chdir(self.directory)
            docker.compose.start()
            logger.info(f"Spawn {self.name} is started.")
            print(f"Spawn {self.name} is started.")
            
        except Exception as e:
            logger.error(f"Failed to start spawn {self.name}: {str(e)}", exc_info=True)
            raise DockerOperationError(
                'start',
                f"Failed to start container: {str(e)}",
                self.name
            )
        finally:
            os.chdir(current_dir)

    def purge(self) -> None:
        """
        Remove the spawn container and delete its directory.
        
        Raises:
            DockerOperationError: If docker-compose down fails
            FileOperationError: If directory deletion fails
        """
        current_dir = os.getcwd()
        try:
            os.chdir(self.directory)
            docker.compose.down(remove_images="all", volumes=True, remove_orphans=True)
            logger.info(f"Spawn {self.name} down.")
            print(f"Spawn {self.name} down.")
            
        except Exception as e:
            logger.error(f"Failed to bring down spawn {self.name}: {str(e)}", exc_info=True)
            raise DockerOperationError(
                'down',
                f"Failed to remove container: {str(e)}",
                self.name
            )
        finally:
            os.chdir(current_dir)

        # Delete directory
        try:
            if os.path.exists(self.directory):
                shutil.rmtree(self.directory)
                logger.info(f"Spawn {self.name} directory purged.")
                print(f"Spawn {self.name} directory purged.")
            else:
                logger.warning(f"No such spawn directory exists for {self.name}.")
                print(f"No such spawn directory exists for {self.name}.")
                
        except Exception as e:
            logger.error(f"Failed to delete directory for spawn {self.name}: {str(e)}", exc_info=True)
            raise FileOperationError(
                'delete',
                self.directory,
                f"Failed to delete spawn directory: {str(e)}"
            )

    def get_status(self) -> str:
        """
        Get the current status of the container.
        
        Returns:
            Status string or "N/A" if container doesn't exist
        """
        if self.container == None:
            return "N/A"
        
        status = self.container.state.status
        return status
    
    def is_running(self) -> bool:
        """
        Check if the container is currently running.
        
        Returns:
            True if container is running, False otherwise
        """
        if self.container is None:
            return False
        
        try:
            # Refresh container information to get current state
            self.__updateContainerInformation()
            return self.container is not None and self.container.state.status == "running"
        except Exception as e:
            logger.warning(f"Error checking if spawn {self.name} is running: {str(e)}")
            return False
    
    def can_execute_command(self) -> bool:
        """
        Check if the container is in a state where commands can be executed.
        
        Returns:
            True if commands can be executed, False otherwise
        """
        return self.is_running()
    
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
        """
        Upload and process a modpack ZIP file.
        
        Args:
            zip_file: Uploaded ZIP file containing modlist.html
            
        Raises:
            ValidationError: If file is not a valid ZIP or missing modlist.html
            FileOperationError: If temporary directory creation fails
        """
        temp_dir = None
        try:
            # Create a temporary directory to extract the zip file
            temp_dir = tempfile.mkdtemp()
            
            # Save the uploaded file to the temp directory
            zip_path = os.path.join(temp_dir, "modpack.zip")
            zip_file.save(zip_path)
            
            # Validate that it's a ZIP file
            if not zipfile.is_zipfile(zip_path):
                logger.error(f"Uploaded file is not a valid ZIP archive for {self.name}")
                raise ValidationError(
                    'modpack_file',
                    'Uploaded file is not a valid ZIP archive',
                    zip_path
                )
            
            # Extract the zip file
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            except zipfile.BadZipFile as e:
                logger.error(f"Corrupted ZIP file for {self.name}: {str(e)}")
                raise ValidationError(
                    'modpack_file',
                    'ZIP file is corrupted or invalid',
                    zip_path
                )
            
            # Find the modlist.html file
            modlist_path = None
            for root, dirs, files in os.walk(temp_dir):
                if "modlist.html" in files:
                    modlist_path = os.path.join(root, "modlist.html")
                    break
            
            if not modlist_path:
                logger.error(f"modlist.html not found in the uploaded zip file for {self.name}")
                raise ValidationError(
                    'modpack_file',
                    'modlist.html not found in the uploaded ZIP file. Please ensure your modpack export includes the mod list.',
                    zip_path
                )
            
            # Parse the HTML file to extract URLs
            try:
                with open(modlist_path, 'r', encoding='utf-8') as file:
                    html_content = file.read()
            except Exception as e:
                logger.error(f"Failed to read modlist.html for {self.name}: {str(e)}")
                raise FileOperationError(
                    'read',
                    modlist_path,
                    f"Failed to read modlist.html: {str(e)}"
                )
            
            # Use BeautifulSoup to parse the HTML
            try:
                soup = BeautifulSoup(html_content, 'html.parser')
            except Exception as e:
                logger.error(f"Failed to parse modlist.html for {self.name}: {str(e)}")
                raise ValidationError(
                    'modpack_file',
                    f'Failed to parse modlist.html: malformed HTML',
                    modlist_path
                )
            
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
                            logger.warning(f"Could not parse file URL: {mod_url}")
                            print(f"Could not parse file URL: {mod_url}")
                    else:
                        # This is a project page URL, get the last part
                        slug = parts[-1]
                        self.addMod(slug)
                else:
                    # Not a CurseForge URL or doesn't match expected pattern
                    logger.debug(f"Skipping URL that doesn't match expected CurseForge pattern: {mod_url}")
                    print(f"Skipping URL that doesn't match expected CurseForge pattern: {mod_url}")
            
            logger.info(f"Successfully processed modpack for {self.name}. Added {len(mod_links)} mods.")
            print(f"Successfully processed modpack for {self.name}. Added {len(mod_links)} mods.")
            
        except (ValidationError, FileOperationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing modpack for {self.name}: {str(e)}", exc_info=True)
            raise FileOperationError(
                'process',
                'modpack.zip',
                f"Unexpected error processing modpack: {str(e)}"
            )
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary directory {temp_dir}: {str(e)}")

    def load_server_properties(self) -> None:
        """
        Load server.properties file from the spawn's data directory.
        Handles missing files gracefully for new servers.
        """
        properties_path = f"{self.directory}/data/server.properties"
        try:
            with open(properties_path, 'r') as file:
                self.server_properties = file.read()
            logger.info(f"Loaded server.properties for {self.name}")
            
        except FileNotFoundError:
            # File doesn't exist yet, which can happen when the container is first created
            # Set default empty properties or wait until file is created
            self.server_properties = ""
            logger.info(f"server.properties file not found for {self.name}. This is normal for new servers.")
            print(f"Warning: server.properties file not found for {self.name}. This is normal for new servers.")
            
        except Exception as e:
            logger.error(f"Error reading server.properties for {self.name}: {str(e)}")
            raise FileOperationError(
                'read',
                properties_path,
                f"Failed to read server.properties: {str(e)}"
            )

    def write_server_properties(self, server_properties) -> None:
        """
        Write server.properties file to the spawn's data directory and restart the container.
        
        Args:
            server_properties: Content to write to server.properties file
            
        Raises:
            FileOperationError: If writing the file fails
        """
        properties_path = f"{self.directory}/data/server.properties"
        try:
            # Make sure the data directory exists
            os.makedirs(f"{self.directory}/data", exist_ok=True)
            
            with open(properties_path, 'w') as file:
                file.write(server_properties)
                self.server_properties = server_properties
            
            logger.info(f"Wrote server.properties for {self.name}")
            
        except PermissionError as e:
            logger.error(f"Permission denied writing server.properties for {self.name}: {str(e)}")
            raise FileOperationError(
                'write',
                properties_path,
                f"Permission denied: {str(e)}"
            )
        except OSError as e:
            logger.error(f"OS error writing server.properties for {self.name}: {str(e)}")
            raise FileOperationError(
                'write',
                properties_path,
                f"Failed to write file: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Error writing server.properties for {self.name}: {str(e)}")
            raise FileOperationError(
                'write',
                properties_path,
                f"Unexpected error: {str(e)}"
            )
        
        # Restart the container to apply changes
        self.up()

    def send_console_command(self, command: str) -> None:
        """
        Send a console command to the running Minecraft server via rcon-cli.
        
        Args:
            command: Console command to execute
            
        Raises:
            DockerOperationError: If container is not running or command execution fails
        """
        # Check if container can execute commands
        if not self.can_execute_command():
            logger.error(f"Cannot execute command on {self.name}: container is not running")
            raise DockerOperationError(
                'execute',
                'Container is not running. Please start the container before sending commands.',
                self.name
            )
        
        try:
            docker.execute(container=self.name, command=["rcon-cli", command])
            logger.info(f"Executed command on {self.name}: {command}")
            self.__updateLogs(20)
            
        except Exception as e:
            logger.error(f"Failed to execute command on {self.name}: {str(e)}", exc_info=True)
            raise DockerOperationError(
                'execute',
                f"Failed to execute command: {str(e)}. Ensure rcon is enabled in server.properties.",
                self.name
            )

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