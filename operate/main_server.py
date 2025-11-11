from fastapi import FastAPI
from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from loguru import logger

app = FastAPI(title="REVA Advanced Server", version="2.0")

class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskRequest(BaseModel):
    model: str
    prompt: str
    priority: str = "normal"
    timeout: int = 300

class Task:
    def __init__(self, task_id, request):
        self.task_id = task_id
        self.status = TaskStatus.QUEUED
        self.model = request.model
        self.prompt = request.prompt
        self.progress = 0

task_store = {}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "REVA Advanced Server v2.0"}

@app.post("/execute")
async def execute(request: TaskRequest):
    task_id = f"task_{len(task_store)}"
    task = Task(task_id, request)
    task_store[task_id] = task
    logger.info(f"Task {task_id} queued")
    return {"status": "accepted", "task_id": task_id}

@app.get("/tasks")
async def list_tasks(status: str = None):
    tasks = list(task_store.values())
    return {"tasks": tasks, "count": len(tasks)}
