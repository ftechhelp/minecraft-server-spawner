from bottle import get, post, run, template, request, redirect, HTTPError
from beaker.middleware import SessionMiddleware
from utils.spawner import Spawner
from utils.validators import (
    validate_port, 
    validate_spawn_name, 
    validate_minecraft_version,
    validate_mod_name,
    check_port_availability
)
from utils.error_handlers import (
    ValidationError,
    SpawnNotFoundError,
    handle_spawn_not_found,
    handle_validation_errors,
    handle_docker_errors,
    handle_file_errors
)
from dotenv import load_dotenv
import os
import logging

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Session configuration
session_opts = {
    'session.type': 'memory',
    'session.cookie_expires': 3600,
    'session.auto': True
}

spawner = Spawner()
spawner.loadSpawns()

# Flash message helper functions
def set_flash_message(message, message_type='info'):
    """
    Set a flash message to be displayed on the next page load.
    
    Args:
        message (str): The message to display
        message_type (str): The type of message ('success', 'info', 'warning', 'danger')
    """
    session = request.environ.get('beaker.session')
    if session:
        if 'flash_messages' not in session:
            session['flash_messages'] = []
        session['flash_messages'].append({
            'message': message,
            'type': message_type
        })
        session.save()

def get_flash_messages():
    """
    Retrieve and clear all flash messages from the session.
    
    Returns:
        list: List of flash message dictionaries with 'message' and 'type' keys
    """
    session = request.environ.get('beaker.session')
    if session and 'flash_messages' in session:
        messages = session['flash_messages']
        session['flash_messages'] = []
        session.save()
        return messages
    return []

@get('/')
def index():
    spawner.loadSpawns()
    flash_messages = get_flash_messages()
    return template('./templates/index', spawns=spawner.spawns, flash_messages=flash_messages)

@post('/spawn')
@handle_validation_errors
@handle_docker_errors
@handle_file_errors
def spawn():
    # Get raw form inputs
    name_raw = request.POST.get('name', '').strip()
    port_raw = request.POST.get('port', '').strip()
    type_raw = request.POST.get('type', '').strip() or None
    minecraft_version_raw = request.POST.get('minecraft_version', '').strip()
    forge_version_raw = request.POST.get('forge_version', '').strip() or None
    
    # Validate spawn name
    is_valid, name, error_msg = validate_spawn_name(name_raw)
    if not is_valid:
        logger.warning(f"Spawn name validation failed: {error_msg}")
        raise ValidationError('spawn name', error_msg, name_raw)
    
    # Validate port
    is_valid, port, error_msg = validate_port(port_raw)
    if not is_valid:
        logger.warning(f"Port validation failed: {error_msg}")
        raise ValidationError('port', error_msg, port_raw)
    
    # Check for port conflicts (only if creating new spawn)
    if name not in spawner.spawns:
        is_available, error_msg = check_port_availability(port, spawner)
        if not is_available:
            logger.warning(f"Port conflict detected: {error_msg}")
            raise ValidationError('port', error_msg, port)
    else:
        # For existing spawns, exclude current spawn from port check
        is_available, error_msg = check_port_availability(port, spawner, exclude_spawn=name)
        if not is_available:
            logger.warning(f"Port conflict detected: {error_msg}")
            raise ValidationError('port', error_msg, port)
    
    # Validate Minecraft version
    is_valid, minecraft_version, error_msg = validate_minecraft_version(minecraft_version_raw)
    if not is_valid:
        logger.warning(f"Minecraft version validation failed: {error_msg}")
        raise ValidationError('minecraft version', error_msg, minecraft_version_raw)
    
    # Forge version is optional, no validation needed
    
    logger.info(f"Creating/modifying spawn: {name} on port {port}")
    spawner.create_or_modify_spawn(
        name=name, 
        new_port=port, 
        new_type=type_raw, 
        new_minecraftVersion=minecraft_version, 
        new_forgeVersion=forge_version_raw
    )
    set_flash_message(f"Spawn '{name}' created/modified successfully!", 'success')
    redirect("/")

@get('/spawn/<name>')
@handle_spawn_not_found
def view_spawn(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    flash_messages = get_flash_messages()
    return template('./templates/spawn', spawn=spawner.spawns[name], flash_messages=flash_messages)

@post('/spawn/<name>/recreate')
@handle_spawn_not_found
@handle_docker_errors
def recreate_spawn(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    logger.info(f"Recreating spawn: {name}")
    spawn.up()
    set_flash_message(f"Spawn '{name}' recreated successfully!", 'success')
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/start')
@handle_spawn_not_found
@handle_docker_errors
def start_spawn(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    logger.info(f"Starting spawn: {name}")
    spawn.start()
    set_flash_message(f"Spawn '{name}' started successfully!", 'success')
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/stop')
@handle_spawn_not_found
@handle_docker_errors
def stop_spawn(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    logger.info(f"Stopping spawn: {name}")
    spawn.stop()
    set_flash_message(f"Spawn '{name}' stopped successfully!", 'success')
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/delete')
@handle_spawn_not_found
@handle_docker_errors
@handle_file_errors
def delete_spawn(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    logger.info(f"Deleting spawn: {name}")
    spawn.purge()
    set_flash_message(f"Spawn '{name}' deleted successfully!", 'success')
    redirect('/')

@post('/spawn/<name>/refresh')
@handle_spawn_not_found
@handle_docker_errors
def refresh_spawn(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    logger.info(f"Refreshing spawn information: {name}")
    spawn.refreshContainerInformation()
    set_flash_message(f"Spawn '{name}' information refreshed!", 'info')
    redirect(f"/spawn/{name}")

@get('/spawn/<name>/logs')
@handle_spawn_not_found
@handle_docker_errors
def download_logs(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    logger.info(f"Retrieving logs for spawn: {name}")
    return template('./templates/spawn_logs', logs=spawn.get_logs())

@post('/spawn/<name>/mods/delete')
@handle_spawn_not_found
@handle_validation_errors
@handle_file_errors
def delete_mod(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    
    # Validate mod name
    mod_raw = request.POST.get('mod', '').strip()
    is_valid, mod, error_msg = validate_mod_name(mod_raw)
    if not is_valid:
        logger.warning(f"Mod name validation failed: {error_msg}")
        raise ValidationError('mod name', error_msg, mod_raw)
    
    logger.info(f"Deleting mod '{mod}' from spawn: {name}")
    spawn.removeMod(mod)
    set_flash_message(f"Mod '{mod}' removed from spawn '{name}'!", 'success')
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/mods/add')
@handle_spawn_not_found
@handle_validation_errors
@handle_file_errors
def add_mod(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    
    # Validate mod name
    mod_raw = request.POST.get('mod', '').strip()
    is_valid, mod, error_msg = validate_mod_name(mod_raw)
    if not is_valid:
        logger.warning(f"Mod name validation failed: {error_msg}")
        raise ValidationError('mod name', error_msg, mod_raw)
    
    logger.info(f"Adding mod '{mod}' to spawn: {name}")
    spawn.addMod(mod)
    set_flash_message(f"Mod '{mod}' added to spawn '{name}'!", 'success')
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/mods/sync')
@handle_spawn_not_found
@handle_docker_errors
@handle_file_errors
def sync_mods(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    logger.info(f"Syncing mods for spawn: {name}")
    spawn.syncMods()
    spawner.create_or_modify_spawn(name=spawn.name, new_port=spawn.port, new_type=spawn.type, new_minecraftVersion=spawn.minecraft_version, new_forgeVersion=spawn.forge_version, mods=spawn.mods)
    set_flash_message(f"Mods synced successfully for spawn '{name}'!", 'success')
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/mods/upload')
@handle_spawn_not_found
@handle_validation_errors
@handle_file_errors
def upload_mod(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    logger.info(f"Uploading mods for spawn: {name}")
    spawn.uploadMods(request.files.get('mods'))
    set_flash_message(f"Mods uploaded successfully for spawn '{name}'!", 'success')
    redirect(f"/spawn/{name}")


@post('/spawn/<name>/server_properties/save')
@handle_spawn_not_found
@handle_file_errors
def save_server_properties(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    logger.info(f"Saving server properties for spawn: {name}")
    spawn.write_server_properties(request.POST.server_properties)
    set_flash_message(f"Server properties saved for spawn '{name}'!", 'success')
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/console/send')
@handle_spawn_not_found
@handle_docker_errors
def send_console_command(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    command = request.POST.consoleCommand
    logger.info(f"Sending console command to spawn {name}: {command}")
    spawn.send_console_command(command)
    set_flash_message(f"Console command sent to spawn '{name}'!", 'info')
    redirect(f"/spawn/{name}")




# Wrap the Bottle app with SessionMiddleware
from bottle import default_app
app = default_app()
app = SessionMiddleware(app, session_opts)

if __name__ == '__main__':
    run(app=app, host='0.0.0.0', port=8888, reloader=True, debug=True)