"""xArm manipulator API routes for motion, gripper control and status."""

import asyncio
import uuid
from collections import OrderedDict

class TaskManager:
    """Utility for tracking asynchronous manipulator tasks."""

    def __init__(self, max_tasks: int = 100):
        self.tasks: "OrderedDict[str, dict]" = OrderedDict()
        self.max_tasks = max_tasks

    def create_task(self, coro):
        """Register and start an asynchronous task."""
        task_id = str(uuid.uuid4())
        loop = asyncio.get_event_loop()
        task = loop.create_task(coro)
        self.tasks[task_id] = {
            "status": "working",  # task started
            "result": None,
            "task": task,
        }

        def _on_task_done(t: asyncio.Task):
            try:
                res = t.result()
                self.tasks[task_id]["status"] = "done"
                self.tasks[task_id]["result"] = res
            except Exception as e:
                self.tasks[task_id]["status"] = "error"
                self.tasks[task_id]["result"] = str(e)

        task.add_done_callback(_on_task_done)

        # Limit task queue size
        while len(self.tasks) > self.max_tasks:
            self.tasks.popitem(last=False)
        return task_id

    def get_status(self, task_id):
        """Return information about an async task."""
        if task_id not in self.tasks:
            return {"status": "not_found"}
        task_info = self.tasks[task_id]
        return {
            "status": task_info["status"],
            "result": task_info["result"],
        }