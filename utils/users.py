import hashlib
import hmac
import json
import os
import secrets
import threading
from datetime import datetime

# All reads and writes of users.json go through this lock — the app serves
# requests on 8 waitress threads.
_users_lock = threading.Lock()

_SCRYPT_N = 16384
_SCRYPT_R = 8
_SCRYPT_P = 1

DEFAULT_EGGS = 1
ANONYMOUS_EGGS = 1


def _panel_data_dir() -> str:
    return os.environ.get("PANEL_DATA_DIR", "./panel_data")


def _users_file() -> str:
    return os.path.join(_panel_data_dir(), "users.json")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_hex, hash_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        digest = hashlib.scrypt(password.encode("utf-8"), salt=bytes.fromhex(salt_hex), n=int(n), r=int(r), p=int(p))
        return hmac.compare_digest(digest.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def _load_db() -> dict:
    try:
        with open(_users_file(), "r") as file:
            db = json.load(file)
            if isinstance(db, dict) and isinstance(db.get("users"), dict):
                return db
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return {"users": {}}


def _save_db(db: dict) -> None:
    os.makedirs(_panel_data_dir(), exist_ok=True)
    tmp_file = _users_file() + ".tmp"
    with open(tmp_file, "w") as file:
        json.dump(db, file, indent=2)
    os.replace(tmp_file, _users_file())


def _with_name(username: str, record: dict) -> dict:
    user = dict(record)
    user["name"] = username
    return user


def get_user(username: str):
    with _users_lock:
        record = _load_db()["users"].get(username)
    return _with_name(username, record) if record else None


def list_users() -> list:
    with _users_lock:
        db = _load_db()
    return [_with_name(name, record) for name, record in sorted(db["users"].items())]


def create_user(username: str, password: str, eggs: int = DEFAULT_EGGS, is_admin: bool = False, must_change_password: bool = False) -> None:
    with _users_lock:
        db = _load_db()
        if username in db["users"]:
            raise ValueError(f"User '{username}' already exists")
        db["users"][username] = {
            "password_hash": hash_password(password),
            "is_admin": bool(is_admin),
            "eggs": max(0, int(eggs)),
            "must_change_password": bool(must_change_password),
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        _save_db(db)


def set_password(username: str, password: str, must_change: bool = False) -> None:
    with _users_lock:
        db = _load_db()
        if username not in db["users"]:
            raise ValueError(f"User '{username}' does not exist")
        db["users"][username]["password_hash"] = hash_password(password)
        db["users"][username]["must_change_password"] = bool(must_change)
        _save_db(db)


def delete_user(username: str) -> None:
    with _users_lock:
        db = _load_db()
        if username not in db["users"]:
            raise ValueError(f"User '{username}' does not exist")
        del db["users"][username]
        _save_db(db)


def set_eggs(username: str, eggs: int) -> None:
    with _users_lock:
        db = _load_db()
        if username not in db["users"]:
            raise ValueError(f"User '{username}' does not exist")
        db["users"][username]["eggs"] = max(0, int(eggs))
        _save_db(db)


def set_admin(username: str, is_admin: bool) -> None:
    with _users_lock:
        db = _load_db()
        if username not in db["users"]:
            raise ValueError(f"User '{username}' does not exist")
        db["users"][username]["is_admin"] = bool(is_admin)
        _save_db(db)


def count_admins() -> int:
    with _users_lock:
        db = _load_db()
    return sum(1 for record in db["users"].values() if record.get("is_admin"))


def authenticate(username: str, password: str):
    user = get_user(username)
    if user and verify_password(password, user.get("password_hash", "")):
        return user
    return None


def bootstrap_admin() -> None:
    """Seed the first admin from ADMIN_USERNAME/ADMIN_PASSWORD, only if no users db exists yet."""
    if os.path.exists(_users_file()):
        return
    admin_username = os.environ.get("ADMIN_USERNAME", "").strip()
    admin_password = os.environ.get("ADMIN_PASSWORD", "").strip()
    if not admin_username or not admin_password:
        return
    # The env password lives in plaintext in .env, so force a rotation at first login
    create_user(admin_username, admin_password, eggs=5, is_admin=True, must_change_password=True)
    print(f"Bootstrapped admin user '{admin_username}'.")


def get_cookie_secret() -> str:
    env_secret = os.environ.get("COOKIE_SECRET", "").strip()
    if env_secret:
        return env_secret
    secret_file = os.path.join(_panel_data_dir(), ".cookie_secret")
    try:
        with open(secret_file, "r") as file:
            secret = file.read().strip()
            if secret:
                return secret
    except FileNotFoundError:
        pass
    secret = secrets.token_hex(32)
    os.makedirs(_panel_data_dir(), exist_ok=True)
    with open(secret_file, "w") as file:
        file.write(secret)
    return secret


def can_manage_spawn(user, owner) -> bool:
    """Owned spawns: owner and admins only. Unowned spawns: anyone, including anonymous."""
    if user and user.get("is_admin"):
        return True
    if owner is None:
        return True
    return user is not None and user["name"] == owner


def egg_capacity(user) -> int:
    return user["eggs"] if user else ANONYMOUS_EGGS
