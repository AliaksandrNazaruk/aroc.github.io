from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from routes.api import igus, symovo, xarm
from routes.websocket import ws
from routes.misc import misc
from services.igus_manager import connection_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    from db.trajectory import init_trajectory_table
    from db.regals import init_regals_table
    from core.state import symovo_car
    
    init_trajectory_table()
    init_regals_table()
    symovo_car.start_polling(interval=10)
    connection_manager.start()
    print("Startup OK.")
    yield
    connection_manager.stop()

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(igus.router)
app.include_router(symovo.router)
app.include_router(xarm.router)
app.include_router(ws.router)
app.include_router(misc.router)
# app.include_router(trajectory.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("core.main:app", host="0.0.0.0", port=8000, reload=True) 