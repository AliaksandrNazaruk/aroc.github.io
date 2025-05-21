# Robot Control Server API Documentation

This document provides comprehensive documentation for the Robot Control Server API. The server provides endpoints for controlling various robotic components including Igus motors, Symovo AGV, XArm, and Arduino devices.

## Table of Contents
- [Base URL](#base-url)
- [Authentication](#authentication)
- [WebSocket Endpoints](#websocket-endpoints)
- [Igus Motor API](#igus-motor-api)
- [Symovo AGV API](#symovo-agv-api)
- [XArm API](#xarm-api)
- [Miscellaneous Endpoints](#miscellaneous-endpoints)
- [Error Handling](#error-handling)

## Base URL

All API endpoints are relative to the base URL of your server:
```
http://server:8000
```

## Authentication

Currently, the API does not require authentication.

## WebSocket Endpoints

### Depth Camera
```websocket
ws://server:8000/depth
```
Proxies to `ws://192.168.1.55:9999`

### Depth Query Camera
```websocket
ws://your-server:8000/depth_query
```
Proxies to `ws://192.168.1.55:10000`

### Color Camera
```websocket
ws://your-server:8000/color
```
Proxies to `ws://192.168.1.55:9998`

### Secondary Camera
```websocket
ws://server:8000/camera2
```
Proxies to `ws://localhost:9998`

### Igus Motor
```websocket
ws://server:8000/igus
```
Proxies to `ws://localhost:8020`

## Igus Motor API

### Get Motor State
```http
GET /api/igus/data
```

Returns the current state of the Igus motor.

**Response:**
```json
{
    "active": boolean,
    "ready": boolean,
    "connected": boolean,
    "last_update_str": string,
    "error": string,
    "homing": boolean
}
```

### Execute Command
```http
GET /api/igus/command_operator
```

Executes a command on the Igus motor.

**Parameters:**
- `command` (string, required): Command to execute
- `position` (integer, required): Target position
- `velocity` (integer, required): Movement velocity
- `acceleration` (integer, required): Movement acceleration
- `wait` (boolean, optional, default: true): Whether to wait for command completion

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

## XArm API

### Get XArm State
```http
GET /api/xarm/data
```

Returns the current state of the XArm robot.

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

## Miscellaneous Endpoints

### Get Root Page
```http
GET /
```
Serves the main index.html page.

### Get Control Page
```http
GET /control
```
Serves the control interface page.

### Get Job Status
```http
GET /job_status
```
Returns the current job status.

**Response:**
```json
{
    "done": boolean
}
```

### Get Script Status
```http
GET /script_status
```
Returns the current script execution status.

**Response:**
```json
{
    "status": string  // One of: "WORKING", "FINISHED", "NOT_RUNNING", "STOPPED", "FAILED"
}
```

### Stop Script
```http
GET /stop_script
```
Stops the currently running script.

### Check Server Status
```http
GET /status
```
Checks the server's operational status.

### Send Arduino Command
```http
POST /api/arduino/send
```
Sends a command to the Arduino controller.

**Request Body:**
```json
{
    "command": string
}
```

### Echo Endpoint
```http
POST /echo
```
Echoes back the received data (useful for testing).

### Submit Job
```http
POST /submit
```
Submits a new job for execution.

**Request Body:**
```json
{
    // Job-specific parameters
}
```

### Run Script
```http
POST /run_script
```
Starts execution of a script.

**Request Body:**
```json
{
    "command": string
}
```

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of requests:

- `200 OK`: Request succeeded
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

Error responses include a JSON object with an error message:

```json
{
    "detail": "Error message description"
}
```

## Examples

### Starting a New AGV Job
```bash
curl -X GET "http://your-server:8000/api/symovo_car/new_job?name=position1"
```

### Executing an Igus Command
```bash
curl -X GET "http://your-server:8000/api/igus/command_operator?command=move&position=100&velocity=50&acceleration=25"
```

### Running a Script
```bash
curl -X POST "http://your-server:8000/run_script" \
     -H "Content-Type: application/json" \
     -d '{"command": "script_name"}'
```

## Notes

- All timestamps are in ISO 8601 format
- WebSocket connections should implement proper error handling and reconnection logic
- Some endpoints may have additional parameters not documented here; refer to the source code for complete details
