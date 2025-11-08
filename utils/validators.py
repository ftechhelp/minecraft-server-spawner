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
