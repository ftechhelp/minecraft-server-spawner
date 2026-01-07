from bottle import get, post, run, template, request, redirect, BaseRequest
from utils.spawner import Spawner
from utils.backup_scheduler import backup_scheduler
from dotenv import load_dotenv
import os
import atexit

load_dotenv()

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
    return template('./templates/index', spawns=spawner.spawns)

@post('/spawn')
def spawn():
    
    name = request.POST.name.strip() or None
    port = int(request.POST.port.strip()) if request.POST.port.strip() else None
    type = request.POST.type.strip() or None
    minecraft_version = request.POST.minecraft_version.strip() or None
    forge_version = request.POST.forge_version.strip() or None

    spawner.create_or_modify_spawn(name=name, new_port=port, new_type=type, new_minecraftVersion=minecraft_version, new_forgeVersion=forge_version)
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


run(host='0.0.0.0', port=8888, reloader=True, debug=True)