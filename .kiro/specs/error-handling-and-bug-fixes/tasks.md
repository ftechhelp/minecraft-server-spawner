# Implementation Plan

- [x] 1. Create input validation module
  - Create `utils/validators.py` with validation functions for ports, spawn names, versions, and mods
  - Implement `validate_port()` to check port range (1-65535) and numeric validity
  - Implement `validate_spawn_name()` to prevent path traversal and invalid characters
  - Implement `validate_minecraft_version()` and `validate_mod_name()` for format validation
  - Implement `check_port_availability()` to detect port conflicts across spawns
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 2. Create error handling infrastructure
  - Create `utils/error_handlers.py` with custom exception classes
  - Define `SpawnNotFoundError`, `ValidationError`, `DockerOperationError`, and `FileOperationError` exception classes
  - Implement decorator functions: `@handle_spawn_not_found`, `@handle_docker_errors`, `@handle_file_errors`, `@handle_validation_errors`
  - Add logging configuration with appropriate log levels
  - _Requirements: 1.1, 1.2, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3_

- [x] 3. Add error handling to Spawner class
  - Modify `utils/spawner.py` to add error handling in `create_or_modify_spawn()`
  - Wrap Docker operations in try-except blocks with specific error handling
  - Add error handling to `loadSpawns()` to skip corrupted spawns and continue loading
  - Ensure spawns directory exists in `__init__()` method
  - Implement `spawn_exists()`, `get_spawn_safely()`, and `check_port_conflict()` helper methods
  - Handle missing or corrupted docker-compose.yml files gracefully
  - _Requirements: 3.1, 3.2, 3.4, 4.1, 4.2, 4.4, 9.1, 9.2, 9.3, 9.4_

- [x] 4. Add error handling to Spawn class
  - Modify `models/spawn.py` to add try-except blocks to all Docker operations (up, stop, start, purge)
  - Add container state validation before executing operations
  - Implement `is_running()` and `can_execute_command()` helper methods
  - Fix `get_docker_compose_contents()` to handle missing files by creating default structure
  - Add error handling to `uploadMods()` for invalid ZIP files and missing modlist.html
  - Add error handling to `send_console_command()` with container state checking
  - Handle FileNotFoundError in `load_server_properties()` and `write_server_properties()`
  - _Requirements: 3.1, 3.2, 3.3, 4.1, 4.3, 4.5, 5.1, 5.2, 5.3, 5.5, 6.1, 6.2, 6.3_

- [x] 5. Add input validation to route handlers
  - Modify `app.py` to add validation to `/spawn` POST route for all form inputs
  - Validate port numbers, spawn names, and version strings before processing
  - Check for port conflicts before creating spawns
  - Add spawn existence checks to all spawn-specific routes (`/spawn/<name>` and related)
  - Return HTTP 400 with error messages for validation failures
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 6. Add error handling decorators to routes
  - Apply `@handle_spawn_not_found` decorator to all spawn-specific routes
  - Apply `@handle_docker_errors` decorator to routes that perform Docker operations
  - Apply `@handle_file_errors` decorator to routes that perform file operations
  - Ensure proper HTTP status codes are returned (404 for not found, 500 for server errors)
  - Add logging statements to capture error details
  - _Requirements: 1.1, 1.2, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 8.2_

- [x] 7. Create error page templates
  - Create `templates/error.tpl` for generic error display with Bulma CSS styling
  - Create `templates/404.tpl` for not found errors with link back to home
  - Create `templates/500.tpl` for server errors with helpful message
  - Add flash message support to `templates/index.tpl` for displaying error notifications
  - Add flash message support to `templates/spawn.tpl` for operation feedback
  - _Requirements: 8.1, 8.2, 8.3_

- [x] 8. Implement session-based flash messages
  - Add session management to `app.py` using Bottle's built-in session support or beaker
  - Create helper functions `set_flash_message()` and `get_flash_messages()` in `app.py`
  - Modify routes to set flash messages on errors and successes
  - Update templates to display and clear flash messages
  - _Requirements: 8.1, 8.3_

- [x] 9. Add comprehensive error handling to mod operations
  - Validate uploaded file is a ZIP archive in `uploadMods()`
  - Add file size validation before processing uploads
  - Handle missing modlist.html with specific error message
  - Add error handling for malformed HTML parsing
  - Handle temporary directory creation failures
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 10. Add resource and network constraint handling
  - Add disk space checking before spawn creation operations
  - Add error handling for Docker resource constraints (memory, CPU)
  - Add timeout handling for long-running Docker operations
  - Detect when Docker daemon is not running and provide clear error message
  - _Requirements: 3.4, 10.1, 10.2, 10.3_

- [ ] 11. Improve concurrent operation safety
  - Add file locking or atomic operations for spawn modifications
  - Ensure spawner.loadSpawns() is called safely when needed
  - Add state checking before operations to prevent race conditions
  - _Requirements: 7.1, 7.2_

- [ ] 12. Add logging throughout the application
  - Configure Python logging module in `app.py` with file and console handlers
  - Add INFO level logging for successful operations
  - Add ERROR level logging for all caught exceptions with stack traces
  - Add WARNING level logging for recoverable issues
  - Ensure sensitive information is not logged
  - _Requirements: 3.5, 8.2_
