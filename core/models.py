"""Task and Command Models"""
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, Dict
import uuid

class TaskStatus(Enum):
    QUEUED = "queued"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class CommandType(Enum):
    PRESS = "press"
    CLICK = "click"
    WRITE = "write"
    SCREENSHOT = "screenshot"
    SYSTEM_INFO = "system_info"
    SLEEP = "sleep"
    OPEN_APP = "open_app"

@dataclass
class Command:
    """Structured command"""
    type: CommandType
    params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "type": self.type.value,
            "params": self.params
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            type=CommandType(data["type"]),
            params=data.get("params", {})
        )

@dataclass
class Task:
    """Task pipeline object"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    command: Command = None
    status: TaskStatus = TaskStatus.QUEUED
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    dispatched_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self):
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "command": self.command.to_dict() if self.command else None,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "dispatched_at": self.dispatched_at.isoformat() if self.dispatched_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retry_count": self.retry_count,
        }

@dataclass
class Agent:
    """Agent registration"""
    agent_id: str
    token: str
    hostname: str = ""
    os_type: str = ""
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    status: str = "offline"  # online/offline
    
    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "hostname": self.hostname,
            "os_type": self.os_type,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "status": self.status,
        }
