"""
Input validation module for Minecraft server management application.
Provides validation functions for ports, spawn names, versions, and mods.
"""

import re
import os
from typing import Tuple, Optional


def validate_port(port: str) -> Tuple[bool, Optional[int], str]:
    """
    Validates port numbers for spawn creation.
    
    Args:
        port: Port number as string
        
    Returns:
        Tuple of (is_valid, validated_port, error_message)
        - is_valid: True if port is valid
        - validated_port: Integer port number if valid, None otherwise
        - error_message: Empty string if valid, error description otherwise
    """
    if not port:
        return False, None, "Port number is required"
    
    # Check if port is numeric
    try:
        port_int = int(port)
    except (ValueError, TypeError):
        return False, None, "Port must be a valid number"
    
    # Check port range (1-65535)
    if port_int < 1 or port_int > 65535:
        return False, None, "Port must be between 1 and 65535"
    
    return True, port_int, ""


def validate_spawn_name(name: str) -> Tuple[bool, str, str]:
    """
    Validates spawn names to prevent path traversal and invalid characters.
    
    Args:
        name: Spawn name to validate
        
    Returns:
        Tuple of (is_valid, validated_name, error_message)
        - is_valid: True if name is valid
        - validated_name: Sanitized name if valid, empty string otherwise
        - error_message: Empty string if valid, error description otherwise
    """
    if not name or not name.strip():
        return False, "", "Spawn name is required"
    
    name = name.strip()
    
    # Check for path traversal attempts
    if ".." in name or "/" in name or "\\" in name:
        return False, "", "Spawn name cannot contain path traversal characters (.. / \\)"
    
    # Check for invalid characters (allow alphanumeric, hyphens, underscores)
    if not re.match(r'^[a-zA-Z0-9_-]+$', name):
        return False, "", "Spawn name can only contain letters, numbers, hyphens, and underscores"
    
    # Check length (reasonable limits)
    if len(name) > 64:
        return False, "", "Spawn name must be 64 characters or less"
    
    if len(name) < 1:
        return False, "", "Spawn name must be at least 1 character"
    
    return True, name, ""


def validate_minecraft_version(version: str) -> Tuple[bool, str, str]:
    """
    Validates Minecraft version strings.
    
    Args:
        version: Minecraft version string
        
    Returns:
        Tuple of (is_valid, validated_version, error_message)
        - is_valid: True if version is valid
        - validated_version: Version string if valid, empty string otherwise
        - error_message: Empty string if valid, error description otherwise
    """
    if not version or not version.strip():
        return False, "", "Minecraft version is required"
    
    version = version.strip()
    
    # Allow "LATEST" as a special case
    if version.upper() == "LATEST":
        return True, "LATEST", ""
    
    # Validate version format (e.g., 1.19.2, 1.20, 1.16.5)
    # Pattern: one or more digits, followed by dot and digits, optionally repeated
    if not re.match(r'^\d+\.\d+(\.\d+)?$', version):
        return False, "", "Minecraft version must be in format X.Y or X.Y.Z (e.g., 1.19.2) or 'LATEST'"
    
    return True, version, ""


def validate_mod_name(mod: str) -> Tuple[bool, str, str]:
    """
    Validates mod identifiers/slugs for CurseForge.
    
    Args:
        mod: Mod identifier/slug
        
    Returns:
        Tuple of (is_valid, validated_mod, error_message)
        - is_valid: True if mod is valid
        - validated_mod: Mod slug if valid, empty string otherwise
        - error_message: Empty string if valid, error description otherwise
    """
    if not mod or not mod.strip():
        return False, "", "Mod identifier is required"
    
    mod = mod.strip()
    
    # CurseForge project slugs typically contain lowercase letters, numbers, and hyphens
    if not re.match(r'^[a-z0-9-]+$', mod):
        return False, "", "Mod identifier can only contain lowercase letters, numbers, and hyphens"
    
    # Check reasonable length
    if len(mod) > 128:
        return False, "", "Mod identifier must be 128 characters or less"
    
    if len(mod) < 1:
        return False, "", "Mod identifier must be at least 1 character"
    
    return True, mod, ""


def check_port_availability(port: int, spawner, exclude_spawn: Optional[str] = None) -> Tuple[bool, str]:
    """
    Checks if a port is available (not used by other spawns).
    
    Args:
        port: Port number to check
        spawner: Spawner instance containing all spawns
        exclude_spawn: Optional spawn name to exclude from check (for modifications)
        
    Returns:
        Tuple of (is_available, error_message)
        - is_available: True if port is available
        - error_message: Empty string if available, conflict description otherwise
    """
    for spawn_name, spawn in spawner.spawns.items():
        # Skip the spawn being modified
        if exclude_spawn and spawn_name == exclude_spawn:
            continue
        
        # Check if port conflicts
        if spawn.port == port:
            return False, f"Port {port} is already in use by spawn '{spawn_name}'"
    
    return True, ""


def validate_file_size(file_path: str, max_size_mb: int = 100) -> Tuple[bool, str]:
    """
    Validates that a file does not exceed the maximum size limit.
    
    Args:
        file_path: Path to the file to check
        max_size_mb: Maximum file size in megabytes (default: 100MB)
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if file size is within limits
        - error_message: Empty string if valid, error description otherwise
    """
    try:
        file_size = os.path.getsize(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            size_mb = file_size / (1024 * 1024)
            return False, f"File size ({size_mb:.2f}MB) exceeds maximum allowed size of {max_size_mb}MB"
        
        return True, ""
        
    except OSError as e:
        return False, f"Unable to check file size: {str(e)}"


def check_disk_space(path: str = ".", min_space_gb: float = 5.0) -> Tuple[bool, str]:
    """
    Checks if sufficient disk space is available at the specified path.
    
    Args:
        path: Path to check disk space for (default: current directory)
        min_space_gb: Minimum required space in gigabytes (default: 5GB)
        
    Returns:
        Tuple of (is_sufficient, error_message)
        - is_sufficient: True if sufficient space is available
        - error_message: Empty string if sufficient, error description otherwise
    """
    try:
        import shutil
        stat = shutil.disk_usage(path)
        free_gb = stat.free / (1024 ** 3)
        
        if free_gb < min_space_gb:
            return False, f"Insufficient disk space: {free_gb:.2f}GB available, {min_space_gb}GB required"
        
        return True, ""
        
    except Exception as e:
        return False, f"Unable to check disk space: {str(e)}"


def check_docker_available() -> Tuple[bool, str]:
    """
    Checks if Docker daemon is running and accessible.
    
    Returns:
        Tuple of (is_available, error_message)
        - is_available: True if Docker is available
        - error_message: Empty string if available, error description otherwise
    """
    try:
        from python_on_whales import docker
        # Try to get Docker version as a simple check
        docker.version()
        return True, ""
    except Exception as e:
        error_msg = str(e).lower()
        if "connection" in error_msg or "refused" in error_msg or "not found" in error_msg:
            return False, "Docker daemon is not running or not accessible. Please start Docker and try again."
        return False, f"Docker is not available: {str(e)}"
