from bottle import get, post, run, template, request, redirect, BaseRequest
from utils.spawner import Spawner
from utils.backup_scheduler import backup_scheduler
from utils.validators import (
    validate_spawn_name,
    validate_port,
    validate_server_type,
    validate_minecraft_version,
    validate_forge_version,
    check_port_availability,
    find_next_available_port,
)
from dotenv import load_dotenv
import os
import atexit

load_dotenv()


def env_flag(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}

# Allow large multi-file uploads (e.g., a folder of .jar mods)
# Default is ~100KB; increase to 512MB to support mod folder uploads
BaseRequest.MEMFILE_MAX = 512 * 1024 * 1024

spawner = Spawner()
spawner.loadSpawns()
spawner.recreate_all_spawns_once()

# Start backup scheduler
backup_scheduler.start(spawner)
atexit.register(backup_scheduler.stop)

@get('/')
def index():
    spawner.loadSpawns()
    return template('./templates/index', spawns=spawner.spawns, create_error=None, create_form={})

@get('/docs')
def documentation():
    return template('./templates/documentation')

@post('/spawn')
def spawn():
    spawner.loadSpawns()

    raw_name = request.POST.get('name', '').strip()
    raw_port = request.POST.get('port', '').strip()
    raw_type = request.POST.get('type', '').strip()
    raw_minecraft_version = request.POST.get('minecraft_version', '').strip()
    raw_forge_version = request.POST.get('forge_version', '').strip()

    create_form = {
        'name': raw_name,
        'port': raw_port,
        'type': raw_type or 'FORGE',
        'minecraft_version': raw_minecraft_version or 'LATEST',
        'forge_version': raw_forge_version or 'LATEST',
    }

    name = None
    if raw_name:
        valid_name, name, name_error = validate_spawn_name(raw_name)
        if not valid_name:
            return template('./templates/index', spawns=spawner.spawns, create_error=name_error, create_form=create_form)

        if spawner.spawn_name_exists(name):
            return template('./templates/index', spawns=spawner.spawns, create_error=f"Spawn name '{name}' already exists", create_form=create_form)

        if spawner.spawn_directory_exists(name):
            return template('./templates/index', spawns=spawner.spawns, create_error=f"Spawn directory for '{name}' already exists on disk", create_form=create_form)

    if raw_port:
        valid_port, port, port_error = validate_port(raw_port)
        if not valid_port:
            return template('./templates/index', spawns=spawner.spawns, create_error=port_error, create_form=create_form)

        is_port_available, port_conflict_error = check_port_availability(port, spawner)
        if not is_port_available:
            return template('./templates/index', spawns=spawner.spawns, create_error=port_conflict_error, create_form=create_form)
    else:
        port = find_next_available_port(spawner)
        if port is None:
            return template('./templates/index', spawns=spawner.spawns, create_error="No available ports left in the allowed range (25565-25665)", create_form=create_form)

    valid_type, server_type, type_error = validate_server_type(raw_type)
    if not valid_type:
        return template('./templates/index', spawns=spawner.spawns, create_error=type_error, create_form=create_form)

    minecraft_version_input = raw_minecraft_version or 'LATEST'
    valid_version, minecraft_version, version_error = validate_minecraft_version(minecraft_version_input)
    if not valid_version:
        return template('./templates/index', spawns=spawner.spawns, create_error=version_error, create_form=create_form)

    forge_version_input = raw_forge_version or 'LATEST'
    valid_forge, forge_version, forge_error = validate_forge_version(forge_version_input, server_type)
    if not valid_forge:
        return template('./templates/index', spawns=spawner.spawns, create_error=forge_error, create_form=create_form)

    try:
        spawner.create_or_modify_spawn(name=name, new_port=port, new_type=server_type, new_minecraftVersion=minecraft_version, new_forgeVersion=forge_version)
    except Exception as exc:
        return template('./templates/index', spawns=spawner.spawns, create_error=f"Failed to create server: {str(exc)}", create_form=create_form)

    redirect("/")

@get('/spawn/<name>')
def view_spawn(name):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    spawn = spawner.spawns[name]
    spawn.refreshContainerInformation()
    spawn.reload_backup_settings()
    tz = ZoneInfo("America/Vancouver")
    default_backup_name = f"backup_{datetime.now(tz=tz).strftime('%Y%m%d_%H%M%S')}"
    return template('./templates/spawn', spawn=spawn, mods=spawn.list_mods(), default_backup_name=default_backup_name)

@post('/spawn/<name>/recreate')
def recreate_spawn(name):
    spawn = spawner.spawns[name]
    spawn.up()
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/start')
def start_spawn(name):
    spawn = spawner.spawns[name]
    spawn.start()
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/stop')
def stop_spawn(name):
    spawn = spawner.spawns[name]
    spawn.stop()
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/delete')
def delete_spawn(name):
    spawn = spawner.spawns[name]
    spawn.purge()
    redirect('/')

@post('/spawn/<name>/refresh')
def refresh_spawn(name):
    spawn = spawner.spawns[name]
    spawn.refreshContainerInformation()
    redirect(f"/spawn/{name}")

@get('/spawn/<name>/logs')
def download_logs(name):
    spawn = spawner.spawns[name]
    return template('./templates/spawn_logs', logs=spawn.get_logs())

@get('/spawn/<name>/logs/content')
def get_logs_content(name):
    spawn = spawner.spawns[name]
    spawn.refreshContainerInformation()
    return spawn.get_logs()

@get('/spawn/<name>/status')
def get_spawn_status(name):
    import json
    spawn = spawner.spawns[name]
    spawn.refreshContainerInformation()
    status = spawn.get_status()
    return json.dumps({'status': status})

@post('/spawn/<name>/mods/delete')
def delete_mod(name):
    spawn = spawner.spawns[name]
    mod_filename = request.POST.mod.strip()
    spawn.remove_mod_file(mod_filename)
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/mods/add-file')
def add_mod_file(name):
    spawn = spawner.spawns[name]
    mod_upload = request.files.get('mod')
    if mod_upload:
        spawn.add_mod_file(mod_upload)
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/mods/replace')
def replace_mods(name):
    spawn = spawner.spawns[name]
    print(f"[replace_mods route] Processing replace for {name}")
    try:
        uploads = request.files.getall('mods')
        print(f"[replace_mods route] Got {len(uploads)} files via getall")
    except Exception as e:
        print(f"[replace_mods route] getall failed: {e}, trying get")
        up = request.files.get('mods')
        uploads = [up] if up else []
        print(f"[replace_mods route] Got {len(uploads)} files via get")
    
    if not uploads:
        print(f"[replace_mods route] WARNING: No files received!")
    
    spawn.replace_mods_from_uploads(uploads)
    redirect(f"/spawn/{name}")

# Deprecated: zip-based import; kept for compatibility if still used
@post('/spawn/<name>/mods/upload')
def upload_mod(name):
    spawn = spawner.spawns[name]
    # No-op or translate zip uploads in future
    redirect(f"/spawn/{name}")


@post('/spawn/<name>/server_properties/save')
def save_server_properties(name):
    spawn = spawner.spawns[name]
    spawn.write_server_properties(request.POST.server_properties)
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/console/send')
def send_console_command(name):
    spawn = spawner.spawns[name]
    spawn.send_console_command(request.POST.consoleCommand)
    redirect(f"/spawn/{name}")


# --- Backup Management Routes ---
@post('/spawn/<name>/backup/create')
def create_backup(name):
    spawn = spawner.spawns[name]
    backup_name = request.forms.get('backup_name', '').strip()
    backup_name = backup_name if backup_name else None
    success, message, backup_file = spawn.create_backup(backup_name, is_scheduled=False)
    # Redirect back to spawn page (backup creation happens in background)
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/backup/restore/<backup_name>')
def restore_backup(name, backup_name):
    spawn = spawner.spawns[name]
    success, message = spawn.restore_backup(backup_name)
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/backup/delete/<backup_name>')
def delete_backup(name, backup_name):
    spawn = spawner.spawns[name]
    success, message = spawn.delete_backup(backup_name)
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/backup/settings')
def update_backup_settings(name):
    spawn = spawner.spawns[name]
    # Handle checkbox - it's only present in POST if checked
    daily_enabled = 'daily_backup_enabled' in request.POST
    hour = int(request.POST.daily_backup_hour) if request.POST.daily_backup_hour else 2
    minute = int(request.POST.daily_backup_minute) if request.POST.daily_backup_minute else 0
    retention_days = int(request.POST.retention_days) if request.POST.retention_days else 7
    
    success, message = spawn.update_backup_settings(
        daily_enabled=daily_enabled,
        hour=hour,
        minute=minute,
        retention_days=retention_days
    )
    redirect(f"/spawn/{name}")


if __name__ == '__main__':
    run(
        host='0.0.0.0',
        port=8888,
        reloader=env_flag('BOTTLE_RELOADER', 'false'),
        debug=env_flag('BOTTLE_DEBUG', 'false'),
    )