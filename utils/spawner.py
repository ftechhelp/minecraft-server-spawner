import uuid
from models.spawn import Spawn
import yaml
import os
import logging
from utils.error_handlers import DockerOperationError, FileOperationError, SpawnNotFoundError

logger = logging.getLogger(__name__)

class Spawner:
    
    def __init__(self):
        self.spawns: dict = {}
        self.spawns_directory = "./spawns"
        
        # Ensure spawns directory exists
        try:
            os.makedirs(self.spawns_directory, exist_ok=True)
            logger.info(f"Spawns directory ensured at: {self.spawns_directory}")
        except OSError as e:
            logger.error(f"Failed to create spawns directory: {str(e)}")
            raise FileOperationError("create_directory", self.spawns_directory, str(e))

    def create_or_modify_spawn(self, name: str = str(uuid.uuid4()), new_port: int = 25565, new_volume: str = "./data", new_type: str = "FORGE", new_minecraftVersion: str = "LATEST", new_forgeVersion: str = "LATEST", mods: list = []) -> None:
        """
        Creates or modifies a spawn with comprehensive error handling and resource checking.
        
        Args:
            name: Spawn name
            new_port: Port number for the server
            new_volume: Volume path for data
            new_type: Server type (FORGE, VANILLA, etc.)
            new_minecraftVersion: Minecraft version
            new_forgeVersion: Forge version
            mods: List of mod identifiers
            
        Raises:
            DockerOperationError: If Docker operations fail
            FileOperationError: If file operations fail
        """
        try:
            # Check if Docker is available before attempting operations
            from utils.validators import check_docker_available, check_disk_space
            from utils.error_handlers import ResourceConstraintError
            
            is_available, error_msg = check_docker_available()
            if not is_available:
                logger.error(f"Docker not available: {error_msg}")
                raise DockerOperationError('create_spawn', error_msg, name)
            
            # Check disk space before creating spawn
            is_sufficient, error_msg = check_disk_space(min_space_gb=5.0)
            if not is_sufficient:
                logger.error(f"Insufficient disk space: {error_msg}")
                raise DockerOperationError('create_spawn', error_msg, name)
            spawn = Spawn(
                name or str(uuid.uuid4()), 
                new_port or 25565, 
                new_volume or "./data", 
                new_type or "FORGE", 
                new_minecraftVersion or "LATEST", 
                new_forgeVersion or "LATEST", 
                mods or []
            )
            
            logger.info(f"Creating/modifying spawn: {spawn.name}")
            
            # Get docker compose contents with error handling
            try:
                docker_compose = spawn.get_docker_compose_contents()
            except Exception as e:
                logger.error(f"Failed to get docker-compose contents for {spawn.name}: {str(e)}")
                raise FileOperationError("read", f"{spawn.name}/docker-compose.yml", str(e))

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
            docker_compose['services']['mc']['environment'] += ["CF_API_KEY=${CF_API_KEY}"]
            docker_compose['services']['mc']['environment'] += ["EULA=TRUE"]
            docker_compose['services']['mc']['environment'] += ["REMOVE_OLD_MODS=TRUE"]
            docker_compose['services']['mc']['environment'] += ["INIT_MEMORY=2G"]
            docker_compose['services']['mc']['environment'] += ["MAX_MEMORY=16G"]
            
            if spawn.mods:
                # Format the mods list according to CurseForge documentation
                valid_mods = [mod for mod in spawn.mods if mod.strip()]
                if valid_mods:
                    docker_compose['services']['mc']['environment'] += [f"CURSEFORGE_FILES={' '.join(valid_mods)}"]

            # Write docker compose file with error handling
            try:
                spawn.set_docker_compose_contents(docker_compose)
                logger.info(f"Docker Compose file updated successfully for {spawn.name}")
            except Exception as e:
                logger.error(f"Failed to write docker-compose file for {spawn.name}: {str(e)}")
                raise FileOperationError("write", f"{spawn.name}/docker-compose.yml", str(e))

            # Start the container with error handling
            try:
                spawn.up()
                logger.info(f"Spawn {spawn.name} started successfully")
            except Exception as e:
                logger.error(f"Failed to start spawn {spawn.name}: {str(e)}")
                raise DockerOperationError("up", str(e), spawn.name)

            # Try to load server properties (non-critical)
            try:
                spawn.load_server_properties()
                logger.info(f"Server properties loaded for {spawn.name}")
            except Exception as e:
                logger.warning(f"Could not load server properties for {spawn.name}: {str(e)}")
                logger.info("This is normal for new servers and will be resolved when the server finishes starting.")
            
            self.spawns[spawn.name] = spawn
            logger.info(f"Spawn {spawn.name} added to spawns dictionary")
            
        except (DockerOperationError, FileOperationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Catch any unexpected errors
            logger.error(f"Unexpected error creating spawn {name}: {str(e)}", exc_info=True)
            raise DockerOperationError("create_spawn", str(e), name)
    
    def loadSpawns(self):
        """
        Loads all spawns from the spawns directory with comprehensive error handling.
        Skips corrupted or invalid spawns and continues loading others.
        """
        self.spawns = {}
        spawn_folder = self.spawns_directory
        
        # Ensure spawns directory exists
        if not os.path.exists(spawn_folder):
            logger.warning(f"Spawns directory does not exist: {spawn_folder}")
            try:
                os.makedirs(spawn_folder, exist_ok=True)
                logger.info(f"Created spawns directory: {spawn_folder}")
            except OSError as e:
                logger.error(f"Failed to create spawns directory: {str(e)}")
                return
        
        try:
            spawn_names = os.listdir(spawn_folder)
        except OSError as e:
            logger.error(f"Failed to list spawns directory: {str(e)}")
            return
        
        logger.info(f"Loading spawns from {spawn_folder}")
        loaded_count = 0
        skipped_count = 0

        for name in spawn_names:
            spawn_path = os.path.join(spawn_folder, name)
            
            # Skip if not a directory
            if not os.path.isdir(spawn_path):
                logger.debug(f"'{spawn_path}' is not a directory. Skipping.")
                skipped_count += 1
                continue
            
            docker_file = os.path.join(spawn_path, "docker-compose.yml")
            
            # Check if docker-compose.yml exists
            if not os.path.isfile(docker_file):
                logger.warning(f"No docker-compose.yml file found in '{spawn_path}'. Skipping spawn '{name}'.")
                skipped_count += 1
                continue
            
            # Try to load the spawn
            try:
                with open(docker_file, "r") as f:
                    docker_compose = yaml.safe_load(f)
                
                # Validate docker-compose structure
                if not docker_compose or 'services' not in docker_compose:
                    logger.error(f"Invalid docker-compose.yml structure in '{spawn_path}'. Missing 'services'. Skipping spawn '{name}'.")
                    skipped_count += 1
                    continue
                
                if 'mc' not in docker_compose['services']:
                    logger.error(f"Invalid docker-compose.yml structure in '{spawn_path}'. Missing 'mc' service. Skipping spawn '{name}'.")
                    skipped_count += 1
                    continue
                
                mc_service = docker_compose['services']['mc']
                
                # Extract configuration with error handling
                try:
                    port = mc_service['ports'][0].split(":")[0]
                    volume = mc_service['volumes'][0].split(":")[0]
                    
                    # Parse environment variables safely
                    environment = mc_service.get('environment', [])
                    type_val = "FORGE"  # Default
                    minecraft_version = "LATEST"  # Default
                    forge_version = "LATEST"  # Default
                    mods = []
                    
                    for env in environment:
                        if isinstance(env, str):
                            if env.startswith('TYPE='):
                                type_val = env.split('=', 1)[1]
                            elif env.startswith('VERSION='):
                                minecraft_version = env.split('=', 1)[1]
                            elif env.startswith('FORGE_VERSION='):
                                forge_version = env.split('=', 1)[1]
                            elif env.startswith('CURSEFORGE_FILES='):
                                mods_str = env.split('=', 1)[1]
                                mods = mods_str.split(' ') if mods_str else []
                    
                    # Create spawn object
                    spawn = Spawn(name, port, volume, type_val, minecraft_version, forge_version, mods)
                    self.spawns[spawn.name] = spawn
                    
                    # Try to load server properties (non-critical)
                    try:
                        spawn.load_server_properties()
                        logger.info(f"Spawn '{name}' loaded successfully with server properties.")
                    except Exception as e:
                        logger.warning(f"Spawn '{name}' loaded but failed to load server properties: {str(e)}")
                    
                    loaded_count += 1
                    
                except (KeyError, IndexError, AttributeError) as e:
                    logger.error(f"Failed to parse docker-compose.yml for spawn '{name}': {str(e)}. Skipping spawn.")
                    skipped_count += 1
                    continue
                    
            except yaml.YAMLError as e:
                logger.error(f"Failed to parse YAML in '{docker_file}': {str(e)}. Skipping spawn '{name}'.")
                skipped_count += 1
                continue
            except FileNotFoundError as e:
                logger.error(f"File not found while loading spawn '{name}': {str(e)}. Skipping spawn.")
                skipped_count += 1
                continue
            except Exception as e:
                logger.error(f"Unexpected error loading spawn '{name}': {str(e)}. Skipping spawn.", exc_info=True)
                skipped_count += 1
                continue
        
        logger.info(f"Spawn loading complete. Loaded: {loaded_count}, Skipped: {skipped_count}")
    
    def spawn_exists(self, name: str) -> bool:
        """
        Checks if a spawn exists in the spawns dictionary.
        
        Args:
            name: Spawn name to check
            
        Returns:
            True if spawn exists, False otherwise
        """
        return name in self.spawns
    
    def get_spawn_safely(self, name: str):
        """
        Safely retrieves a spawn by name.
        
        Args:
            name: Spawn name to retrieve
            
        Returns:
            Spawn object if found, None otherwise
        """
        return self.spawns.get(name, None)
    
    def check_port_conflict(self, port: int, exclude_spawn: str = None) -> tuple[bool, str]:
        """
        Checks if a port is already in use by another spawn.
        
        Args:
            port: Port number to check
            exclude_spawn: Optional spawn name to exclude from check (for modifications)
            
        Returns:
            Tuple of (has_conflict, conflicting_spawn_name)
            - has_conflict: True if port is in use
            - conflicting_spawn_name: Name of spawn using the port, or empty string
        """
        for spawn_name, spawn in self.spawns.items():
            # Skip the spawn being modified
            if exclude_spawn and spawn_name == exclude_spawn:
                continue
            
            # Check if port conflicts
            try:
                if int(spawn.port) == int(port):
                    return True, spawn_name
            except (ValueError, TypeError):
                logger.warning(f"Invalid port value for spawn '{spawn_name}': {spawn.port}")
                continue
        
        return False, ""