"""Built-in agent service for REVA desktop app"""
import logging
import threading
import time
from typing import Optional, Dict, Any, Callable
from .client import REVAClient
from .executor import CommandExecutor

logger = logging.getLogger(__name__)


class AgentService:
    """Built-in agent that polls backend and executes commands"""
    
    def __init__(self, server_url: str = "http://localhost:8002"):
        self.server_url = server_url
        self.client = REVAClient(server_url)
        self.agent_id: Optional[str] = None
        self.token: Optional[str] = None
        self.is_running = False
        self.is_connected = False
        self.poll_thread: Optional[threading.Thread] = None
        self.heartbeat_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.on_connected: Optional[Callable] = None
        self.on_disconnected: Optional[Callable] = None
        self.on_task_start: Optional[Callable[[str], None]] = None
        self.on_task_complete: Optional[Callable[[str, Dict], None]] = None
        self.on_task_error: Optional[Callable[[str, str], None]] = None
        self.on_status_update: Optional[Callable[[Dict], None]] = None
    
    def initialize(self, agent_id: str, token: str) -> bool:
        """Initialize with credentials"""
        try:
            self.agent_id = agent_id
            self.token = token
            
            # Try to register
            if self.client.register_agent(agent_id, token):
                logger.info(f"✅ Agent registered: {agent_id}")
                self.is_connected = True
                if self.on_connected:
                    self.on_connected()
                return True
            else:
                logger.error("Failed to register agent")
                return False
        except Exception as e:
            logger.error(f"Initialize error: {e}")
            return False
    
    def start(self):
        """Start agent polling loop"""
        if self.is_running:
            logger.warning("Agent already running")
            return
        
        if not self.agent_id or not self.token:
            logger.error("Agent not initialized")
            return
        
        self.is_running = True
        logger.info("🚀 Starting agent service")
        
        # Start polling thread
        self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self.poll_thread.start()
        
        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
    
    def stop(self):
        """Stop agent"""
        self.is_running = False
        logger.info("⏹️ Stopping agent service")
        
        if self.poll_thread:
            self.poll_thread.join(timeout=2)
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2)
    
    def _poll_loop(self):
        """Main polling loop"""
        while self.is_running:
            try:
                # Fetch task from backend
                task_data = self.client.get_task(self.agent_id, self.token)
                
                if task_data:
                    task_id = task_data.get("task_id")
                    command = task_data.get("command")
                    
                    if task_id and command:
                        logger.info(f"📋 Executing task: {task_id}")
                        
                        # Callback
                        if self.on_task_start:
                            self.on_task_start(task_id)
                        
                        # Execute command
                        result = CommandExecutor.execute(
                            command.get("type"),
                            command.get("params", {})
                        )
                        
                        # Submit result
                        error = result.get("error") if not result.get("success") else None
                        self.client.submit_result(
                            self.agent_id,
                            self.token,
                            task_id,
                            result,
                            error
                        )
                        
                        # Callback
                        if result.get("success"):
                            logger.info(f"✅ Task {task_id} completed")
                            if self.on_task_complete:
                                self.on_task_complete(task_id, result)
                        else:
                            logger.error(f"❌ Task {task_id} failed: {error}")
                            if self.on_task_error:
                                self.on_task_error(task_id, error or "Unknown error")
                
                # Poll interval
                time.sleep(3)
            
            except Exception as e:
                logger.error(f"Poll loop error: {e}")
                time.sleep(3)
    
    def _heartbeat_loop(self):
        """Send heartbeat every 30 seconds"""
        while self.is_running:
            try:
                if self.client.heartbeat(self.agent_id, self.token):
                    if not self.is_connected:
                        self.is_connected = True
                        logger.info("✅ Reconnected to backend")
                        if self.on_connected:
                            self.on_connected()
                else:
                    if self.is_connected:
                        self.is_connected = False
                        logger.warning("❌ Backend disconnected")
                        if self.on_disconnected:
                            self.on_disconnected()
                
                time.sleep(30)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                time.sleep(30)
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "agent_id": self.agent_id,
            "is_running": self.is_running,
            "is_connected": self.is_connected,
            "server_url": self.server_url,
        }
    
    def send_command_direct(self, command_type: str, params: Dict[str, Any]) -> Optional[str]:
        """Send command directly to backend"""
        return self.client.send_command(command_type, params)
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status from backend"""
        return self.client.get_status(task_id)
    
    def check_connection(self) -> bool:
        """Check if backend is reachable"""
        return self.client.check_connection()
