"""
REVA Web Server - AI OS Controlling Agent
A web-based interface for controlling your computer with natural language

Run: python main_server.py
Access: http://localhost:8002
"""

import os
import sys
import asyncio
import base64
import json
import subprocess
import platform
import threading
import time
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from loguru import logger
import uvicorn

# Load environment variables
load_dotenv()

# Configure logging
os.makedirs("logs", exist_ok=True)
logger.add("logs/reva_server.log", rotation="10 MB", retention="7 days")

app = FastAPI(
    title="REVA - AI OS Controlling Agent",
    description="Control your computer with natural language commands",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== Models ==============

class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CommandRequest(BaseModel):
    command: str
    model: str = "fast-gpt"


class PermissionRequest(BaseModel):
    permission_type: str


class APIKeyRequest(BaseModel):
    api_key: str


# ============== State Management ==============

class REVAState:
    def __init__(self):
        self.permissions = {
            "screenshot": False,
            "keyboard": False,
            "mouse": False,
            "system": False
        }
        self.api_key_set = bool(os.getenv("OPENAI_API_KEY"))
        self.current_task = None
        self.task_history = []
        self.is_running = False
        self.websocket_clients: List[WebSocket] = []

    def check_all_permissions(self):
        return all(self.permissions.values())


state = REVAState()


# ============== Permission Checking ==============

def check_screenshot_permission():
    """Check if screenshot capability is available"""
    system = platform.system()

    if system == "Linux":
        try:
            result = subprocess.run(["which", "grim"], capture_output=True)
            if result.returncode == 0:
                return True
            result = subprocess.run(["which", "scrot"], capture_output=True)
            if result.returncode == 0:
                return True
            result = subprocess.run(["which", "gnome-screenshot"], capture_output=True)
            return result.returncode == 0
        except:
            return False
    elif system == "Darwin":
        return True
    elif system == "Windows":
        return True
    return False


def check_input_permission():
    """Check if keyboard/mouse control is available"""
    try:
        import pyautogui
        pyautogui.size()
        return True
    except Exception as e:
        logger.warning(f"Input permission check failed: {e}")
        return False


def verify_permissions():
    """Verify all required permissions"""
    state.permissions["screenshot"] = check_screenshot_permission()
    state.permissions["keyboard"] = check_input_permission()
    state.permissions["mouse"] = check_input_permission()
    state.permissions["system"] = True
    return state.permissions


# ============== Screenshot Capture ==============

def capture_screenshot_base64():
    """Capture screenshot and return as base64"""
    screenshot_path = "/tmp/reva_screenshot.png"
    system = platform.system()

    try:
        if system == "Linux":
            result = subprocess.run(f"grim {screenshot_path}", shell=True, capture_output=True)
            if result.returncode != 0:
                result = subprocess.run(f"scrot {screenshot_path}", shell=True, capture_output=True)
            if result.returncode != 0:
                subprocess.run(f"gnome-screenshot -f {screenshot_path}", shell=True, capture_output=True)
        elif system == "Darwin":
            subprocess.run(f"screencapture -x {screenshot_path}", shell=True)
        elif system == "Windows":
            import pyautogui
            screenshot = pyautogui.screenshot()
            screenshot.save(screenshot_path)

        if os.path.exists(screenshot_path):
            with open(screenshot_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        logger.error(f"Screenshot capture failed: {e}")

    return None


# ============== LLM Integration ==============

async def call_groq_api(messages: List[Dict], image_base64: Optional[str] = None):
    """Call Groq API for LLM inference"""
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE_URL", "https://api.groq.com/openai/v1")

    if not api_key:
        raise HTTPException(status_code=400, detail="API key not configured")

    client = OpenAI(api_key=api_key, base_url=base_url)
    model = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

    try:
        if image_base64:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this screenshot and determine the next action."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
                ]
            })

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1024
        )

        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============== Action Execution ==============

def execute_action(action: Dict):
    """Execute a single action on the OS"""
    import pyautogui

    action_type = action.get("operation", "").lower()

    try:
        if action_type == "click":
            x = action.get("x", 0)
            y = action.get("y", 0)
            if isinstance(x, float) and x <= 1:
                screen_w, screen_h = pyautogui.size()
                x = int(screen_w * x)
                y = int(screen_h * y)
            pyautogui.click(x, y)
            return {"success": True, "action": "click", "position": {"x": x, "y": y}}

        elif action_type == "write":
            content = action.get("content", "")
            pyautogui.write(content, interval=0.02)
            return {"success": True, "action": "write", "content": content}

        elif action_type == "press":
            keys = action.get("keys", [])
            if isinstance(keys, list):
                pyautogui.hotkey(*keys)
            else:
                pyautogui.press(keys)
            return {"success": True, "action": "press", "keys": keys}

        elif action_type == "scroll":
            pyautogui.scroll(-5)
            return {"success": True, "action": "scroll"}

        elif action_type == "done":
            return {"success": True, "action": "done", "summary": action.get("summary", "Task completed")}

        else:
            return {"success": False, "error": f"Unknown action: {action_type}"}

    except Exception as e:
        logger.error(f"Action execution failed: {e}")
        return {"success": False, "error": str(e)}


# ============== API Routes ==============

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface"""
    return get_web_interface()


@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "REVA Web Server",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/permissions")
async def get_permissions():
    """Get current permission status"""
    verify_permissions()
    return {
        "permissions": state.permissions,
        "all_granted": state.check_all_permissions(),
        "api_key_set": bool(os.getenv("OPENAI_API_KEY"))
    }


@app.post("/api/permissions/request")
async def request_permission(request: PermissionRequest):
    """Request OS-level permissions"""
    perm_type = request.permission_type

    if perm_type == "all":
        verify_permissions()
        return {"permissions": state.permissions, "all_granted": state.check_all_permissions()}

    if perm_type == "screenshot":
        state.permissions["screenshot"] = check_screenshot_permission()
    elif perm_type in ["keyboard", "mouse"]:
        state.permissions[perm_type] = check_input_permission()

    return {"permission": perm_type, "granted": state.permissions.get(perm_type, False)}


@app.post("/api/key")
async def set_api_key(request: APIKeyRequest):
    """Set or update the Groq API key"""
    api_key = request.api_key.strip()

    if not api_key.startswith("gsk_"):
        raise HTTPException(status_code=400, detail="Invalid Groq API key format")

    env_path = os.path.join(os.path.dirname(__file__), ".env")

    env_content = ""
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
            env_content = "".join([l for l in lines if not l.startswith("OPENAI_API_KEY=")])

    with open(env_path, "w") as f:
        f.write(env_content)
        f.write(f"\nOPENAI_API_KEY='{api_key}'\n")
        if "OPENAI_API_BASE_URL" not in env_content:
            f.write("OPENAI_API_BASE_URL='https://api.groq.com/openai/v1'\n")

    load_dotenv(override=True)
    state.api_key_set = True

    return {"success": True, "message": "API key saved"}


@app.get("/api/key/status")
async def get_key_status():
    """Check if API key is configured"""
    return {
        "configured": bool(os.getenv("OPENAI_API_KEY")),
        "base_url": os.getenv("OPENAI_API_BASE_URL", "https://api.groq.com/openai/v1")
    }


@app.get("/api/screenshot")
async def get_screenshot():
    """Capture and return current screenshot"""
    if not state.permissions.get("screenshot"):
        verify_permissions()
        if not state.permissions.get("screenshot"):
            raise HTTPException(status_code=403, detail="Screenshot permission not granted")

    screenshot_b64 = capture_screenshot_base64()
    if screenshot_b64:
        return {"screenshot": screenshot_b64}
    raise HTTPException(status_code=500, detail="Failed to capture screenshot")


@app.post("/api/execute")
async def execute_command(request: CommandRequest):
    """Execute a natural language command"""
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=400, detail="API key not configured")

    if not state.check_all_permissions():
        verify_permissions()
        if not state.check_all_permissions():
            raise HTTPException(status_code=403, detail="Not all permissions granted")

    command = request.command
    state.is_running = True
    state.current_task = {
        "command": command,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "actions": []
    }

    try:
        screenshot_b64 = capture_screenshot_base64()

        system_prompt = f"""You are REVA, an AI that controls a {platform.system()} computer.
Analyze the screenshot and determine the next action to complete the user's objective.

CRITICAL: You MUST respond with ONLY a valid JSON array. No explanations, no markdown, no text before or after.

Available actions:
1. click - {{"operation": "click", "x": 0.5, "y": 0.5, "thought": "reason"}}
2. write - {{"operation": "write", "content": "text", "thought": "reason"}}
3. press - {{"operation": "press", "keys": ["super"], "thought": "reason"}}
4. scroll - {{"operation": "scroll", "thought": "reason"}}
5. done - {{"operation": "done", "summary": "what was done", "thought": "reason"}}

x and y are percentages (0.0 to 1.0) of screen dimensions.
For keyboard shortcuts: use "super" for Windows/Super key, "ctrl", "alt", "shift".

RESPOND WITH ONLY THE JSON ARRAY. Example response:
[{{"operation": "press", "keys": ["super"], "thought": "Opening app menu"}}]

User objective: {command}"""

        messages = [{"role": "system", "content": system_prompt}]

        response = await call_groq_api(messages, screenshot_b64)

        try:
            response = response.strip()

            # Try to extract JSON from response
            import re

            # Look for JSON array pattern
            json_match = re.search(r'\[[\s\S]*?\](?=\s*$|\s*```)', response)
            if json_match:
                response = json_match.group(0)
            else:
                # Try to find any JSON array in the response
                json_match = re.search(r'\[\s*\{[\s\S]*?\}\s*\]', response)
                if json_match:
                    response = json_match.group(0)

            # Clean markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            response = response.strip()

            actions = json.loads(response)
            if not isinstance(actions, list):
                actions = [actions]

            results = []
            for action in actions:
                result = execute_action(action)
                results.append(result)
                state.current_task["actions"].append({
                    "action": action,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })

                if action.get("operation") == "done":
                    break

                time.sleep(0.5)

            state.current_task["status"] = "completed"
            state.task_history.append(state.current_task)

            return {
                "success": True,
                "command": command,
                "actions": results,
                "message": "Command executed successfully"
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {response}")
            raise HTTPException(status_code=500, detail=f"Invalid LLM response: {str(e)}")

    except Exception as e:
        state.current_task["status"] = "failed"
        state.current_task["error"] = str(e)
        state.task_history.append(state.current_task)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        state.is_running = False
        state.current_task = None


@app.get("/api/history")
async def get_history():
    """Get command execution history"""
    return {"history": state.task_history[-20:]}


@app.get("/api/status")
async def get_status():
    """Get current execution status"""
    return {
        "is_running": state.is_running,
        "current_task": state.current_task,
        "permissions": state.permissions,
        "api_key_set": bool(os.getenv("OPENAI_API_KEY"))
    }


# ============== WebSocket for Real-time Updates ==============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    state.websocket_clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "type": "status",
                "is_running": state.is_running,
                "current_task": state.current_task
            })
    except WebSocketDisconnect:
        state.websocket_clients.remove(websocket)


# ============== Web Interface ==============

def get_web_interface():
    """Return the main web interface HTML"""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>REVA - AI OS Controlling Agent</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }
        .container { max-width: 900px; margin: 0 auto; padding: 40px 20px; }
        header { text-align: center; margin-bottom: 40px; }
        h1 {
            font-size: 3rem;
            background: linear-gradient(135deg, #60A5FA, #A78BFA);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .subtitle { color: #9CA3AF; font-size: 1.1rem; }
        .card {
            background: rgba(17, 24, 39, 0.8);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            border: 1px solid rgba(75, 85, 99, 0.3);
        }
        .card-title {
            font-size: 1.2rem;
            color: #60A5FA;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .permissions-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
        }
        .permission-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            background: rgba(31, 41, 55, 0.8);
            border-radius: 8px;
        }
        .permission-status { width: 12px; height: 12px; border-radius: 50%; }
        .permission-status.granted { background: #10B981; }
        .permission-status.denied { background: #EF4444; }
        .api-key-section { display: flex; gap: 12px; margin-top: 16px; }
        input[type="text"], input[type="password"] {
            flex: 1;
            padding: 12px 16px;
            border: none;
            border-radius: 8px;
            background: rgba(31, 41, 55, 0.8);
            color: #e0e0e0;
            font-size: 1rem;
        }
        input::placeholder { color: #6B7280; }
        .command-input { width: 100%; padding: 16px; font-size: 1.1rem; margin-bottom: 16px; }
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary {
            background: linear-gradient(135deg, #3B82F6, #8B5CF6);
            color: white;
            font-weight: 600;
        }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4); }
        .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .btn-secondary { background: rgba(75, 85, 99, 0.5); color: #e0e0e0; }
        .btn-secondary:hover { background: rgba(75, 85, 99, 0.8); }
        .execute-btn { width: 100%; padding: 16px; font-size: 1.1rem; }
        .screenshot-preview { width: 100%; border-radius: 8px; margin-top: 16px; display: none; }
        .log-container {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 16px;
            max-height: 300px;
            overflow-y: auto;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9rem;
        }
        .log-entry { padding: 4px 0; border-bottom: 1px solid rgba(75, 85, 99, 0.2); }
        .log-entry:last-child { border-bottom: none; }
        .log-time { color: #6B7280; }
        .log-success { color: #10B981; }
        .log-error { color: #EF4444; }
        .log-info { color: #60A5FA; }
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9rem;
        }
        .status-ready { background: rgba(16, 185, 129, 0.2); color: #10B981; }
        .status-running { background: rgba(59, 130, 246, 0.2); color: #60A5FA; }
        .status-error { background: rgba(239, 68, 68, 0.2); color: #EF4444; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .loading { animation: pulse 1.5s infinite; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>REVA</h1>
            <p class="subtitle">AI OS Controlling Agent - Powered by Groq</p>
        </header>

        <div class="card">
            <div class="card-title">
                <span>🔐</span> System Permissions
                <button class="btn-secondary" onclick="checkPermissions()" style="margin-left: auto; padding: 8px 16px;">Refresh</button>
            </div>
            <div class="permissions-grid">
                <div class="permission-item"><span>📸 Screenshot</span><div class="permission-status denied" id="perm-screenshot"></div></div>
                <div class="permission-item"><span>⌨️ Keyboard</span><div class="permission-status denied" id="perm-keyboard"></div></div>
                <div class="permission-item"><span>🖱️ Mouse</span><div class="permission-status denied" id="perm-mouse"></div></div>
                <div class="permission-item"><span>⚙️ System</span><div class="permission-status denied" id="perm-system"></div></div>
            </div>
        </div>

        <div class="card">
            <div class="card-title">
                <span>🔑</span> Groq API Key
                <span id="api-status" class="status-indicator status-error" style="margin-left: auto;">Not Set</span>
            </div>
            <p style="color: #9CA3AF; margin-bottom: 12px;">Get your free API key from <a href="https://console.groq.com" target="_blank" style="color: #60A5FA;">console.groq.com</a></p>
            <div class="api-key-section">
                <input type="password" id="api-key-input" placeholder="Enter your Groq API key (gsk_...)">
                <button class="btn-primary" onclick="saveApiKey()">Save Key</button>
            </div>
        </div>

        <div class="card">
            <div class="card-title"><span>💬</span> Command</div>
            <input type="text" class="command-input" id="command-input" placeholder="Enter your command... (e.g., 'Open Firefox and search for weather')">
            <button class="btn-primary execute-btn" id="execute-btn" onclick="executeCommand()">▶ Execute Command</button>
            <img id="screenshot-preview" class="screenshot-preview" alt="Screenshot preview">
        </div>

        <div class="card">
            <div class="card-title">
                <span>📋</span> Activity Log
                <button class="btn-secondary" onclick="clearLog()" style="margin-left: auto; padding: 8px 16px;">Clear</button>
            </div>
            <div class="log-container" id="log-container">
                <div class="log-entry log-info">Welcome to REVA! Configure your API key and permissions to get started.</div>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = '';

        function log(message, type = 'info') {
            const container = document.getElementById('log-container');
            const time = new Date().toLocaleTimeString();
            const entry = document.createElement('div');
            entry.className = `log-entry log-${type}`;
            entry.innerHTML = `<span class="log-time">[${time}]</span> ${message}`;
            container.appendChild(entry);
            container.scrollTop = container.scrollHeight;
        }

        function clearLog() {
            document.getElementById('log-container').innerHTML = '';
            log('Log cleared', 'info');
        }

        async function checkPermissions() {
            try {
                const response = await fetch(`${API_BASE}/api/permissions`);
                const data = await response.json();

                ['screenshot', 'keyboard', 'mouse', 'system'].forEach(perm => {
                    const el = document.getElementById(`perm-${perm}`);
                    el.className = data.permissions[perm] ? 'permission-status granted' : 'permission-status denied';
                });

                if (data.all_granted) {
                    log('All permissions granted ✓', 'success');
                } else {
                    log('Some permissions missing. Screenshot/input control may not work.', 'error');
                }

                updateApiStatus(data.api_key_set);
            } catch (err) {
                log(`Permission check failed: ${err.message}`, 'error');
            }
        }

        function updateApiStatus(isSet) {
            const el = document.getElementById('api-status');
            if (isSet) {
                el.textContent = 'Configured ✓';
                el.className = 'status-indicator status-ready';
            } else {
                el.textContent = 'Not Set';
                el.className = 'status-indicator status-error';
            }
        }

        async function saveApiKey() {
            const input = document.getElementById('api-key-input');
            const key = input.value.trim();

            if (!key) { log('Please enter an API key', 'error'); return; }
            if (!key.startsWith('gsk_')) { log('Invalid API key format. Groq keys start with gsk_', 'error'); return; }

            try {
                const response = await fetch(`${API_BASE}/api/key`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ api_key: key })
                });

                if (response.ok) {
                    log('API key saved successfully ✓', 'success');
                    input.value = '';
                    updateApiStatus(true);
                } else {
                    const err = await response.json();
                    log(`Failed to save API key: ${err.detail}`, 'error');
                }
            } catch (err) {
                log(`Error saving API key: ${err.message}`, 'error');
            }
        }

        async function executeCommand() {
            const input = document.getElementById('command-input');
            const btn = document.getElementById('execute-btn');
            const command = input.value.trim();

            if (!command) { log('Please enter a command', 'error'); return; }

            btn.disabled = true;
            btn.textContent = '⏳ Processing...';
            btn.classList.add('loading');

            log(`Executing: "${command}"`, 'info');

            try {
                const ssResponse = await fetch(`${API_BASE}/api/screenshot`);
                if (ssResponse.ok) {
                    const ssData = await ssResponse.json();
                    const preview = document.getElementById('screenshot-preview');
                    preview.src = `data:image/png;base64,${ssData.screenshot}`;
                    preview.style.display = 'block';
                }

                const response = await fetch(`${API_BASE}/api/execute`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: command })
                });

                const data = await response.json();

                if (response.ok) {
                    log(`Command completed successfully ✓`, 'success');
                    if (data.actions) {
                        data.actions.forEach(action => {
                            log(`  → ${action.action}: ${JSON.stringify(action)}`, 'info');
                        });
                    }
                    input.value = '';
                } else {
                    log(`Command failed: ${data.detail}`, 'error');
                }
            } catch (err) {
                log(`Execution error: ${err.message}`, 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = '▶ Execute Command';
                btn.classList.remove('loading');
            }
        }

        document.getElementById('command-input').addEventListener('keypress', (e) => { if (e.key === 'Enter') executeCommand(); });
        document.getElementById('api-key-input').addEventListener('keypress', (e) => { if (e.key === 'Enter') saveApiKey(); });

        checkPermissions();
    </script>
</body>
</html>"""


# ============== Main ==============

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 REVA Web Server Starting...")
    print("=" * 60)
    print(f"📍 Open in browser: http://localhost:8002")
    print(f"📚 API Documentation: http://localhost:8002/docs")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
