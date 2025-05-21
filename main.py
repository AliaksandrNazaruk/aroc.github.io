from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from routes import igus, symovo, xarm, ws, misc, trajectory

@asynccontextmanager
async def lifespan(app: FastAPI):
    from db.trajectory import init_trajectory_table
    from db.regals import init_regals_table
    from state import igus_motor, symovo_car
    init_trajectory_table()
    init_regals_table()
    igus_motor.start_polling(interval=3)
    symovo_car.start_polling(interval=10)
    print("Startup OK.")
    yield

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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
