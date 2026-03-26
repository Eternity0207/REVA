"""REVA Web Server - Full Implementation with Agent System"""
import os
import platform
import subprocess
import base64
import json
import re
from datetime import datetime
from io import BytesIO
from typing import Optional
from PIL import Image
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from loguru import logger
from openai import OpenAI
import markdown

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

# Serve static files if they exist
if os.path.exists("dist"):
    app.mount("/dist", StaticFiles(directory="dist"), name="dist")

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
    error: Optional[str] = None

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
async def root():
    """Serve the main landing page"""
    if os.path.exists("index.html"):
        with open("index.html", "r") as f:
            return f.read()
    # Fallback if index.html doesn't exist
    return HTMLResponse(content="<h1>REVA - Remote Execution Agent</h1><p>index.html not found</p>", status_code=200)


@app.get("/docs", response_class=HTMLResponse)
async def show_documentation(request: Request):
    """Display full documentation from README.md"""
    if not os.path.exists("README.md"):
        return HTMLResponse(content="<h1>Documentation not found</h1>", status_code=404)
    
    with open("README.md", "r") as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(md_content, extensions=['extra', 'codehilite'])
    
    # Get the server URL from request
    server_url = f"{request.url.scheme}://{request.url.netloc}"
    
    # Create styled HTML page
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>REVA Documentation</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 40px 20px;
                color: #333;
            }}
            
            .container {{
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                padding: 50px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            
            .back-link {{
                display: inline-block;
                color: #667eea;
                text-decoration: none;
                font-weight: 600;
                margin-bottom: 30px;
                transition: all 0.3s;
            }}
            
            .back-link:hover {{
                color: #764ba2;
                transform: translateX(-3px);
            }}
            
            h1, h2, h3, h4, h5, h6 {{
                color: #667eea;
                margin-top: 30px;
                margin-bottom: 15px;
                border-bottom: 2px solid #f0f0f0;
                padding-bottom: 10px;
            }}
            
            h1 {{
                font-size: 2.5em;
                margin-top: 0;
                border-bottom: 3px solid #667eea;
            }}
            
            h2 {{
                font-size: 1.8em;
            }}
            
            h3 {{
                font-size: 1.4em;
            }}
            
            p {{
                line-height: 1.8;
                margin-bottom: 15px;
                color: #555;
            }}
            
            ul, ol {{
                margin-left: 30px;
                margin-bottom: 15px;
            }}
            
            li {{
                margin-bottom: 8px;
                color: #555;
                line-height: 1.6;
            }}
            
            code {{
                background: #f5f5f5;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                color: #d32f2f;
                font-size: 0.9em;
            }}
            
            pre {{
                background: #1a1a2e;
                color: #60a5fa;
                padding: 20px;
                border-radius: 8px;
                overflow-x: auto;
                margin: 20px 0;
                border-left: 4px solid #667eea;
                font-size: 0.9em;
                line-height: 1.5;
            }}
            
            pre code {{
                background: none;
                color: inherit;
                padding: 0;
                border-radius: 0;
                font-size: inherit;
            }}
            
            blockquote {{
                border-left: 4px solid #667eea;
                padding-left: 20px;
                margin-left: 0;
                margin-bottom: 15px;
                color: #666;
                font-style: italic;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            
            th {{
                background: #f0f4ff;
                color: #667eea;
                font-weight: 600;
            }}
            
            tr:nth-child(even) {{
                background: #f9f9f9;
            }}
            
            a {{
                color: #667eea;
                text-decoration: none;
                font-weight: 500;
                transition: all 0.3s;
            }}
            
            a:hover {{
                color: #764ba2;
                text-decoration: underline;
            }}
            
            em, strong {{
                color: #667eea;
            }}
            
            .toc {{
                background: #f0f4ff;
                border: 2px solid #e0e0f5;
                border-radius: 8px;
                padding: 20px;
                margin: 30px 0;
            }}
            
            .toc h3 {{
                margin-top: 0;
                color: #667eea;
            }}
            
            .toc ul {{
                list-style: none;
                margin-left: 0;
            }}
            
            .toc li {{
                margin: 8px 0;
            }}
            
            .toc a {{
                color: #667eea;
            }}
            
            @media (max-width: 768px) {{
                .container {{
                    padding: 30px 20px;
                }}
                
                h1 {{
                    font-size: 1.8em;
                }}
                
                h2 {{
                    font-size: 1.3em;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Home</a>
            <div class="documentation-content">
                {html_content}
            </div>
            <hr style="margin: 40px 0; border: none; border-top: 2px solid #f0f0f0;">
            <p style="text-align: center; color: #999; font-size: 0.9em; margin-top: 40px;">
                Server: <code>{server_url}</code> | Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </div>
    </body>
    </html>
    """
    
    return styled_html


@app.get("/guide", response_class=HTMLResponse)
async def show_guide(request: Request):
    """Display quick start guide from GUIDE.md"""
    if not os.path.exists("GUIDE.md"):
        return HTMLResponse(content="<h1>Guide not found</h1>", status_code=404)
    
    with open("GUIDE.md", "r") as f:
        md_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(md_content, extensions=['extra', 'codehilite'])
    
    # Get the server URL from request
    server_url = f"{request.url.scheme}://{request.url.netloc}"
    
    # Create styled HTML page
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>REVA Quick Start Guide</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 40px 20px;
                color: #333;
            }}
            
            .container {{
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                padding: 50px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}
            
            .back-link {{
                display: inline-block;
                color: #667eea;
                text-decoration: none;
                font-weight: 600;
                margin-bottom: 30px;
                transition: all 0.3s;
            }}
            
            .back-link:hover {{
                color: #764ba2;
                transform: translateX(-3px);
            }}
            
            h1, h2, h3, h4, h5, h6 {{
                color: #667eea;
                margin-top: 30px;
                margin-bottom: 15px;
                border-bottom: 2px solid #f0f0f0;
                padding-bottom: 10px;
            }}
            
            h1 {{
                font-size: 2.5em;
                margin-top: 0;
                border-bottom: 3px solid #667eea;
            }}
            
            h2 {{
                font-size: 1.8em;
            }}
            
            h3 {{
                font-size: 1.4em;
            }}
            
            p {{
                line-height: 1.8;
                margin-bottom: 15px;
                color: #555;
            }}
            
            ul, ol {{
                margin-left: 30px;
                margin-bottom: 15px;
            }}
            
            li {{
                margin-bottom: 8px;
                color: #555;
                line-height: 1.6;
            }}
            
            code {{
                background: #f5f5f5;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                color: #d32f2f;
                font-size: 0.9em;
            }}
            
            pre {{
                background: #1a1a2e;
                color: #60a5fa;
                padding: 20px;
                border-radius: 8px;
                overflow-x: auto;
                margin: 20px 0;
                border-left: 4px solid #667eea;
                font-size: 0.9em;
                line-height: 1.5;
            }}
            
            pre code {{
                background: none;
                color: inherit;
                padding: 0;
                border-radius: 0;
                font-size: inherit;
            }}
            
            blockquote {{
                border-left: 4px solid #667eea;
                padding-left: 20px;
                margin-left: 0;
                margin-bottom: 15px;
                color: #666;
                font-style: italic;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            
            th {{
                background: #f0f4ff;
                color: #667eea;
                font-weight: 600;
            }}
            
            tr:nth-child(even) {{
                background: #f9f9f9;
            }}
            
            a {{
                color: #667eea;
                text-decoration: none;
                font-weight: 500;
                transition: all 0.3s;
            }}
            
            a:hover {{
                color: #764ba2;
                text-decoration: underline;
            }}
            
            em, strong {{
                color: #667eea;
            }}
            
            .step-box {{
                background: #f0f4ff;
                border: 2px solid #e0e0f5;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }}
            
            .step-box h3 {{
                margin-top: 0;
                color: #667eea;
            }}
            
            @media (max-width: 768px) {{
                .container {{
                    padding: 30px 20px;
                }}
                
                h1 {{
                    font-size: 1.8em;
                }}
                
                h2 {{
                    font-size: 1.3em;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Home</a>
            <div class="guide-content">
                {html_content}
            </div>
            <hr style="margin: 40px 0; border: none; border-top: 2px solid #f0f0f0;">
            <p style="text-align: center; color: #999; font-size: 0.9em; margin-top: 40px;">
                Server: <code>{server_url}</code> | Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
        </div>
    </body>
    </html>
    """
    
    return styled_html


@app.get("/api/config")
async def get_config(request: Request):
    """Get server configuration including auto-detected URL"""
    server_url = f"{request.url.scheme}://{request.url.netloc}"
    return {
        "server_url": server_url,
        "agent_id": "my-agent",
        "token": "my-secret-token",
        "timestamp": datetime.now().isoformat()
    }

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
