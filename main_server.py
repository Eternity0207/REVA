"""REVA Web Server"""
import os
import platform
import subprocess
import base64
import json
import re
from datetime import datetime
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
command_history = []

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
    if platform.system() == "Linux":
        subprocess.run(f"grim {path} || scrot {path}", shell=True, capture_output=True)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def execute_action(action):
    import pyautogui
    op = action.get("operation", "").lower()

    if op == "click":
        x, y = action.get("x", 0.5), action.get("y", 0.5)
        if isinstance(x, (int, float)) and x <= 1:
            w, h = pyautogui.size()
            x, y = int(w * x), int(h * y)
        pyautogui.click(int(x), int(y))
        return {"success": True, "action": "click"}
    elif op == "write":
        pyautogui.write(action.get("content", ""), interval=0.02)
        return {"success": True, "action": "write"}
    elif op == "press":
        keys = action.get("keys", [])
        if keys:
            pyautogui.hotkey(*keys)
        return {"success": True, "action": "press"}
    elif op == "scroll":
        pyautogui.scroll(-5)
        return {"success": True, "action": "scroll"}
    elif op == "done":
        return {"success": True, "action": "done", "summary": action.get("summary")}
    return {"success": False, "error": f"Unknown: {op}"}

@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h1>REVA Web Server</h1><p>API at /api/*</p>"

@app.get("/api/health")
async def health():
    return {"status": "healthy", "time": datetime.now().isoformat()}

@app.get("/api/permissions")
async def permissions():
    return {"permissions": check_permissions(), "api_key_set": bool(os.getenv("OPENAI_API_KEY"))}

@app.post("/api/key")
async def save_key(request: APIKeyRequest):
    with open(".env", "w") as f:
        f.write(f"OPENAI_API_KEY='{request.api_key}'\n")
        f.write("OPENAI_API_BASE_URL='https://api.groq.com/openai/v1'\n")
    load_dotenv(override=True)
    return {"success": True}

@app.get("/api/screenshot")
async def screenshot():
    img = capture_screenshot()
    if img:
        return {"screenshot": img, "timestamp": datetime.now().isoformat()}
    raise HTTPException(500, "Screenshot failed")

@app.get("/api/history")
async def history():
    return {"history": command_history[-50:]}

@app.post("/api/execute")
async def execute(request: CommandRequest):
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(400, "API key not set")

    command_history.append({"command": request.command, "time": datetime.now().isoformat()})

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE_URL", "https://api.groq.com/openai/v1")
    )

    img_b64 = capture_screenshot()

    prompt = f"""You are REVA controlling a {platform.system()} computer.
RESPOND WITH ONLY JSON ARRAY.
Actions: click, write, press, scroll, done
Objective: {request.command}"""

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": [
            {"type": "text", "text": "Execute now. JSON only."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
        ]}
    ]

    resp = client.chat.completions.create(model=GROQ_MODEL, messages=messages, max_tokens=1024)
    content = resp.choices[0].message.content.strip()

    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        content = match.group(0)

    actions = json.loads(content)
    results = [execute_action(a) for a in (actions if isinstance(actions, list) else [actions])]

    return {"success": True, "actions": results}

if __name__ == "__main__":
    import uvicorn
    print("REVA Web Server: http://localhost:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)
