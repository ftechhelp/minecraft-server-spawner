from bottle import get, post, run, template, request, redirect, BaseRequest
from utils.spawner import Spawner
from dotenv import load_dotenv
import os

load_dotenv()

# Allow large multi-file uploads (e.g., a folder of .jar mods)
# Default is ~100KB; increase to 512MB to support mod folder uploads
BaseRequest.MEMFILE_MAX = 512 * 1024 * 1024

spawner = Spawner()
spawner.loadSpawns()
spawner.recreate_all_spawns_once()

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
    spawn = spawner.spawns[name]
    spawn.refreshContainerInformation()
    return template('./templates/spawn', spawn=spawn, mods=spawn.list_mods())

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




run(host='0.0.0.0', port=8888, reloader=True, debug=True)