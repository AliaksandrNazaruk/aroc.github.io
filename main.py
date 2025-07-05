from core.logger import init_server_logger
# Initialize logging
init_server_logger()
from core.logger import server_logger

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from info import openapi_tags,description

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

    from routes.api import igus, symovo, xarm, robot, misc
    from routes.websocket import ws
    app.include_router(igus.router)
    app.include_router(symovo.router)
    app.include_router(xarm.router)
    app.include_router(robot.router)
    app.include_router(ws.router)
    app.include_router(misc.router)

    server_logger.log_event("info", "Startup OK.")

    yield
    server_logger.log_event("info", "Shutdown initiated")

    await xarm_client.__aexit__(None, None, None)
    await igus_client.__aexit__(None, None, None)

app = FastAPI(
    title="AE.01 API",
    version="1.0.0",
    lifespan=lifespan,
    description= description,
    openapi_tags=openapi_tags,
)
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    from core.connection_config import web_server_host, web_server_port
    server_logger.log_event("info", "Starting uvicorn server")
    uvicorn.run("main:app", host=web_server_host, port=web_server_port, reload=False)
