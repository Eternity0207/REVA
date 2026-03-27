"""Agent Client - Runs on user machine"""
import requests
import time
import platform
import socket
import os
from typing import Optional, Dict, Any
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("REVAAgent")

class REVAAgent:
    """Agent that polls backend and executes commands"""
    
    def __init__(self, server_url: str, agent_id: str, token: str, poll_interval: int = 3):
        self.server_url = server_url.rstrip('/')
        self.agent_id = agent_id
        self.token = token
        self.poll_interval = poll_interval
        self.running = False
        self.session = requests.Session()
        self.hostname = socket.gethostname()
        self.os_type = platform.system()
    
    def register(self) -> bool:
        """Register agent with backend"""
        try:
            payload = {
                "agent_id": self.agent_id,
                "token": self.token,
                "hostname": self.hostname,
                "os_type": self.os_type,
            }
            
            resp = self.session.post(
                f"{self.server_url}/api/agent/register",
                json=payload,
                timeout=5
            )
            
            if resp.status_code == 200:
                logger.info(f"✅ Registered: {self.agent_id} @ {self.server_url}")
                return True
            else:
                logger.error(f"❌ Registration failed: {resp.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Registration error: {e}")
            return False
    
    def heartbeat(self) -> bool:
        """Send heartbeat to backend"""
        try:
            payload = {
                "agent_id": self.agent_id,
                "token": self.token,
            }
            
            resp = self.session.post(
                f"{self.server_url}/api/agent/heartbeat",
                json=payload,
                timeout=5
            )
            
            return resp.status_code == 200
        except Exception as e:
            logger.debug(f"Heartbeat failed: {e}")
            return False
    
    def fetch_task(self) -> Optional[Dict[str, Any]]:
        """Fetch next task from backend"""
        try:
            headers = {
                "X-Agent-ID": self.agent_id,
                "X-Agent-Token": self.token,
            }
            
            resp = self.session.get(
                f"{self.server_url}/api/agent/get-task",
                headers=headers,
                timeout=5
            )
            
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 204:  # No content
                return None
            else:
                logger.warning(f"Failed to fetch task: {resp.status_code}")
                return None
        except Exception as e:
            logger.debug(f"Fetch task error: {e}")
            return False
    
    def submit_result(self, task_id: str, result: Dict[str, Any], error: Optional[str] = None) -> bool:
        """Submit task result to backend"""
        try:
            payload = {
                "agent_id": self.agent_id,
                "token": self.token,
                "task_id": task_id,
                "result": result,
                "error": error,
            }
            
            resp = self.session.post(
                f"{self.server_url}/api/agent/submit-result",
                json=payload,
                timeout=5
            )
            
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Submit result error: {e}")
            return False
    
    def execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command locally"""
        try:
            from handlers.command import CommandHandler
            
            result = CommandHandler.execute(
                command.get("type"),
                command.get("params", {})
            )
            
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def run(self):
        """Main agent loop - register and poll for tasks"""
        logger.info(f"🚀 Starting REVA Agent: {self.agent_id}")
        
        if not self.register():
            logger.error("Failed to register, retrying...")
            time.sleep(5)
            return
        
        self.running = True
        last_heartbeat = 0
        
        try:
            while self.running:
                # Send heartbeat every 30 seconds
                if time.time() - last_heartbeat > 30:
                    self.heartbeat()
                    last_heartbeat = time.time()
                
                # Fetch and execute task
                task_data = self.fetch_task()
                
                if task_data:
                    task_id = task_data.get("task_id")
                    command = task_data.get("command")
                    
                    logger.info(f"📋 Executing task: {task_id}")
                    
                    result = self.execute_command(command)
                    
                    self.submit_result(
                        task_id,
                        result,
                        error=result.get("error") if not result.get("success") else None
                    )
                    
                    logger.info(f"✅ Task {task_id} completed")
                else:
                    # No task, wait and try again
                    time.sleep(self.poll_interval)
        
        except KeyboardInterrupt:
            logger.info("Agent stopped by user")
            self.running = False
        except Exception as e:
            logger.error(f"Agent error: {e}")
            self.running = False

def main():
    """Agent entrypoint"""
    import sys
    
    # Load from environment or config file
    server_url = os.getenv("REVA_SERVER_URL", "http://localhost:8002")
    agent_id = os.getenv("REVA_AGENT_ID", f"agent-{socket.gethostname()}")
    token = os.getenv("REVA_AGENT_TOKEN", "")
    
    if not token:
        logger.error("❌ REVA_AGENT_TOKEN not set")
        sys.exit(1)
    
    agent = REVAAgent(server_url, agent_id, token)
    agent.run()

if __name__ == "__main__":
    main()
