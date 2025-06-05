# Robot Control Server API Documentation

This document provides comprehensive documentation for the Robot Control Server API. The server provides endpoints for controlling various robotic components including Igus motors, Symovo AGV, and XArm.

## Table of Contents
- [Base URL](#base-url)
- [Authentication](#authentication)
- [Igus Motor API](#igus-motor-api)
- [Symovo AGV API](#symovo-agv-api)
- [XArm API](#xarm-api)
- [System API](#system-api)
- [Error Handling](#error-handling)

## Base URL

All API endpoints are relative to the base URL of your server:
```
http://your-server:8000
```

## Authentication

Currently, the API does not require authentication.

## Igus Motor API

### Get Motor Data
```http
GET /api/igus/data
```

Returns the current state of the Igus motor.

**Response:**
```json
{
    "status": object,
    "error": string,
    "connected": boolean,
    "position": number
}
```

### Get Motor State
```http
GET /api/igus/state
```

Returns detailed state information about the Igus motor.

**Response:**
```json
{
    "status": object,
    "homing": boolean,
    "error": string,
    "connected": boolean,
    "position": number
}
```

### Get Current Position
```http
GET /api/igus/position
```

Returns only the current position of the motor.

**Response:**
```json
{
    "position": number,
    "state": object
}
```

### Move to Position
```http
POST /api/igus/move_to_position
```

Moves the motor to a specified position.

**Request Body:**
```json
{
    "position": number,
    "velocity": number,
    "acceleration": number,
    "wait": boolean
}
```

**Response:**
```json
{
    "success": boolean,
    "result": {
        "position": number
    },
    "error": string,
    "state": object
}
```

### Reference Motor
```http
POST /api/igus/reference
```

Performs homing operation on the motor.

**Response:**
```json
{
    "success": boolean,
    "result": {
        "homing": boolean
    },
    "error": string,
    "state": object
}
```

### Reset Faults
```http
POST /api/igus/fault_reset
```

Resets any active faults on the motor.

**Response:**
```json
{
    "success": boolean,
    "result": {
        "fault_reset": boolean
    },
    "error": string,
    "state": object
}
```

## Symovo AGV API

### Get AGV State
```http
GET /api/symovo_car/data
```

Returns the current state of the Symovo AGV.

**Response:**
```json
{
    "online": boolean,
    "last_update_time": string,
    "id": string,
    "name": string,
    "pose": {
        "x": number,
        "y": number,
        "theta": number,
        "map_id": string
    },
    "velocity": {
        "x": number,
        "y": number,
        "theta": number
    },
    "state": string,
    "battery_level": number,
    "state_flags": object,
    "robot_ip": string,
    "replication_port": number,
    "api_port": number,
    "iot_port": number,
    "last_seen": string,
    "enabled": boolean,
    "last_update": string,
    "attributes": object,
    "planned_path_edges": array
}
```

### Get Jobs
```http
GET /api/symovo_car/jobs
```

Returns the list of current jobs for the AGV.

### Create New Job
```http
GET /api/symovo_car/new_job
```

Starts a new job for the AGV to move to a specified position.

**Parameters:**
- `name` (string, required): Name of the target position

**Response:**
```json
{
    "status": "ok",
    "message": string,
    "result": object
}
```

### Get Maps
```http
GET /api/symovo_car/maps
```

Returns the list of available maps from the AGV.

### Move to Pose
```http
POST /api/symovo_car/go_to_pose
```

Moves the AGV to an arbitrary pose.

**Request Body:**
```json
{
    "x": number,
    "y": number,
    "theta": number,
    "map_id": string,
    "max_speed": number
}
```

**Response:**
```json
{
    "status": "ok",
    "result": object
}
```

### Check Pose
```http
POST /api/symovo_car/check_pose
```

Checks if the given pose is reachable by the AGV.

### Task Status
```http
GET /api/symovo_car/task_status
```

Query Parameters:
- `task_id` (string, required): Identifier of the task returned when moving the AGV.

Returns status information for the specified task.

## XArm API

### Get XArm State
```http
GET /api/xarm/data
```

Returns the current state of the XArm robot.

**Response:**
```json
{
    "message": string  // "manipulator is busy" or actual data
}
```

### Execute Command
```http
POST /api/xarm/command
```

Executes a command on the XArm robot.

**Request Body:**
```json
{
    "command": string,
    // Additional command-specific parameters
}
```

**Response:**
- Success: Command execution result
- Error: Error message with appropriate HTTP status code

**Possible Error Responses:**
- 409: Manipulator is busy with another command
- 408: Command execution timed out
- 400: Invalid command
- 500: Internal server error

## System API

### Get System Status
```http
GET /api/system/status
```

Returns high level information about the robot system.

**Response:**
```json
{
    "symovo_online": boolean,
    "igus_connected": boolean
}
```

### Move to Product
```http
POST /api/system/move_to_product
```

Moves the entire robot system to the specified product location. The AGV drives
to the coordinates, the lift moves to the given position, and the manipulator
executes the provided pose sequence.

**Request Body:**
```json
{
    "product_id": "string",
    "location": {
        "x": number,
        "y": number,
        "theta": number,
        "map_id": "string"
    },
    "lift_position": number,
    "manipulator_coords": {
        "x": number,
        "y": number,
        "z": number
    },
    "speed": number
}
```

**Response:**
```json
{
    "status": "ok",
    "agv_result": object,
    "lift_result": object,
    "manipulator_result": object
}
```

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of requests:

- `200 OK`: Request succeeded
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `408 Request Timeout`: Command execution timed out
- `409 Conflict`: Resource is busy
- `500 Internal Server Error`: Server-side error

Error responses include a JSON object with an error message:

```json
{
    "detail": "Error message description"
}
```

## Notes

- All timestamps are in ISO 8601 format
- XArm commands have a default timeout of 30 seconds
- The XArm API uses a lock mechanism to prevent concurrent command execution
- Some endpoints may have additional parameters not documented here; refer to the source code for complete details 
