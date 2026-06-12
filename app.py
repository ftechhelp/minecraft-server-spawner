from bottle import get, post, run, template as bottle_template, request, redirect, abort, BaseRequest, error, response
import bottle
from utils.spawner import Spawner
from utils import users
from utils.backup_scheduler import backup_scheduler
from utils.log_analyzer import log_analyzer, LogAnalysisError
from utils.validators import (
    validate_spawn_name,
    validate_port,
    validate_server_type,
    validate_minecraft_version,
    validate_forge_version,
    check_port_availability,
    find_next_available_port,
    validate_username,
)
from dotenv import load_dotenv
from urllib.parse import quote
import functools
import os
import atexit
import json
import threading
import time
import uuid

load_dotenv()


def env_flag(name: str, default: str = "false") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


WEB_PANEL_URL = os.environ.get('WEB_PANEL_URL', 'http://localhost:8888').strip() or 'http://localhost:8888'
SERVER_CONNECTION_HOST = os.environ.get('SERVER_CONNECTION_HOST', 'localhost').strip() or 'localhost'
IS_TEST = env_flag('IS_TEST', 'false')

users.bootstrap_admin()
COOKIE_SECRET = users.get_cookie_secret()
SESSION_MAX_AGE = 14 * 24 * 3600

# Container states that occupy an egg slot (the server is up or coming up)
OCCUPIED_STATUSES = {'running', 'restarting', 'paused', 'created'}


def current_user():
    session = request.get_cookie('session', secret=COOKIE_SECRET)
    if not isinstance(session, dict):
        return None
    if session.get('exp', 0) < time.time():
        return None
    username = session.get('u')
    return users.get_user(username) if username else None


def render_template(template_path: str, **kwargs):
    user = current_user()
    owner = user['name'] if user else None
    # Cached statuses only — the egg-enforcement path does the fresh docker check
    eggs_used = sum(1 for s in spawner.spawns.values() if s.owner == owner and s.get_status() in OCCUPIED_STATUSES)
    template_context = {
        'web_panel_url': WEB_PANEL_URL,
        'server_connection_host': SERVER_CONNECTION_HOST,
        'server_connection_example': f'{SERVER_CONNECTION_HOST}:25565',
        'is_test': IS_TEST,
        'user': user,
        'eggs_total': users.egg_capacity(user),
        'eggs_used': eggs_used,
    }
    template_context.update(kwargs)
    return bottle_template(template_path, **template_context)


def require_spawn_permission(handler):
    @functools.wraps(handler)
    def wrapper(name, *args, **kwargs):
        spawn = spawner.spawns.get(name)
        if spawn is None:
            abort(404, f"Unknown server '{name}'")
        user = current_user()
        if not users.can_manage_spawn(user, spawn.owner):
            message = f"This server is owned by {spawn.owner}. Log in as the owner or an admin to manage it."
            accept_header = request.get_header('Accept') or ''
            is_ajax_request = request.get_header('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in accept_header
            if is_ajax_request:
                response.content_type = 'application/json'
                response.status = 403
                return json.dumps({'ok': False, 'error': message})
            if user is None:
                redirect(f"/login?next={quote(f'/spawn/{name}')}")
            abort(403, message)
        return handler(name, *args, **kwargs)
    return wrapper


def require_admin(handler):
    @functools.wraps(handler)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            redirect(f"/login?next={quote(request.path)}")
        if not user.get('is_admin'):
            abort(403, 'Admin access required.')
        return handler(*args, **kwargs)
    return wrapper


# Held across capacity check + container start so two simultaneous requests
# can't both pass the check with one free slot.
_capacity_lock = threading.Lock()


def check_egg_capacity(owner, exclude_spawn=None):
    """Can the owner (username, or None for the shared anonymous slot) run one more server?"""
    if owner:
        owner_user = users.get_user(owner)
        capacity = owner_user['eggs'] if owner_user else users.DEFAULT_EGGS
    else:
        capacity = users.ANONYMOUS_EGGS
    used = 0
    for spawn in spawner.spawns.values():
        if spawn.owner != owner:
            continue
        if exclude_spawn is not None and spawn.name == exclude_spawn.name:
            continue
        spawn.refreshContainerInformation()
        if spawn.get_status() in OCCUPIED_STATUSES:
            used += 1
    if used >= capacity:
        if owner is None:
            return False, "The shared anonymous egg is in use — only one unowned server can run at a time. Log in to use your own eggs."
        return False, f"All {capacity} of {owner}'s egg(s) are in use ({used} running). Stop a server first, or have an admin raise the egg balance."
    return True, None

# Allow large multi-file uploads (e.g., a folder of .jar mods)
# Default is ~100KB; increase to 512MB to support mod folder uploads
UPLOAD_MEMFILE_MAX = 512 * 1024 * 1024
BaseRequest.MEMFILE_MAX = UPLOAD_MEMFILE_MAX
bottle.BaseRequest.MEMFILE_MAX = UPLOAD_MEMFILE_MAX
bottle.LocalRequest.MEMFILE_MAX = UPLOAD_MEMFILE_MAX

spawner = Spawner()
spawner.loadSpawns()
spawner.ensure_all_spawns_up()

# Start backup scheduler
backup_scheduler.start(spawner)
atexit.register(backup_scheduler.stop)

def render_index(create_error=None, create_form=None):
    user = current_user()
    can_manage = {name: users.can_manage_spawn(user, spawn.owner) for name, spawn in spawner.spawns.items()}
    return render_template(
        './templates/index',
        spawns=spawner.spawns,
        can_manage=can_manage,
        create_error=create_error,
        create_form=create_form or {},
        page_error=request.query.get('error', '').strip(),
    )


def local_redirect_target(default: str) -> str:
    target = request.POST.get('redirect', '').strip()
    if target.startswith('/') and not target.startswith('//'):
        return target
    return default


@get('/')
def index():
    spawner.loadSpawns()
    return render_index()


@get('/login')
def login_page():
    if current_user():
        redirect('/')
    return render_template('./templates/login', login_error=None, next_url=request.query.get('next', '/'))


@post('/login')
def login_submit():
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    next_url = request.POST.get('next', '/').strip() or '/'
    if not next_url.startswith('/'):
        next_url = '/'
    user = users.authenticate(username, password)
    if user is None:
        return render_template('./templates/login', login_error='Invalid username or password', next_url=next_url)
    session = {'u': user['name'], 'exp': int(time.time()) + SESSION_MAX_AGE}
    response.set_cookie('session', session, secret=COOKIE_SECRET, max_age=SESSION_MAX_AGE, httponly=True, path='/', samesite='lax')
    redirect(next_url)


@post('/logout')
def logout():
    response.delete_cookie('session', path='/')
    redirect('/')

@get('/docs')
def documentation():
    return render_template('./templates/documentation')


@get('/backups')
def archived_backups():
    spawner.loadSpawns()
    archived = spawner.list_archived_backups()
    notice = request.query.get('notice', '').strip()
    page_error = request.query.get('error', '').strip()
    return render_template('./templates/archived_backups', archived_backups=archived, notice=notice, page_error=page_error)

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
            return render_index(create_error=name_error, create_form=create_form)

        if spawner.spawn_name_exists(name):
            return render_index(create_error=f"Spawn name '{name}' already exists", create_form=create_form)

        if spawner.spawn_directory_exists(name):
            return render_index(create_error=f"Spawn directory for '{name}' already exists on disk", create_form=create_form)

    if raw_port:
        valid_port, port, port_error = validate_port(raw_port)
        if not valid_port:
            return render_index(create_error=port_error, create_form=create_form)

        is_port_available, port_conflict_error = check_port_availability(port, spawner)
        if not is_port_available:
            return render_index(create_error=port_conflict_error, create_form=create_form)
    else:
        port = find_next_available_port(spawner)
        if port is None:
            return render_index(create_error="No available ports left in the allowed range (25565-25665)", create_form=create_form)

    valid_type, server_type, type_error = validate_server_type(raw_type)
    if not valid_type:
        return render_index(create_error=type_error, create_form=create_form)

    minecraft_version_input = raw_minecraft_version or 'LATEST'
    valid_version, minecraft_version, version_error = validate_minecraft_version(minecraft_version_input)
    if not valid_version:
        return render_index(create_error=version_error, create_form=create_form)

    forge_version_input = raw_forge_version or 'LATEST'
    valid_forge, forge_version, forge_error = validate_forge_version(forge_version_input, server_type)
    if not valid_forge:
        return render_index(create_error=forge_error, create_form=create_form)

    user = current_user()
    owner = user['name'] if user else None
    with _capacity_lock:
        capacity_ok, egg_error = check_egg_capacity(owner)
        if not capacity_ok:
            return render_index(create_error=egg_error, create_form=create_form)

        try:
            new_spawn = spawner.create_or_modify_spawn(name=name, new_port=port, new_type=server_type, new_minecraftVersion=minecraft_version, new_forgeVersion=forge_version)
        except Exception as exc:
            return render_index(create_error=f"Failed to create server: {str(exc)}", create_form=create_form)

        new_spawn.set_owner(owner)

    redirect("/")

@get('/spawn/<name>')
def view_spawn(name):
    from datetime import datetime
    from zoneinfo import ZoneInfo
    spawn = spawner.spawns.get(name)
    if spawn is None:
        abort(404, f"Unknown server '{name}'")
    spawn.refreshContainerInformation()
    spawn.reload_backup_settings()
    tz = ZoneInfo("America/Vancouver")
    default_backup_name = f"backup_{datetime.now(tz=tz).strftime('%Y%m%d_%H%M%S')}"
    server_status = spawn.get_server_status() or {}
    players = server_status.get("players") if isinstance(server_status, dict) else {}
    player_count = players.get("online") if isinstance(players, dict) else None
    player_capacity = players.get("max") if isinstance(players, dict) else None
    return render_template(
        './templates/spawn',
        spawn=spawn,
        mods=spawn.list_mods(),
        default_backup_name=default_backup_name,
        player_count=player_count,
        player_capacity=player_capacity,
        can_manage=users.can_manage_spawn(current_user(), spawn.owner),
        page_error=request.query.get('error', '').strip(),
    )

@post('/spawn/<name>/recreate')
@require_spawn_permission
def recreate_spawn(name):
    spawn = spawner.spawns[name]
    with _capacity_lock:
        spawn.refreshContainerInformation()
        if spawn.get_status() not in OCCUPIED_STATUSES:
            # Recreating a stopped server brings it up, so it needs a free egg
            capacity_ok, egg_error = check_egg_capacity(spawn.owner, exclude_spawn=spawn)
            if not capacity_ok:
                redirect(f"/spawn/{name}?error={quote(egg_error)}")
        spawn.up()
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/start')
@require_spawn_permission
def start_spawn(name):
    spawn = spawner.spawns[name]
    redirect_to = local_redirect_target(f"/spawn/{name}")
    with _capacity_lock:
        spawn.refreshContainerInformation()
        if spawn.get_status() not in OCCUPIED_STATUSES:
            capacity_ok, egg_error = check_egg_capacity(spawn.owner, exclude_spawn=spawn)
            if not capacity_ok:
                redirect(f"{redirect_to}?error={quote(egg_error)}")
        spawn.start()
    redirect(redirect_to)

@post('/spawn/<name>/stop')
@require_spawn_permission
def stop_spawn(name):
    spawn = spawner.spawns[name]
    spawn.stop()
    redirect(local_redirect_target(f"/spawn/{name}"))

@post('/spawn/<name>/claim')
def claim_spawn(name):
    spawn = spawner.spawns.get(name)
    if spawn is None:
        abort(404, f"Unknown server '{name}'")
    user = current_user()
    if user is None:
        redirect(f"/login?next={quote(f'/spawn/{name}')}")
    redirect_to = local_redirect_target(f"/spawn/{name}")
    with _capacity_lock:
        if spawn.owner:
            redirect(f"{redirect_to}?error={quote(f'This server is already owned by {spawn.owner}.')}")
        spawn.refreshContainerInformation()
        if spawn.get_status() in OCCUPIED_STATUSES:
            # A running unowned server occupies the shared anonymous egg; once
            # claimed it occupies one of the new owner's eggs instead
            capacity_ok, egg_error = check_egg_capacity(user['name'])
            if not capacity_ok:
                redirect(f"{redirect_to}?error={quote(f'Claiming this running server needs a free egg. {egg_error}')}")
        spawn.set_owner(user['name'])
    redirect(redirect_to)

@post('/spawn/<name>/delete')
@require_spawn_permission
def delete_spawn(name):
    spawner.loadSpawns()
    spawn = spawner.spawns[name]

    archive_notice = ''
    archive_success, archive_message, _ = spawn.archive_latest_backup(spawner.archived_backups_dir)
    if archive_success:
        archive_notice = f"Latest backup archived before deleting '{name}'."
    else:
        archive_notice = f"Deleted '{name}'. No archived backup was created ({archive_message})."

    spawn.purge()
    spawner.loadSpawns()
    redirect(f"/backups?notice={archive_notice}")

@post('/spawn/<name>/refresh')
@require_spawn_permission
def refresh_spawn(name):
    spawn = spawner.spawns[name]
    spawn.refreshContainerInformation()
    redirect(f"/spawn/{name}")

@get('/spawn/<name>/logs')
def download_logs(name):
    spawn = spawner.spawns[name]
    return render_template('./templates/spawn_logs', logs=spawn.get_logs())

@get('/spawn/<name>/logs/content')
def get_logs_content(name):
    spawn = spawner.spawns[name]
    spawn.refreshContainerInformation()
    return spawn.get_logs()

@post('/spawn/<name>/logs/analyze')
@require_spawn_permission
def analyze_logs(name):
    spawn = spawner.spawns[name]
    spawn.refreshContainerInformation()
    response.content_type = 'application/json'

    try:
        analysis = log_analyzer.analyze(spawn)
        return json.dumps({'ok': True, 'analysis': analysis})
    except LogAnalysisError as exc:
        response.status = 400
        return json.dumps({'ok': False, 'error': str(exc)})
    except Exception as exc:
        response.status = 500
        return json.dumps({'ok': False, 'error': f'Unexpected analysis failure: {str(exc)}'})

@get('/spawn/<name>/status')
def get_spawn_status(name):
    spawn = spawner.spawns[name]
    spawn.refreshContainerInformation()
    status = spawn.get_status()
    server_status = spawn.get_server_status() or {}
    players = server_status.get('players') if isinstance(server_status, dict) else {}
    player_count = players.get('online') if isinstance(players, dict) else None
    player_capacity = players.get('max') if isinstance(players, dict) else None
    response.content_type = 'application/json'
    return json.dumps({'status': status, 'player_count': player_count, 'player_capacity': player_capacity})

@post('/spawn/<name>/mods/delete')
@require_spawn_permission
def delete_mod(name):
    spawn = spawner.spawns[name]
    mod_filename = request.POST.mod.strip()
    spawn.remove_mod_file(mod_filename)
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/mods/delete-all')
@require_spawn_permission
def delete_all_mods(name):
    spawn = spawner.spawns[name]
    spawn.remove_all_mod_files()
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/mods/add-file')
@require_spawn_permission
def add_mod_file(name):
    spawn = spawner.spawns[name]
    accept_header = request.get_header('Accept') or ''
    is_ajax_request = request.get_header('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in accept_header
    mod_upload = request.files.get('mod')
    if mod_upload:
        spawn.add_mod_file(mod_upload)
        if is_ajax_request:
            response.content_type = 'application/json'
            return json.dumps({'ok': True, 'redirect_url': f"/spawn/{name}"})
    elif is_ajax_request:
        response.content_type = 'application/json'
        response.status = 400
        return json.dumps({'ok': False, 'error': 'No mod file was received for upload.'})
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/mods/replace/start')
@require_spawn_permission
def start_replace_mods_batch(name):
    spawn = spawner.spawns[name]
    response.content_type = 'application/json'

    try:
        batch_id = str(uuid.uuid4())
        spawn.start_mod_upload_batch(batch_id)
        return json.dumps({'ok': True, 'batch_id': batch_id})
    except Exception as exc:
        response.status = 500
        return json.dumps({'ok': False, 'error': str(exc)})

@post('/spawn/<name>/mods/replace/file')
@require_spawn_permission
def stage_replace_mod_file(name):
    spawn = spawner.spawns[name]
    response.content_type = 'application/json'

    batch_id = (request.forms.get('batch_id') or '').strip()
    mod_upload = request.files.get('mod')

    if not batch_id:
        response.status = 400
        return json.dumps({'ok': False, 'error': 'Missing upload batch id.'})

    if not mod_upload:
        response.status = 400
        return json.dumps({'ok': False, 'error': 'No mod file was received for upload.'})

    try:
        spawn.stage_mod_upload_file(batch_id, mod_upload)
        return json.dumps({'ok': True})
    except Exception as exc:
        response.status = 500
        return json.dumps({'ok': False, 'error': str(exc)})

@post('/spawn/<name>/mods/replace/commit')
@require_spawn_permission
def commit_replace_mods_batch(name):
    spawn = spawner.spawns[name]
    response.content_type = 'application/json'

    batch_id = (request.forms.get('batch_id') or '').strip()
    if not batch_id:
        response.status = 400
        return json.dumps({'ok': False, 'error': 'Missing upload batch id.'})

    try:
        spawn.commit_mod_upload_batch(batch_id)
        return json.dumps({'ok': True, 'redirect_url': f"/spawn/{name}"})
    except Exception as exc:
        response.status = 500
        return json.dumps({'ok': False, 'error': str(exc)})

@post('/spawn/<name>/mods/replace')
@require_spawn_permission
def replace_mods(name):
    spawn = spawner.spawns[name]
    accept_header = request.get_header('Accept') or ''
    is_ajax_request = request.get_header('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in accept_header
    print(f"[replace_mods route] Processing replace for {name}")
    try:
        uploads = request.files.getall('mods')
        print(f"[replace_mods route] Got {len(uploads)} files via getall")
    except Exception as e:
        print(f"[replace_mods route] getall failed: {e}, trying get")
        try:
            up = request.files.get('mods')
            uploads = [up] if up else []
            print(f"[replace_mods route] Got {len(uploads)} files via get")
        except Exception as inner_exc:
            print(f"[replace_mods route] get fallback failed: {inner_exc}")
            if is_ajax_request:
                response.content_type = 'application/json'
                response.status = 413 if 'Memory limit reached' in str(inner_exc) else 400
                return json.dumps({'ok': False, 'error': str(inner_exc)})
            raise
    
    if not uploads:
        print(f"[replace_mods route] WARNING: No files received!")
        if is_ajax_request:
            response.content_type = 'application/json'
            response.status = 400
            return json.dumps({'ok': False, 'error': 'No files were received for upload.'})
    
    try:
        spawn.replace_mods_from_uploads(uploads)
    except Exception as exc:
        if is_ajax_request:
            response.content_type = 'application/json'
            response.status = 500
            return json.dumps({'ok': False, 'error': str(exc)})
        raise

    if is_ajax_request:
        response.content_type = 'application/json'
        return json.dumps({'ok': True, 'redirect_url': f"/spawn/{name}"})
    redirect(f"/spawn/{name}")

# Deprecated: zip-based import; kept for compatibility if still used
@post('/spawn/<name>/mods/upload')
@require_spawn_permission
def upload_mod(name):
    spawn = spawner.spawns[name]
    # No-op or translate zip uploads in future
    redirect(f"/spawn/{name}")


@post('/spawn/<name>/server_properties/save')
@require_spawn_permission
def save_server_properties(name):
    spawn = spawner.spawns[name]
    spawn.write_server_properties(request.POST.server_properties)
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/console/send')
@require_spawn_permission
def send_console_command(name):
    spawn = spawner.spawns[name]
    spawn.send_console_command(request.POST.consoleCommand)
    redirect(f"/spawn/{name}")


# --- Backup Management Routes ---
@post('/spawn/<name>/backup/create')
@require_spawn_permission
def create_backup(name):
    spawn = spawner.spawns[name]
    backup_name = request.forms.get('backup_name', '').strip()
    backup_name = backup_name if backup_name else None
    success, message, backup_file = spawn.create_backup(backup_name, is_scheduled=False)
    # Redirect back to spawn page (backup creation happens in background)
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/backup/restore/<backup_name>')
@require_spawn_permission
def restore_backup(name, backup_name):
    spawn = spawner.spawns[name]
    success, message = spawn.restore_backup(backup_name)
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/backup/delete/<backup_name>')
@require_spawn_permission
def delete_backup(name, backup_name):
    spawn = spawner.spawns[name]
    success, message = spawn.delete_backup(backup_name)
    redirect(f"/spawn/{name}")

@post('/spawn/<name>/backup/settings')
@require_spawn_permission
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


@post('/backups/restore')
def restore_archived_backup():
    spawner.loadSpawns()
    archive_filename = request.forms.get('backup_file', '').strip()
    restored_name = request.forms.get('restored_name', '').strip() or None

    if not archive_filename:
        redirect('/backups?error=No archived backup selected for restore')

    user = current_user()
    owner = user['name'] if user else None
    with _capacity_lock:
        capacity_ok, egg_error = check_egg_capacity(owner)
        if not capacity_ok:
            redirect(f"/backups?error={quote(egg_error)}")

        success, message, new_spawn_name = spawner.restore_archived_backup(archive_filename, restored_name, owner=owner)
    if not success:
        redirect(f"/backups?error={message}")

    redirect(f"/spawn/{new_spawn_name}")


@post('/backups/delete')
def delete_archived_backup():
    archive_filename = request.forms.get('backup_file', '').strip()
    if not archive_filename:
        redirect('/backups?error=No archived backup selected for deletion')

    success, message = spawner.delete_archived_backup(archive_filename)
    if not success:
        redirect(f"/backups?error={message}")

    redirect('/backups?notice=Archived backup deleted permanently')


# --- Admin Routes ---
@get('/admin')
@require_admin
def admin_page():
    return render_template(
        './templates/admin',
        users_list=users.list_users(),
        notice=request.query.get('notice', '').strip(),
        page_error=request.query.get('error', '').strip(),
    )


@post('/admin/users/create')
@require_admin
def admin_create_user():
    username_raw = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    eggs_raw = request.POST.get('eggs', '').strip()
    is_admin = 'is_admin' in request.POST

    valid, username, username_error = validate_username(username_raw)
    if not valid:
        redirect(f"/admin?error={quote(username_error)}")
    if not password:
        redirect('/admin?error=Password cannot be empty')
    try:
        eggs = int(eggs_raw) if eggs_raw else users.DEFAULT_EGGS
        if eggs < 0:
            raise ValueError
    except ValueError:
        redirect('/admin?error=Eggs must be a number of 0 or more')

    try:
        users.create_user(username, password, eggs=eggs, is_admin=is_admin)
    except ValueError as exc:
        redirect(f"/admin?error={quote(str(exc))}")

    redirect(f"/admin?notice={quote(f'User {username} created with {eggs} egg(s)')}")


@post('/admin/users/<username>/delete')
@require_admin
def admin_delete_user(username):
    actor = current_user()
    target = users.get_user(username)
    if target is None:
        redirect(f"/admin?error={quote(f'User {username} does not exist')}")
    if username == actor['name']:
        redirect('/admin?error=You cannot delete your own account')
    if target.get('is_admin') and users.count_admins() <= 1:
        redirect('/admin?error=Cannot delete the last admin')

    users.delete_user(username)
    # Orphaned servers become unowned (manageable by anyone) instead of locked
    for spawn in spawner.spawns.values():
        if spawn.owner == username:
            spawn.set_owner(None)

    redirect(f"/admin?notice={quote(f'User {username} deleted; their servers are now unowned')}")


@post('/admin/users/<username>/eggs')
@require_admin
def admin_set_eggs(username):
    try:
        eggs = int(request.POST.get('eggs', '').strip())
        if eggs < 0:
            raise ValueError
    except ValueError:
        redirect('/admin?error=Eggs must be a number of 0 or more')

    try:
        users.set_eggs(username, eggs)
    except ValueError as exc:
        redirect(f"/admin?error={quote(str(exc))}")

    redirect(f"/admin?notice={quote(f'{username} now has {eggs} egg(s)')}")


@post('/admin/users/<username>/toggle-admin')
@require_admin
def admin_toggle_admin(username):
    target = users.get_user(username)
    if target is None:
        redirect(f"/admin?error={quote(f'User {username} does not exist')}")
    if target.get('is_admin') and users.count_admins() <= 1:
        redirect('/admin?error=Cannot demote the last admin')

    users.set_admin(username, not target.get('is_admin'))
    role = 'an admin' if not target.get('is_admin') else 'a regular user'
    redirect(f"/admin?notice={quote(f'{username} is now {role}')}")


@error(403)
def error403(err):
    details = getattr(err, 'body', '') or 'You do not have permission to do this.'
    return render_template(
        './templates/error',
        status_code=403,
        title='Permission denied',
        friendly_message="Oups... Uncle Vince says this server belongs to someone else.",
        details=details,
    )


@error(404)
def error404(err):
    return render_template(
        './templates/error',
        status_code=404,
        title='Page not found',
        friendly_message="Oups... Uncle Vince looked in all the usual places, but this page isn't here.",
        details=f"Path: {request.path}",
    )


@error(500)
def error500(err):
    exception_obj = getattr(err, 'exception', None)
    details = str(exception_obj) if exception_obj else str(err)
    details = details or 'No exception details were captured.'

    return render_template(
        './templates/error',
        status_code=500,
        title='Unexpected server error',
        friendly_message='Oups... Uncle Vince has seen many different outcomes, but not this one yet.',
        details=details,
    )


if __name__ == '__main__':
    # waitress: threaded, buffers slow clients off the worker threads, and
    # drops stalled connections (channel_timeout). The default wsgiref server
    # is single-threaded with no socket timeout, so one stalled client wedged
    # the whole panel in recvfrom.
    run(
        host='0.0.0.0',
        port=8888,
        server='waitress',
        threads=8,
        reloader=env_flag('BOTTLE_RELOADER', 'false'),
        debug=env_flag('BOTTLE_DEBUG', 'false'),
    )