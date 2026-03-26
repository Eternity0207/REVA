"""Backend API client for REVA desktop app"""
import requests
import logging
from typing import Optional, Dict, Any
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class REVAClient:
    """API client to communicate with backend"""
    
    def __init__(self, server_url: str = "http://localhost:8002"):
        self.server_url = server_url
        self.session = requests.Session()
        self.session.timeout = 10
    
    def register_agent(self, agent_id: str, token: str) -> bool:
        """Register agent with backend"""
        try:
            resp = self.session.post(
                f"{self.server_url}/api/agent/register",
                json={"agent_id": agent_id, "token": token},
                timeout=5
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Register failed: {e}")
            return False
    
    def heartbeat(self, agent_id: str, token: str) -> bool:
        """Send heartbeat to backend"""
        try:
            resp = self.session.post(
                f"{self.server_url}/api/agent/heartbeat",
                json={"agent_id": agent_id, "token": token},
                timeout=5
            )
            return resp.status_code == 200
        except Exception as e:
            logger.debug(f"Heartbeat failed: {e}")
            return False
    
    def get_task(self, agent_id: str, token: str) -> Optional[Dict[str, Any]]:
        """Fetch next task from backend"""
        try:
            headers = {
                "X-Agent-ID": agent_id,
                "X-Agent-Token": token,
            }
            resp = self.session.get(
                f"{self.server_url}/api/agent/get-task",
                headers=headers,
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                if data and data.get("task_id"):
                    return data
            return None
        except Exception as e:
            logger.debug(f"Get task error: {e}")
            return None
    
    def submit_result(self, agent_id: str, token: str, task_id: str, 
                     result: dict, error: Optional[str] = None) -> bool:
        """Submit task result to backend"""
        try:
            resp = self.session.post(
                f"{self.server_url}/api/agent/submit-result",
                json={
                    "agent_id": agent_id,
                    "token": token,
                    "task_id": task_id,
                    "result": result,
                    "error": error,
                },
                timeout=5
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Submit result error: {e}")
            return False
    
    def send_command(self, command_type: str, params: dict) -> Optional[str]:
        """Send command to backend (returns task_id)"""
        try:
            resp = self.session.post(
                f"{self.server_url}/api/send-command",
                json={"command_type": command_type, "params": params},
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json().get("task_id")
            return None
        except Exception as e:
            logger.error(f"Send command error: {e}")
            return None
    
    def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status"""
        try:
            resp = self.session.get(
                f"{self.server_url}/api/status/{task_id}",
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception as e:
            logger.debug(f"Get status error: {e}")
            return None
    
    def get_agents(self) -> Dict[str, Any]:
        """Get registered agents"""
        try:
            resp = self.session.get(
                f"{self.server_url}/api/agents",
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json()
            return {"agents": []}
        except Exception as e:
            logger.error(f"Get agents error: {e}")
            return {"agents": []}
    
    def check_connection(self) -> bool:
        """Check if backend is reachable"""
        try:
            resp = self.session.get(
                f"{self.server_url}/api/agents",
                timeout=3
            )
            return resp.status_code == 200
        except:
            return False
