from bottle import get, post, run, template, request, redirect, HTTPError
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
    handle_validation_errors
)
from dotenv import load_dotenv
import os
import logging

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

spawner = Spawner()
spawner.loadSpawns()

@get('/')
def index():
    spawner.loadSpawns()
    return template('./templates/index', spawns=spawner.spawns)

@post('/spawn')
@handle_validation_errors
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
    redirect("/")

@get('/spawn/<name>')
@handle_spawn_not_found
def view_spawn(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    return template('./templates/spawn', spawn=spawner.spawns[name])

@post('/spawn/<name>/recreate')
@handle_spawn_not_found
def recreate_spawn(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    spawn.up()
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/start')
@handle_spawn_not_found
def start_spawn(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    spawn.start()
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/stop')
@handle_spawn_not_found
def stop_spawn(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    spawn.stop()
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/delete')
@handle_spawn_not_found
def delete_spawn(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    spawn.purge()
    redirect('/')

@post('/spawn/<name>/refresh')
@handle_spawn_not_found
def refresh_spawn(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    spawn.refreshContainerInformation()
    redirect(f"/spawn/{name}")

@get('/spawn/<name>/logs')
@handle_spawn_not_found
def download_logs(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    return template('./templates/spawn_logs', logs=spawn.get_logs())

@post('/spawn/<name>/mods/delete')
@handle_spawn_not_found
@handle_validation_errors
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
    
    spawn.removeMod(mod)
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/mods/add')
@handle_spawn_not_found
@handle_validation_errors
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
    
    spawn.addMod(mod)
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/mods/sync')
@handle_spawn_not_found
def sync_mods(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    spawn.syncMods()
    spawner.create_or_modify_spawn(name=spawn.name, new_port=spawn.port, new_type=spawn.type, new_minecraftVersion=spawn.minecraft_version, new_forgeVersion=spawn.forge_version, mods=spawn.mods)
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/mods/upload')
@handle_spawn_not_found
def upload_mod(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    spawn.uploadMods(request.files.get('mods'))
    redirect(f"/spawn/{name}")


@post('/spawn/<name>/server_properties/save')
@handle_spawn_not_found
def save_server_properties(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    spawn.write_server_properties(request.POST.server_properties)
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/console/send')
@handle_spawn_not_found
def send_console_command(name):
    if name not in spawner.spawns:
        raise SpawnNotFoundError(name)
    spawn = spawner.spawns[name]
    spawn.send_console_command(request.POST.consoleCommand)
    redirect(f"/spawn/{name}")




run(host='0.0.0.0', port=8888, reloader=True, debug=True)