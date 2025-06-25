from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from core.logger import init_server_logger
# Initialize logging
init_server_logger()
from core.logger import server_logger
from routes.misc import misc
from core.configuration import igus_motor_ip, igus_motor_port
from core.connection_config import web_server_host, web_server_port

import time
# time.sleep(15)

@asynccontextmanager
async def lifespan(app: FastAPI):
    from db.trajectory import init_trajectory_table
    from db.regals import init_regals_table
    # from core.state import symovo_car
    from core.state import xarm_client
    from core.state import igus_client
    # Clients initialization
    await xarm_client.__aenter__()
    await igus_client.__aenter__()

    init_trajectory_table()
    init_regals_table()

    from routes.api import igus, symovo, xarm, system
    from routes.websocket import ws
    app.include_router(igus.router)
    app.include_router(symovo.router)
    app.include_router(xarm.router)
    app.include_router(system.router)
    app.include_router(ws.router)
    app.include_router(misc.router)

    server_logger.log_event("info", "Startup OK.")
    yield
    server_logger.log_event("info", "Shutdown initiated")

    await xarm_client.__aexit__(None, None, None)
    await igus_client.__aexit__(None, None, None)


app = FastAPI(
    title="AE.01 API",
    description="Prototype API for managing igus, xarm, symovo systems. Supports position control, speed control, error reset and device status monitoring.",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Igus Motor",
            "description": (
                "Igus Motor endpoints provide access to motor control features:\n"
                "- Position control\n"
                "- Speed and acceleration settings\n"
                "- Homing/reference\n"
                "- Fault reset\n"
                "- Status monitoring\n"
                "\n"
                "Note: Only one command can be processed at a time; 423 Locked will be returned if busy."
            )
        }
    ]
)
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    server_logger.log_event("info", "Starting uvicorn server")
    uvicorn.run("main:app", host=web_server_host, port=web_server_port, reload=True)
from fastapi import FastAPI

