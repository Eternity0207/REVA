"""REVA Web Server - Full Implementation with Agent System"""
import os
import platform
import subprocess
import base64
import json
import re
import markdown
from datetime import datetime
from io import BytesIO
from PIL import Image
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from loguru import logger
from openai import OpenAI

# Import REVA core modules
from core import TaskManager, Command, CommandType, Agent
from security import TokenManager, AuthMiddleware
from handlers import CommandHandler

load_dotenv()
os.makedirs("logs", exist_ok=True)
logger.add("logs/server.log", rotation="10 MB")

# Initialize task manager and auth
task_manager = TaskManager()
auth = AuthMiddleware(task_manager)

app = FastAPI(title="REVA", version="3.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class CommandRequest(BaseModel):
    command: str

class APIKeyRequest(BaseModel):
    api_key: str

class AgentRegisterRequest(BaseModel):
    agent_id: str
    token: str
    hostname: str = ""
    os_type: str = ""

class SendCommandRequest(BaseModel):
    command_type: str
    params: dict = {}

class SubmitResultRequest(BaseModel):
    agent_id: str
    token: str
    task_id: str
    result: dict
    error: str = None

class HeartbeatRequest(BaseModel):
    agent_id: str
    token: str


GROQ_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

def check_permissions():
    perms = {"screenshot": False, "keyboard": False, "mouse": False}
    system = platform.system()
    
    # Check screenshot capability
    if system == "Linux":
        for tool in ["grim", "scrot"]:
            if subprocess.run(["which", tool], capture_output=True).returncode == 0:
                perms["screenshot"] = True
                break
    elif system == "Darwin":  # macOS
        try:
            result = subprocess.run(["screencapture", "-x", "/tmp/test.png"], 
                                  capture_output=True, timeout=2)
            if result.returncode == 0:
                perms["screenshot"] = True
                subprocess.run(["rm", "/tmp/test.png"], capture_output=True)
        except:
            pass
    else:  # Windows
        perms["screenshot"] = True
    
    # Check keyboard and mouse control
    system = platform.system()
    
    if system == "Linux":
        # On Linux, check for xdotool first (doesn't need DISPLAY)
        if subprocess.run(["which", "xdotool"], capture_output=True).returncode == 0:
            perms["keyboard"] = perms["mouse"] = True
        else:
            # Try pyautogui with DISPLAY variable
            try:
                # Set DISPLAY if not already set
                env = os.environ.copy()
                if "DISPLAY" not in env:
                    env["DISPLAY"] = ":0"  # Try default display
                
                import pyautogui
                w, h = pyautogui.size()
                if w > 0 and h > 0:
                    perms["keyboard"] = perms["mouse"] = True
            except:
                pass
    elif system == "Darwin":  # macOS
        try:
            result = subprocess.run(["osascript", "-e", 
                                   "tell application \"System Events\" to keystroke \"x\""],
                                  capture_output=True, timeout=2)
            if "not permitted" not in result.stderr.decode().lower():
                perms["keyboard"] = perms["mouse"] = True
        except:
            pass
    else:  # Windows
        try:
            import pyautogui
            w, h = pyautogui.size()
            if w > 0 and h > 0:
                perms["keyboard"] = perms["mouse"] = True
        except:
            pass
    
    return perms

def capture_screenshot():
    path = "/tmp/reva_screenshot.png"
    system = platform.system()

    try:
        if system == "Linux":
            # Try multiple screenshot tools
            for cmd in [f"grim {path}", f"scrot {path}", f"gnome-screenshot -f {path}"]:
                result = subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
                if result.returncode == 0 and os.path.exists(path):
                    logger.debug(f"Screenshot captured with: {cmd.split()[0]}")
                    break
        elif system == "Darwin":  # macOS
            subprocess.run(f"screencapture {path}", shell=True, capture_output=True, timeout=5)
            logger.debug("Screenshot captured with screencapture")
        else:  # Windows
            import pyautogui
            img = pyautogui.screenshot()
            img.save(path)
            logger.debug("Screenshot captured with pyautogui")

        if os.path.exists(path) and os.path.getsize(path) > 0:
            with open(path, "rb") as f:
                data = f.read()
                if data and len(data) > 50:  # Sanity check - PNG should be at least 67 bytes
                    encoded = base64.b64encode(data).decode('utf-8')
                    logger.debug(f"Screenshot encoded: {len(encoded)} bytes")
                    return encoded
    except Exception as e:
        logger.error(f"Screenshot capture error: {e}")

    # If all else fails, create a placeholder 200x200 white PNG using PIL
    logger.warning("Creating placeholder image")
    try:
        img = Image.new('RGB', (200, 200), color='white')
        buf = BytesIO()
        img.save(buf, format='PNG')
        encoded = base64.b64encode(buf.getvalue()).decode('utf-8')
        logger.debug(f"Placeholder created: {len(encoded)} bytes")
        return encoded
    except Exception as e:
        logger.error(f"Failed to create placeholder: {e}")
        return None

def execute_action(action):
    import pyautogui
    import time
    op = action.get("operation", "").lower()

    if op == "click":
        x, y = action.get("x", 0.5), action.get("y", 0.5)
        if isinstance(x, (int, float)) and x <= 1:
            w, h = pyautogui.size()
            x, y = int(w * x), int(h * y)
        pyautogui.click(int(x), int(y))
        return {"success": True, "action": "click", "position": {"x": x, "y": y}}
    elif op == "write":
        content = action.get("content", "")
        pyautogui.write(content, interval=0.02)
        return {"success": True, "action": "write", "content": content}
    elif op == "press":
        keys = action.get("keys", [])
        if keys:
            pyautogui.hotkey(*keys)
        return {"success": True, "action": "press", "keys": keys}
    elif op == "scroll":
        pyautogui.scroll(-5)
        return {"success": True, "action": "scroll"}
    elif op == "done":
        return {"success": True, "action": "done", "summary": action.get("summary", "Complete")}
    return {"success": False, "error": f"Unknown action: {op}"}

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve homepage - detect server URL and show proper UI"""
    # Detect server URL from request
    scheme = request.url.scheme
    netloc = request.url.netloc
    server_url = f"{scheme}://{netloc}"
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>REVA - Remote Execution and Visualization Agent</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #333;
        }}

        .container {{
            max-width: 1200px;
            width: 90%;
        }}

        .hero {{
            text-align: center;
            color: white;
            margin-bottom: 50px;
        }}

        .hero h1 {{
            font-size: 3.5em;
            font-weight: 700;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .hero p {{
            font-size: 1.3em;
            margin-bottom: 10px;
            opacity: 0.95;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }}

        .hero .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 24px;
            margin-bottom: 40px;
        }}

        .card {{
            background: white;
            border-radius: 12px;
            padding: 28px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }}

        .card h3 {{
            color: #667eea;
            margin-bottom: 16px;
            font-size: 1.3em;
        }}

        .card p {{
            color: #666;
            line-height: 1.6;
            margin-bottom: 16px;
        }}

        .credentials {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 12px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.9em;
            margin-bottom: 12px;
        }}

        .copy-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background 0.3s ease;
        }}

        .copy-btn:hover {{
            background: #764ba2;
        }}

        .button {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 14px 32px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: none;
            cursor: pointer;
            margin: 8px;
        }}

        .button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
        }}

        .full-width {{
            width: 100%;
            margin: 0;
        }}

        .doc-links {{
            text-align: center;
            margin-top: 30px;
        }}

        .doc-link {{
            color: white;
            text-decoration: none;
            margin: 0 15px;
            font-weight: 500;
            border-bottom: 2px solid transparent;
            transition: border-color 0.3s ease;
        }}

        .doc-link:hover {{
            border-bottom-color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>🤖 REVA</h1>
            <p>Remote Execution & Visualization Agent</p>
            <p class="subtitle">Control your OS with AI | Distributed Agent System</p>
        </div>

        <div class="cards">
            <div class="card">
                <h3>📥 Download App</h3>
                <p>Get the standalone REVA desktop application that connects to this server.</p>
                <button class="button full-width" onclick="downloadApp()">
                    ⬇️ Download REVA App
                </button>
                <p style="color: #999; font-size: 0.9em; margin-top: 10px;">
                    Works on Windows, macOS, and Linux
                </p>
            </div>

            <div class="card">
                <h3>🔑 Agent Credentials</h3>
                <p>Use these credentials in the REVA app to connect:</p>
                <div class="credentials">
                    Server: <span id="server-url">{server_url}</span>
                    <button class="copy-btn" onclick="copy('server-url')">Copy</button>
                </div>
                <div class="credentials">
                    ID: <span id="agent-id">my-agent</span>
                    <button class="copy-btn" onclick="copy('agent-id')">Copy</button>
                </div>
                <div class="credentials">
                    Token: <span id="agent-token">my-secret-token</span>
                    <button class="copy-btn" onclick="copy('agent-token')">Copy</button>
                </div>
            </div>

            <div class="card">
                <h3>📚 Documentation</h3>
                <p>Learn how to use REVA and set up your agent.</p>
                <button class="button full-width" onclick="location.href='/guide'" style="background: #667eea;">
                    📖 Setup Guide
                </button>
                <button class="button full-width" onclick="location.href='/documentation'" style="background: #764ba2; margin-top: 8px;">
                    📋 Full Documentation
                </button>
            </div>
        </div>

        <div style="text-align: center; color: white; margin-top: 40px;">
            <p>🟢 <strong>Server Status:</strong> Ready | <strong>Agent System:</strong> Active</p>
            <p style="font-size: 0.9em; opacity: 0.8; margin-top: 10px;">
                Version 3.0 | Built for distributed OS automation
            </p>
        </div>
    </div>

    <script>
        function copy(elementId) {{
            const text = document.getElementById(elementId).textContent;
            navigator.clipboard.writeText(text).then(() => {{
                alert('Copied to clipboard!');
            }}).catch(() => {{
                prompt('Copy this:', text);
            }});
        }}

        function downloadApp() {{
            const fileUrl = '/dist/REVA';
            const xhr = new XMLHttpRequest();
            xhr.open('HEAD', fileUrl, true);
            xhr.onload = function() {{
                if (xhr.status === 200) {{
                    window.location.href = fileUrl;
                }} else {{
                    alert('App not available yet. Please try again later.');
                }}
            }};
            xhr.onerror = function() {{
                alert('Error checking app availability');
            }};
            xhr.send();
        }}
    </script>
</body>
</html>"""
    return html


# ====================== AGENT ENDPOINTS ======================

@app.post("/api/agent/register")
async def agent_register(req: AgentRegisterRequest):
    """Register an agent"""
    try:
        agent = Agent(
            agent_id=req.agent_id,
            token=req.token,
            hostname=req.hostname,
            os_type=req.os_type,
        )
        task_manager.register_agent(agent)
        logger.info(f"✅ Agent registered: {req.agent_id}")
        return {"success": True, "message": "Agent registered"}
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(500, str(e))

@app.post("/api/agent/heartbeat")
async def agent_heartbeat(req: HeartbeatRequest):
    """Agent heartbeat"""
    if not auth.verify_agent_token(req.agent_id, req.token):
        raise HTTPException(401, "Invalid credentials")
    
    task_manager.update_agent_heartbeat(req.agent_id)
    return {"success": True}

@app.get("/api/agent/get-task")
async def agent_get_task(x_agent_id: str = Header(None), x_agent_token: str = Header(None)):
    """Fetch next task for agent"""
    if not x_agent_id or not x_agent_token:
        raise HTTPException(400, "Missing agent headers")
    
    if not auth.verify_agent_token(x_agent_id, x_agent_token):
        raise HTTPException(401, "Invalid credentials")
    
    task = task_manager.get_agent_task(x_agent_id)
    
    if not task:
        return {}  # Empty response means no task
    
    return {
        "task_id": task.task_id,
        "command": task.command.to_dict(),
    }

@app.post("/api/agent/submit-result")
async def agent_submit_result(req: SubmitResultRequest):
    """Agent submits task result"""
    if not auth.verify_agent_token(req.agent_id, req.token):
        raise HTTPException(401, "Invalid credentials")
    
    success = task_manager.submit_result(req.task_id, req.result, req.error)
    
    if not success:
        raise HTTPException(404, "Task not found")
    
    logger.info(f"✅ Task {req.task_id} result submitted")
    return {"success": True}

@app.get("/api/agent/status")
async def agent_status(agent_id: str):
    """Get agent status"""
    status = task_manager.get_agent_status(agent_id)
    return status

@app.get("/api/agents")
async def list_agents():
    """List all agents"""
    agents = task_manager.list_agents()
    return {"agents": agents}

# ====================== UI ENDPOINTS ======================

@app.post("/api/send-command")
async def send_command(req: SendCommandRequest):
    """Send a structured command to first available agent"""
    try:
        # Get first online agent
        agents = task_manager.list_agents()
        available_agents = [a for a in agents if a["status"] == "online"]
        
        if not available_agents:
            raise HTTPException(503, "No agents available")
        
        agent_id = available_agents[0]["agent_id"]
        
        # Create command
        command = Command(
            type=CommandType(req.command_type),
            params=req.params
        )
        
        # Create task
        task = task_manager.create_task(agent_id, command)
        
        logger.info(f"📋 Task created: {task.task_id} for {agent_id}")
        
        return {
            "task_id": task.task_id,
            "agent_id": agent_id,
            "status": task.status.value
        }
    except Exception as e:
        logger.error(f"Send command error: {e}")
        raise HTTPException(400, str(e))

@app.get("/api/status/{task_id}")
async def task_status(task_id: str):
    """Get task status"""
    status = task_manager.get_task_status(task_id)
    
    if not status:
        raise HTTPException(404, "Task not found")
    
    return status

@app.get("/api/health")
async def health():
    return {"status": "healthy", "time": datetime.now().isoformat()}

@app.get("/api/permissions")
async def permissions():
    return {"permissions": check_permissions(), "api_key_set": bool(os.getenv("OPENAI_API_KEY"))}

@app.get("/api/verify-capabilities")
async def verify_capabilities():
    perms = check_permissions()
    all_ok = perms.get("screenshot") and perms.get("keyboard") and perms.get("mouse")
    missing = [k for k, v in perms.items() if not v]
    return {
        "all_available": all_ok,
        "permissions": perms,
        "missing": missing,
        "message": "All capabilities available" if all_ok else f"Missing: {', '.join(missing)}"
    }

@app.post("/api/key")
async def save_key(request: APIKeyRequest):
    key = request.api_key.strip()
    if not key.startswith("gsk_"):
        raise HTTPException(400, "Invalid Groq API key")
    with open(".env", "w") as f:
        f.write(f"OPENAI_API_KEY='{key}'\n")
        f.write("OPENAI_API_BASE_URL='https://api.groq.com/openai/v1'\n")
    load_dotenv(override=True)
    return {"success": True}

@app.get("/api/screenshot")
async def screenshot():
    img = capture_screenshot()
    if img:
        return {"screenshot": img}
    raise HTTPException(500, "Screenshot failed")

@app.post("/api/execute")
async def execute(request: CommandRequest):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(400, "API key not configured")

    perms = check_permissions()
    if not all(perms.values()):
        raise HTTPException(403, f"System permissions not available: {[k for k,v in perms.items() if not v]}")

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE_URL", "https://api.groq.com/openai/v1")
    )

    img_b64 = capture_screenshot()
    if not img_b64:
        raise HTTPException(500, "Failed to capture screenshot")

    prompt = f"""You are REVA controlling a {platform.system()} computer.
CRITICAL: Respond with ONLY a JSON array. No explanations.

Actions:
1. click - {{"operation": "click", "x": 0.5, "y": 0.5, "thought": "reason"}}
2. write - {{"operation": "write", "content": "text", "thought": "reason"}}
3. press - {{"operation": "press", "keys": ["super"], "thought": "reason"}}
4. scroll - {{"operation": "scroll", "thought": "reason"}}
5. done - {{"operation": "done", "summary": "what was done", "thought": "reason"}}

x, y are percentages (0.0 to 1.0).
Example: [{{"operation": "press", "keys": ["super"], "thought": "Opening menu"}}]

Objective: {request.command}"""

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": [
            {"type": "text", "text": "Execute now. JSON array only."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
        ]}
    ]

    try:
        resp = client.chat.completions.create(model=GROQ_MODEL, messages=messages, max_tokens=1024)
        content = resp.choices[0].message.content.strip()
        logger.debug(f"LLM response: {content[:200]}...")

        # Extract JSON
        match = re.search(r'\[\s*\{[\s\S]*?\}\s*\]', content)
        if match:
            content = match.group(0)

        logger.debug(f"Extracted JSON: {content[:200]}...")
        actions = json.loads(content)
        if not isinstance(actions, list):
            actions = [actions]

        results = []
        for action in actions:
            result = execute_action(action)
            results.append(result)
            if action.get("operation") == "done":
                break


        return {"success": True, "command": request.command, "actions": results}

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        raise HTTPException(500, f"Invalid LLM response: {str(e)}")
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Execute error: {error_msg}")
        raise HTTPException(500, error_msg)


# ====================== DOCUMENTATION ENDPOINTS ======================

@app.get("/guide", response_class=HTMLResponse)
async def guide():
    """Render GUIDE.md as styled HTML"""
    try:
        with open("GUIDE.md", "r") as f:
            content = f.read()
        html_content = markdown.markdown(content, extensions=['extra', 'codehilite'])
    except FileNotFoundError:
        html_content = "<p>Guide not found</p>"
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>REVA Setup Guide</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 40px 20px; color: #333; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }}
        h1 {{ color: #667eea; margin-bottom: 30px; border-bottom: 3px solid #667eea; padding-bottom: 15px; }}
        h2 {{ color: #764ba2; margin-top: 30px; margin-bottom: 15px; }}
        h3 {{ color: #667eea; margin-top: 20px; margin-bottom: 10px; }}
        code {{ background: #f0f4ff; padding: 2px 6px; border-radius: 4px; font-family: 'Monaco', 'Courier New', monospace; }}
        pre {{ background: #1a1a2e; color: #e0e0e0; padding: 16px; border-radius: 8px; overflow-x: auto; margin: 15px 0; }}
        pre code {{ background: none; padding: 0; color: #e0e0e0; }}
        blockquote {{ border-left: 4px solid #667eea; padding-left: 16px; margin: 20px 0; color: #666; }}
        a {{ color: #667eea; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .back-link {{ display: inline-block; margin-bottom: 20px; padding: 10px 20px; background: #667eea; color: white; border-radius: 6px; }}
        .back-link:hover {{ background: #764ba2; }}
        li {{ margin-left: 20px; margin-bottom: 8px; line-height: 1.6; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #f0f4ff; color: #667eea; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Back to Home</a>
        {html_content}
        <a href="/" class="back-link" style="margin-top: 30px;">← Back to Home</a>
    </div>
</body>
</html>"""


@app.get("/documentation", response_class=HTMLResponse)
async def documentation():
    """Render README.md as styled HTML"""
    try:
        with open("README.md", "r") as f:
            content = f.read()
        html_content = markdown.markdown(content, extensions=['extra', 'codehilite'])
    except FileNotFoundError:
        html_content = "<p>Documentation not found</p>"
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>REVA Documentation</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 40px 20px; color: #333; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }}
        h1 {{ color: #667eea; margin-bottom: 30px; border-bottom: 3px solid #667eea; padding-bottom: 15px; }}
        h2 {{ color: #764ba2; margin-top: 30px; margin-bottom: 15px; }}
        h3 {{ color: #667eea; margin-top: 20px; margin-bottom: 10px; }}
        code {{ background: #f0f4ff; padding: 2px 6px; border-radius: 4px; font-family: 'Monaco', 'Courier New', monospace; }}
        pre {{ background: #1a1a2e; color: #e0e0e0; padding: 16px; border-radius: 8px; overflow-x: auto; margin: 15px 0; }}
        pre code {{ background: none; padding: 0; color: #e0e0e0; }}
        blockquote {{ border-left: 4px solid #667eea; padding-left: 16px; margin: 20px 0; color: #666; }}
        a {{ color: #667eea; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .back-link {{ display: inline-block; margin-bottom: 20px; padding: 10px 20px; background: #667eea; color: white; border-radius: 6px; }}
        .back-link:hover {{ background: #764ba2; }}
        li {{ margin-left: 20px; margin-bottom: 8px; line-height: 1.6; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #f0f4ff; color: #667eea; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-link">← Back to Home</a>
        {html_content}
        <a href="/" class="back-link" style="margin-top: 30px;">← Back to Home</a>
    </div>
</body>
</html>"""


# ====================== STATIC FILES & APP DOWNLOAD ======================

# Mount static files directory directly at /dist
if os.path.exists("dist"):
    try:
        app.mount("/dist", StaticFiles(directory="dist"), name="dist")
    except Exception as e:
        logger.error(f"Failed to mount /dist: {e}")

if __name__ == "__main__":
    import uvicorn
    
    # Check and request permissions on startup
    print("=" * 50)
    print("Checking system permissions...")
    print("=" * 50)
    
    perms = check_permissions()
    for perm, status in perms.items():
        status_str = "✅ Available" if status else "❌ Not Available"
        print(f"  {perm.capitalize()}: {status_str}")
    
    if not all(perms.values()):
        missing = [k for k, v in perms.items() if not v]
        print("\n⚠️  Missing capabilities:", ", ".join(missing))
        print("\nTo enable these features:")
        
        if platform.system() == "Linux":
            if "screenshot" in missing:
                print("  • Screenshot: sudo apt install grim scrot")
            if "keyboard" in missing or "mouse" in missing:
                print("  • Keyboard/Mouse: sudo apt install python3-pip xdotool")
                print("                   pip install pyautogui xlib")
        elif platform.system() == "Darwin":
            print("  • macOS: Go to System Preferences > Security & Privacy > Accessibility")
            print("           Add your terminal/IDE to the allowed apps list")
        elif platform.system() == "Windows":
            print("  • Windows: Run the app as Administrator")
        
        print("\nStarting anyway (will fail on execute)...\n")
    else:
        print("\n✅ All permissions available!\n")
    
    print("=" * 50)
    print("REVA Web Server: http://localhost:8002")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8002)
