# Design Document

## Overview

This design document outlines the approach for implementing comprehensive error handling and bug fixes in the Minecraft server management application. The solution focuses on adding defensive programming practices, input validation, exception handling, and user-friendly error reporting throughout the application stack.

The design follows a layered approach:
1. **Input Validation Layer** - Validate all user inputs at the route level
2. **Error Handling Layer** - Wrap operations with try-catch blocks and proper error propagation
3. **User Feedback Layer** - Provide clear, actionable error messages to users
4. **Logging Layer** - Log technical details for debugging

## Architecture

### Error Handling Strategy

The application will implement a multi-tiered error handling strategy:

```
User Request → Input Validation → Business Logic → Docker Operations → Response
                     ↓                  ↓                ↓              ↓
                Error Handler ← Error Handler ← Error Handler ← Error Response
```

Each layer will:
- Validate inputs and preconditions
- Catch exceptions from lower layers
- Transform technical errors into user-friendly messages
- Log errors for debugging
- Return appropriate HTTP status codes

### Error Response Format

All error responses will follow a consistent pattern:
- HTTP status code (400, 404, 500, etc.)
- User-friendly error message
- Optional: Suggested actions
- Backend: Detailed logging for debugging

## Components and Interfaces

### 1. Input Validation Module

**Location**: New file `utils/validators.py`

**Purpose**: Centralize all input validation logic

**Functions**:
- `validate_port(port: str) -> tuple[bool, int, str]` - Validates port numbers
- `validate_spawn_name(name: str) -> tuple[bool, str, str]` - Validates spawn names
- `validate_minecraft_version(version: str) -> tuple[bool, str, str]` - Validates version strings
- `validate_mod_name(mod: str) -> tuple[bool, str, str]` - Validates mod identifiers
- `check_port_availability(port: int, spawner: Spawner, exclude_spawn: str = None) -> tuple[bool, str]` - Checks for port conflicts

**Return Format**: `(is_valid: bool, validated_value: any, error_message: str)`

### 2. Error Handler Decorator

**Location**: New file `utils/error_handlers.py`

**Purpose**: Provide reusable error handling decorators for routes

**Decorators**:
- `@handle_spawn_not_found` - Catches KeyError for missing spawns
- `@handle_docker_errors` - Catches Docker-related exceptions
- `@handle_file_errors` - Catches file operation exceptions
- `@handle_validation_errors` - Catches validation exceptions

**Custom Exceptions**:
- `SpawnNotFoundError` - Raised when spawn doesn't exist
- `ValidationError` - Raised for invalid inputs
- `DockerOperationError` - Raised for Docker failures
- `FileOperationError` - Raised for file operation failures

### 3. Enhanced Spawner Class

**Modifications to**: `utils/spawner.py`

**Changes**:
- Add error handling to `create_or_modify_spawn()`
- Add error handling to `loadSpawns()`
- Add `spawn_exists(name: str) -> bool` method
- Add `get_spawn_safely(name: str) -> Spawn | None` method
- Add `check_port_conflict(port: int, exclude_spawn: str = None) -> bool` method
- Ensure spawns directory exists on initialization
- Handle corrupted docker-compose.yml files gracefully

### 4. Enhanced Spawn Class

**Modifications to**: `models/spawn.py`

**Changes**:
- Add error handling to all Docker operations (up, stop, start, purge)
- Add validation to `uploadMods()`
- Add error handling to `send_console_command()`
- Add container state checking before operations
- Add timeout handling for Docker operations
- Improve `get_docker_compose_contents()` to handle missing files
- Add `is_running() -> bool` method
- Add `can_execute_command() -> bool` method

### 5. Enhanced Route Handlers

**Modifications to**: `app.py`

**Changes**:
- Add input validation to all POST routes
- Add spawn existence checks to all spawn-specific routes
- Add error handling wrappers to all routes
- Add flash message support for error notifications
- Return proper HTTP status codes
- Add error templates for 404, 500 errors

### 6. Error Templates

**New Templates**:
- `templates/error.tpl` - Generic error page
- `templates/404.tpl` - Not found page
- `templates/500.tpl` - Server error page

**Modifications**:
- Add flash message display to `templates/index.tpl`
- Add flash message display to `templates/spawn.tpl`

## Data Models

### Error Response Model

```python
@dataclass
class ErrorResponse:
    status_code: int
    message: str
    details: str = ""
    suggested_action: str = ""
```

### Validation Result Model

```python
@dataclass
class ValidationResult:
    is_valid: bool
    value: any = None
    error_message: str = ""
```

## Error Handling

### Error Categories and Handling

#### 1. Input Validation Errors (HTTP 400)
- Invalid port numbers
- Invalid spawn names
- Invalid version strings
- Empty required fields
- Port conflicts

**Handling**: Validate at route level, return error page with form data preserved

#### 2. Not Found Errors (HTTP 404)
- Spawn doesn't exist
- File doesn't exist

**Handling**: Return 404 error page with helpful message and link to home

#### 3. Docker Operation Errors (HTTP 500)
- Container creation failures
- Container start/stop failures
- Docker daemon not available
- Insufficient resources

**Handling**: Catch exceptions, log details, show user-friendly message with suggested actions

#### 4. File Operation Errors (HTTP 500)
- Permission denied
- Disk full
- Corrupted files
- Missing directories

**Handling**: Catch exceptions, attempt recovery where possible, inform user

#### 5. Mod Upload Errors (HTTP 400/500)
- Invalid ZIP file
- Missing modlist.html
- Malformed HTML
- File too large

**Handling**: Validate file before processing, provide specific error messages

### Error Logging Strategy

All errors will be logged with:
- Timestamp
- Error type
- Stack trace
- User action that triggered the error
- Spawn name (if applicable)
- Request details

Use Python's `logging` module with appropriate log levels:
- `ERROR` - For exceptions and failures
- `WARNING` - For recoverable issues
- `INFO` - For successful operations
- `DEBUG` - For detailed debugging information

## Testing Strategy

### Unit Tests

Test individual validation functions:
- Test `validate_port()` with valid and invalid inputs
- Test `validate_spawn_name()` with edge cases
- Test port conflict detection
- Test error handler decorators

### Integration Tests

Test error handling in context:
- Test spawn creation with invalid inputs
- Test operations on non-existent spawns
- Test Docker operation failures (mock Docker)
- Test file operation failures (mock file system)
- Test mod upload with invalid files

### Manual Testing Scenarios

1. **Missing Spawn Test**
   - Access `/spawn/nonexistent`
   - Expected: 404 error page

2. **Invalid Port Test**
   - Submit spawn form with port "abc"
   - Expected: Validation error message

3. **Port Conflict Test**
   - Create spawn on port 25565
   - Create another spawn on port 25565
   - Expected: Port conflict error

4. **Docker Down Test**
   - Stop Docker daemon
   - Attempt spawn operation
   - Expected: Docker unavailable error

5. **Invalid Mod Upload Test**
   - Upload non-ZIP file as modpack
   - Expected: Invalid file type error

6. **Missing Directory Test**
   - Delete spawns directory
   - Restart application
   - Expected: Directory created automatically

7. **Corrupted Config Test**
   - Corrupt a docker-compose.yml file
   - Restart application
   - Expected: Spawn skipped, others load successfully

### Error Recovery Testing

Test that the application can recover from errors:
- Application continues running after errors
- Other spawns unaffected by one spawn's errors
- Subsequent operations succeed after fixing issues

## Implementation Notes

### Backward Compatibility

- Existing spawns will continue to work
- No changes to docker-compose.yml format
- No database migrations needed

### Performance Considerations

- Validation adds minimal overhead
- Error handling doesn't impact happy path performance
- Logging is asynchronous where possible

### Security Considerations

- Validate spawn names to prevent path traversal attacks
- Sanitize user inputs before displaying in error messages
- Don't expose sensitive information in error messages
- Log sensitive details only to server logs, not user-facing messages

### User Experience

- Error messages are clear and actionable
- Users can easily return to previous page
- Form data is preserved on validation errors where possible
- Loading indicators for long operations
- Success messages for completed operations

## Design Decisions and Rationales

### Decision 1: Centralized Validation Module

**Rationale**: Keeping validation logic in one place makes it easier to maintain, test, and reuse across routes. It also ensures consistent validation behavior.

### Decision 2: Custom Exception Classes

**Rationale**: Custom exceptions make error handling more explicit and allow for specific handling of different error types. They also improve code readability.

### Decision 3: Decorator-Based Error Handling

**Rationale**: Decorators reduce code duplication and make routes cleaner. They provide a consistent error handling pattern across all routes.

### Decision 4: Fail-Safe Spawn Loading

**Rationale**: One corrupted spawn shouldn't prevent the entire application from starting. Skipping problematic spawns allows the application to remain functional.

### Decision 5: Graceful Degradation

**Rationale**: When operations fail, the application should continue functioning for other spawns and operations. This improves overall reliability.

### Decision 6: Detailed Logging with Simple User Messages

**Rationale**: Developers need technical details for debugging, but users need simple, actionable messages. Separating these concerns improves both developer and user experience.
