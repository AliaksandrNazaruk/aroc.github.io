import asyncio
import sys
import signal
import logging
import os

logger = logging.getLogger("manager")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Command to launch the server process.
# Uses sys.executable so the same interpreter is used,
# forming the path to server.py which should be in the same directory.
SERVER_PATH = os.path.join(os.path.dirname(__file__), "server.py")
SERVER_CMD = [sys.executable, SERVER_PATH]

RESTART_DELAY = 5  # delay before restart (seconds)

async def run_server():
    """
    Launch the server process as a subprocess and log its stdout/stderr.
    Returns the exit code when the process ends.
    """
    logger.info("Starting server process...")
    proc = await asyncio.create_subprocess_exec(
        *SERVER_CMD,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    # Tasks to read stdout and stderr
    stdout_task = asyncio.create_task(read_stream(proc.stdout, "STDOUT"))
    stderr_task = asyncio.create_task(read_stream(proc.stderr, "STDERR"))
    try:
        returncode = await proc.wait()
        logger.error(f"Server exited with code {returncode}")
    except Exception as e:
        logger.error(f"Server process error: {e}")
        returncode = -1
    finally:
        stdout_task.cancel()
        stderr_task.cancel()
    return returncode

async def read_stream(stream, label):
    """
    Read and log lines from the server process stream (stdout or stderr).
    """
    while True:
        line = await stream.readline()
        if not line:
            break
        logger.info(f"{label}: {line.decode().rstrip()}")

async def run_manager():
    """
    Run the server process in a loop. If it exits,
    wait RESTART_DELAY seconds and start it again.
    """
    while True:
        code = await run_server()
        logger.info(f"Restarting server in {RESTART_DELAY} seconds...")
        await asyncio.sleep(RESTART_DELAY)

def shutdown():
    logger.info("Stopping manager...")
    for task in asyncio.all_tasks():
        task.cancel()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    # Register signal handlers for graceful shutdown
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)
    try:
        loop.run_until_complete(run_manager())
    except asyncio.CancelledError:
        logger.info("Manager stopped.")
    finally:
        loop.close()
