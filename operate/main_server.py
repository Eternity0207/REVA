"""REVA Internal Server"""
from fastapi import FastAPI
from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from loguru import logger

app = FastAPI(title="REVA Server", version="2.0")

command_history = []

class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskRequest(BaseModel):
    model: str
    prompt: str
    priority: str = "normal"

class Task:
    def __init__(self, task_id, request):
        self.task_id = task_id
        self.status = TaskStatus.QUEUED
        self.model = request.model
        self.prompt = request.prompt
        self.created_at = datetime.now()

task_store = {}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/execute")
async def execute(request: TaskRequest):
    task_id = f"task_{len(task_store)}"
    task = Task(task_id, request)
    task_store[task_id] = task
    command_history.append({"id": task_id, "prompt": request.prompt, "time": datetime.now().isoformat()})
    logger.info(f"Task {task_id} queued")
    return {"status": "accepted", "task_id": task_id}

@app.get("/history")
async def get_history():
    return {"history": command_history[-20:]}

@app.get("/tasks")
async def list_tasks(status: str = None):
    tasks = list(task_store.values())
    return {"tasks": tasks, "count": len(tasks)}
