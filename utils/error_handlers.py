"""
Error handling infrastructure for the Minecraft server management application.

This module provides custom exception classes and decorator functions for
consistent error handling across the application.
"""

import logging
import functools
from typing import Callable, Any
from bottle import HTTPError, redirect, request


# Get logger (configuration is done in app.py)
logger = logging.getLogger(__name__)


# Custom Exception Classes

class SpawnNotFoundError(Exception):
    """Raised when a spawn does not exist in the spawns dictionary."""
    
    def __init__(self, spawn_name: str, message: str = None):
        self.spawn_name = spawn_name
        self.message = message or f"Spawn '{spawn_name}' not found"
        super().__init__(self.message)


class ValidationError(Exception):
    """Raised when input validation fails."""
    
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.value = value
        self.message = message
        super().__init__(f"Validation error for '{field}': {message}")


class DockerOperationError(Exception):
    """Raised when a Docker operation fails."""
    
    def __init__(self, operation: str, message: str, spawn_name: str = None):
        self.operation = operation
        self.spawn_name = spawn_name
        self.message = message
        error_msg = f"Docker operation '{operation}' failed"
        if spawn_name:
            error_msg += f" for spawn '{spawn_name}'"
        error_msg += f": {message}"
        super().__init__(error_msg)


class FileOperationError(Exception):
    """Raised when a file operation fails."""
    
    def __init__(self, operation: str, filepath: str, message: str):
        self.operation = operation
        self.filepath = filepath
        self.message = message
        super().__init__(f"File operation '{operation}' failed for '{filepath}': {message}")


class ResourceConstraintError(Exception):
    """Raised when system resources are insufficient."""
    
    def __init__(self, resource_type: str, message: str):
        self.resource_type = resource_type
        self.message = message
        super().__init__(f"Resource constraint ({resource_type}): {message}")


# Decorator Functions

def handle_spawn_not_found(func: Callable) -> Callable:
    """
    Decorator to handle SpawnNotFoundError and KeyError exceptions.
    Returns HTTP 404 error page when spawn is not found.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SpawnNotFoundError as e:
            logger.error(f"Spawn not found: {e.spawn_name} - {request.path}")
            # Set flash message
            session = request.environ.get('beaker.session')
            if session:
                if 'flash_messages' not in session:
                    session['flash_messages'] = []
                session['flash_messages'].append({
                    'message': f"Spawn '{e.spawn_name}' not found. It may have been deleted or never existed.",
                    'type': 'danger'
                })
                session.save()
            raise HTTPError(
                404,
                f"Spawn '{e.spawn_name}' not found. It may have been deleted or never existed."
            )
        except KeyError as e:
            spawn_name = str(e).strip("'\"")
            logger.error(f"Spawn not found (KeyError): {spawn_name} - {request.path}")
            # Set flash message
            session = request.environ.get('beaker.session')
            if session:
                if 'flash_messages' not in session:
                    session['flash_messages'] = []
                session['flash_messages'].append({
                    'message': f"Spawn '{spawn_name}' not found. It may have been deleted or never existed.",
                    'type': 'danger'
                })
                session.save()
            raise HTTPError(
                404,
                f"Spawn '{spawn_name}' not found. It may have been deleted or never existed."
            )
    return wrapper


def handle_docker_errors(func: Callable) -> Callable:
    """
    Decorator to handle Docker-related exceptions.
    Returns HTTP 500 error with user-friendly message.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DockerOperationError as e:
            logger.error(
                f"Docker operation failed: {e.operation} - "
                f"Spawn: {e.spawn_name} - Path: {request.path} - Error: {e.message}",
                exc_info=True
            )
            # Set flash message
            session = request.environ.get('beaker.session')
            if session:
                if 'flash_messages' not in session:
                    session['flash_messages'] = []
                session['flash_messages'].append({
                    'message': f"Docker operation failed: {e.message}. Please ensure Docker is running and try again.",
                    'type': 'danger'
                })
                session.save()
            raise HTTPError(
                500,
                f"Docker operation failed: {e.message}. "
                "Please ensure Docker is running and try again."
            )
        except Exception as e:
            # Catch generic Docker-related exceptions
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['docker', 'container', 'compose']):
                logger.error(
                    f"Docker-related error: {request.path} - {str(e)}",
                    exc_info=True
                )
                # Set flash message
                session = request.environ.get('beaker.session')
                if session:
                    if 'flash_messages' not in session:
                        session['flash_messages'] = []
                    session['flash_messages'].append({
                        'message': f"Docker operation failed: {str(e)}. Please ensure Docker is running and try again.",
                        'type': 'danger'
                    })
                    session.save()
                raise HTTPError(
                    500,
                    f"Docker operation failed: {str(e)}. "
                    "Please ensure Docker is running and try again."
                )
            raise
    return wrapper


def handle_file_errors(func: Callable) -> Callable:
    """
    Decorator to handle file operation exceptions.
    Returns HTTP 500 error with user-friendly message.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileOperationError as e:
            logger.error(
                f"File operation failed: {e.operation} - "
                f"File: {e.filepath} - Path: {request.path} - Error: {e.message}",
                exc_info=True
            )
            # Set flash message
            session = request.environ.get('beaker.session')
            if session:
                if 'flash_messages' not in session:
                    session['flash_messages'] = []
                session['flash_messages'].append({
                    'message': f"File operation failed: {e.message}. Please check file permissions and disk space.",
                    'type': 'danger'
                })
                session.save()
            raise HTTPError(
                500,
                f"File operation failed: {e.message}. "
                "Please check file permissions and disk space."
            )
        except FileNotFoundError as e:
            logger.error(
                f"File not found: {request.path} - {str(e)}",
                exc_info=True
            )
            # Set flash message
            session = request.environ.get('beaker.session')
            if session:
                if 'flash_messages' not in session:
                    session['flash_messages'] = []
                session['flash_messages'].append({
                    'message': f"Required file not found: {str(e)}. The file may have been deleted or moved.",
                    'type': 'danger'
                })
                session.save()
            raise HTTPError(
                500,
                f"Required file not found: {str(e)}. "
                "The file may have been deleted or moved."
            )
        except PermissionError as e:
            logger.error(
                f"Permission denied: {request.path} - {str(e)}",
                exc_info=True
            )
            # Set flash message
            session = request.environ.get('beaker.session')
            if session:
                if 'flash_messages' not in session:
                    session['flash_messages'] = []
                session['flash_messages'].append({
                    'message': f"Permission denied: {str(e)}. Please check file and directory permissions.",
                    'type': 'danger'
                })
                session.save()
            raise HTTPError(
                500,
                f"Permission denied: {str(e)}. "
                "Please check file and directory permissions."
            )
        except OSError as e:
            logger.error(
                f"OS error during file operation: {request.path} - {str(e)}",
                exc_info=True
            )
            # Set flash message
            session = request.environ.get('beaker.session')
            if session:
                if 'flash_messages' not in session:
                    session['flash_messages'] = []
                session['flash_messages'].append({
                    'message': f"File system error: {str(e)}. Please check disk space and permissions.",
                    'type': 'danger'
                })
                session.save()
            raise HTTPError(
                500,
                f"File system error: {str(e)}. "
                "Please check disk space and permissions."
            )
    return wrapper


def handle_validation_errors(func: Callable) -> Callable:
    """
    Decorator to handle validation exceptions.
    Returns HTTP 400 error with validation error message.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            logger.warning(
                f"Validation error: {e.field} - "
                f"Value: {e.value} - Path: {request.path} - Error: {e.message}"
            )
            # Set flash message
            session = request.environ.get('beaker.session')
            if session:
                if 'flash_messages' not in session:
                    session['flash_messages'] = []
                session['flash_messages'].append({
                    'message': f"Invalid input for {e.field}: {e.message}",
                    'type': 'warning'
                })
                session.save()
            raise HTTPError(
                400,
                f"Invalid input for {e.field}: {e.message}"
            )
    return wrapper


def handle_resource_errors(func: Callable) -> Callable:
    """
    Decorator to handle resource constraint exceptions.
    Returns HTTP 500 error with resource constraint message.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ResourceConstraintError as e:
            logger.error(
                f"Resource constraint: {e.resource_type} - "
                f"Path: {request.path} - Error: {e.message}",
                exc_info=True
            )
            # Set flash message
            session = request.environ.get('beaker.session')
            if session:
                if 'flash_messages' not in session:
                    session['flash_messages'] = []
                session['flash_messages'].append({
                    'message': f"Resource constraint: {e.message}",
                    'type': 'danger'
                })
                session.save()
            raise HTTPError(
                500,
                f"Resource constraint: {e.message}"
            )
    return wrapper
