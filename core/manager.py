"""Task Manager - In-memory task queue and management"""
from typing import Dict, List, Optional
from datetime import datetime
from .models import Task, TaskStatus, Command, Agent
import threading

class TaskManager:
    """Manages task pipeline and agent queues"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}  # task_id -> Task
        self.agents: Dict[str, Agent] = {}  # agent_id -> Agent
        self.agent_queues: Dict[str, List[str]] = {}  # agent_id -> [task_id, ...]
        self.agent_locks: Dict[str, threading.Lock] = {}  # agent_id -> Lock
        self.lock = threading.Lock()
    
    def create_task(self, agent_id: str, command: Command) -> Task:
        """Create and queue a new task"""
        task = Task(agent_id=agent_id, command=command)
        
        with self.lock:
            self.tasks[task.task_id] = task
            
            # Initialize agent queue if needed
            if agent_id not in self.agent_queues:
                self.agent_queues[agent_id] = []
                self.agent_locks[agent_id] = threading.Lock()
            
            # Add to agent's queue
            self.agent_queues[agent_id].append(task.task_id)
        
        return task
    
    def get_agent_task(self, agent_id: str) -> Optional[Task]:
        """Get next task for an agent (non-blocking)"""
        if agent_id not in self.agent_queues:
            return None
        
        with self.agent_locks[agent_id]:
            queue = self.agent_queues[agent_id]
            if not queue:
                return None
            
            task_id = queue.pop(0)
            task = self.tasks.get(task_id)
            
            if task:
                task.status = TaskStatus.DISPATCHED
                task.dispatched_at = datetime.utcnow()
                task.status = TaskStatus.RUNNING
            
            return task
    
    def submit_result(self, task_id: str, result: dict, error: Optional[str] = None) -> bool:
        """Agent submits task result"""
        with self.lock:
            if task_id not in self.tasks:
                return False
            
            task = self.tasks[task_id]
            task.result = result
            task.error = error
            task.status = TaskStatus.COMPLETED if not error else TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            
            return True
    
    def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get task status for UI"""
        with self.lock:
            if task_id not in self.tasks:
                return None
            return self.tasks[task_id].to_dict()
    
    def register_agent(self, agent: Agent) -> bool:
        """Register an agent"""
        with self.lock:
            self.agents[agent.agent_id] = agent
            if agent.agent_id not in self.agent_queues:
                self.agent_queues[agent.agent_id] = []
                self.agent_locks[agent.agent_id] = threading.Lock()
        return True
    
    def update_agent_heartbeat(self, agent_id: str) -> bool:
        """Update agent's last heartbeat"""
        with self.lock:
            if agent_id not in self.agents:
                return False
            self.agents[agent_id].last_heartbeat = datetime.utcnow()
            self.agents[agent_id].status = "online"
            return True
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent info"""
        with self.lock:
            return self.agents.get(agent_id)
    
    def list_agents(self) -> List[dict]:
        """List all agents"""
        with self.lock:
            return [agent.to_dict() for agent in self.agents.values()]
    
    def get_agent_status(self, agent_id: str) -> dict:
        """Get agent status and queue info"""
        with self.lock:
            agent = self.agents.get(agent_id)
            queue_size = len(self.agent_queues.get(agent_id, []))
            
            if not agent:
                return {"status": "unknown", "queue_size": 0}
            
            return {
                "agent_id": agent.agent_id,
                "status": agent.status,
                "last_heartbeat": agent.last_heartbeat.isoformat(),
                "queue_size": queue_size,
                "hostname": agent.hostname,
                "os_type": agent.os_type,
            }
