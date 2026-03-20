"""REVA Web Server - Full Implementation"""
import os
import platform
import subprocess
import base64
import json
import re
from datetime import datetime
from io import BytesIO
from PIL import Image
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from loguru import logger
from openai import OpenAI

load_dotenv()
os.makedirs("logs", exist_ok=True)
logger.add("logs/server.log", rotation="10 MB")

app = FastAPI(title="REVA", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class CommandRequest(BaseModel):
    command: str

class APIKeyRequest(BaseModel):
    api_key: str

GROQ_MODEL = os.getenv("GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

def check_permissions():
    perms = {"screenshot": False, "keyboard": False, "mouse": False}
    if platform.system() == "Linux":
        for tool in ["grim", "scrot"]:
            if subprocess.run(["which", tool], capture_output=True).returncode == 0:
                perms["screenshot"] = True
                break
    else:
        perms["screenshot"] = True
    try:
        import pyautogui
        pyautogui.size()
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
    return """<!DOCTYPE html>
<html><head><title>REVA</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui;background:linear-gradient(135deg,#1a1a2e,#16213e);min-height:100vh;color:#e0e0e0}
.container{max-width:800px;margin:0 auto;padding:40px 20px}
h1{font-size:3rem;background:linear-gradient(135deg,#60A5FA,#A78BFA);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;margin-bottom:10px}
.subtitle{text-align:center;color:#9CA3AF;margin-bottom:30px}
.card{background:rgba(17,24,39,0.8);border-radius:16px;padding:24px;margin-bottom:20px}
.card-title{font-size:1.2rem;color:#60A5FA;margin-bottom:16px}
input{width:100%;padding:14px;border:none;border-radius:8px;background:#1F2937;color:#e0e0e0;font-size:1rem;margin-bottom:12px}
button{padding:14px 24px;border:none;border-radius:8px;font-size:1rem;cursor:pointer;width:100%;margin-bottom:8px}
.btn-primary{background:linear-gradient(135deg,#3B82F6,#8B5CF6);color:white;font-weight:600}
.btn-secondary{background:#374151;color:#e0e0e0}
.log{background:#000;border-radius:8px;padding:16px;max-height:200px;overflow-y:auto;font-family:monospace;font-size:0.9rem}
.status{display:inline-block;width:12px;height:12px;border-radius:50%;margin-right:8px}
.status.ok{background:#10B981}
.status.err{background:#EF4444}
</style></head>
<body><div class="container">
<h1>REVA</h1>
<p class="subtitle">AI OS Controlling Agent</p>
<div class="card">
<div class="card-title">Permissions</div>
<div id="perms"></div>
</div>
<div class="card">
<div class="card-title">API Key</div>
<input type="password" id="key" placeholder="gsk_...">
<button class="btn-primary" onclick="saveKey()">Save Key</button>
</div>
<div class="card">
<div class="card-title">Command</div>
<input type="text" id="cmd" placeholder="Enter command...">
<button class="btn-primary" onclick="execute()">Execute</button>
</div>
<div class="card">
<div class="card-title">Log</div>
<div class="log" id="log">Ready.</div>
</div>
</div>
<script>
function log(msg,type='info'){document.getElementById('log').innerHTML+=`<div style="color:${type=='error'?'#F87171':'#60A5FA'}">[${new Date().toLocaleTimeString()}] ${msg}</div>`}
async function checkPerms(){
const r=await fetch('/api/permissions');const d=await r.json();
let h='';for(let k in d.permissions){h+=`<span class="status ${d.permissions[k]?'ok':'err'}"></span>${k} `}
h+=`<br><span class="status ${d.api_key_set?'ok':'err'}"></span>API Key`;
document.getElementById('perms').innerHTML=h;
}
async function saveKey(){
const k=document.getElementById('key').value;
if(!k.startsWith('gsk_')){log('Invalid key format','error');return}
const r=await fetch('/api/key',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({api_key:k})});
if(r.ok){log('Key saved');checkPerms()}else{log('Save failed','error')}
}
async function execute(){
const c=document.getElementById('cmd').value;if(!c){log('Enter command','error');return}
log('Executing: '+c);
try{
const r=await fetch('/api/execute',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:c})});
const d=await r.json();
if(r.ok){log('Success: '+JSON.stringify(d.actions))}else{log(d.detail,'error')}
}catch(e){log(e.message,'error')}
}
document.getElementById('cmd').addEventListener('keypress',e=>{if(e.key=='Enter')execute()});
checkPerms();
</script></body></html>"""

@app.get("/api/health")
async def health():
    return {"status": "healthy", "time": datetime.now().isoformat()}

@app.get("/api/permissions")
async def permissions():
    return {"permissions": check_permissions(), "api_key_set": bool(os.getenv("OPENAI_API_KEY"))}

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
        raise HTTPException(403, "Permissions not granted")

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
    print("=" * 50)
    print("REVA Web Server: http://localhost:8002")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8002)
