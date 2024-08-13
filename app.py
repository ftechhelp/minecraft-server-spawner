from bottle import get, post, run, template, request, redirect
from utils.spawner import Spawner
from dotenv import load_dotenv
import os

load_dotenv()

spawner = Spawner()
spawner.loadSpawns()

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
    return template('./templates/spawn', spawn=spawner.spawns[name])

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
    mod = request.POST.mod.strip()
    spawn.removeMod(mod)
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/mods/add')
def add_mod(name):
    spawn = spawner.spawns[name]
    mod = request.POST.mod.strip()
    spawn.addMod(mod)
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/mods/sync')
def sync_mods(name):
    spawn = spawner.spawns[name]
    spawn.syncMods()
    spawner.create_or_modify_spawn(name=spawn.name, new_port=spawn.port, new_type=spawn.type, new_minecraftVersion=spawn.minecraft_version, new_forgeVersion=spawn.forge_version, mods=spawn.mods)
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/server_properties/save')
def save_server_properties(name):
    spawn = spawner.spawns[name]
    spawn.write_server_properties(request.POST.server_properties)
    redirect(f"/spawn/{name}")




run(host='0.0.0.0', port=8888, reloader=True, debug=True)