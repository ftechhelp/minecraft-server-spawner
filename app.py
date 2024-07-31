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
    return template('./templates/index', spawns=spawner.spawns)

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




run(host='0.0.0.0', port=8888, reloader=True, debug=True)