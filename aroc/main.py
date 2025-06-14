from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager


from routes.misc import misc
from core.configuration import igus_motor_ip, igus_motor_port
from core.connection_config import web_server_host, web_server_port
from core.logger import init_server_logger, server_logger

import time
# time.sleep(15)

# Initialize logging
init_server_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    from db.trajectory import init_trajectory_table
    from db.regals import init_regals_table
    from core.state import symovo_car
    from core.state import xarm_client
    from core.state import igus_client
    from core.state import init_igus_motor
    # Clients initialization
    await xarm_client.__aenter__()
    await igus_client.__aenter__()
        
    init_igus_motor(igus_motor_ip, igus_motor_port)
    init_trajectory_table()
    init_regals_table()
    symovo_car.start_polling(interval=10)

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

    await xarm_client.__aexit__(None, None, None)
    await igus_client.__aexit__(None, None, None)


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=web_server_host, port=web_server_port, reload=True)
