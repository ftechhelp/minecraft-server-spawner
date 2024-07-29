from bottle import route, run, template, request
from utils.spawner import Spawner

spawner = Spawner()
spawner.loadSpawns()

@route('/')
def index():
    return template('./templates/index', spawns=spawner.spawns)

@route('/spawn', method='POST')
def spawn():
    
    name = request.POST.name.strip() or None
    port = int(request.POST.port.strip()) if request.POST.port.strip() else None
    type = request.POST.type.strip() or None
    minecraft_version = request.POST.minecraft_version.strip() or None
    forge_version = request.POST.forge_version.strip() or None

    spawner.create_or_modify_spawn(name=name, new_port=port, new_type=type, new_minecraftVersion=minecraft_version, new_forgeVersion=forge_version)
    return template('./templates/index', spawns=spawner.spawns)

@route('/spawn/<name>', method='GET')
def view_spawn(name):
    return template('./templates/spawn', spawn=spawner.spawns[name])


run(host='0.0.0.0', port=8888, reloader=True, debug=True)