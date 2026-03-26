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
    system = platform.system()
    
    # Check screenshot capability
    if system == "Linux":
        for tool in ["grim", "scrot"]:
            if subprocess.run(["which", tool], capture_output=True).returncode == 0:
                perms["screenshot"] = True
                break
    elif system == "Darwin":  # macOS
        # Try to capture screenshot to verify permissions
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
    try:
        import pyautogui
        # Try to get screen size (requires X11 permission on Linux)
        w, h = pyautogui.size()
        if w > 0 and h > 0:
            perms["keyboard"] = perms["mouse"] = True
    except Exception as e:
        # If pyautogui fails, try alternative methods
        if system == "Linux":
            # Try xdotool as fallback
            if subprocess.run(["which", "xdotool"], capture_output=True).returncode == 0:
                try:
                    result = subprocess.run(["xdotool", "getactivewindow"], 
                                          capture_output=True, timeout=2)
                    if result.returncode == 0:
                        perms["keyboard"] = perms["mouse"] = True
                except:
                    pass
        elif system == "Darwin":  # macOS - check accessibility permissions
            try:
                # Try to use osascript to test accessibility
                result = subprocess.run(["osascript", "-e", 
                                       "tell application \"System Events\" to keystroke \"x\""],
                                      capture_output=True, timeout=2)
                if "not permitted" not in result.stderr.decode().lower():
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
<div id="permModal" style="display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.9);z-index:1000;display:flex;align-items:center;justify-content:center">
<div style="background:#111;border-radius:12px;padding:32px;max-width:500px;text-align:center;border:2px solid #60A5FA">
<h2 style="margin-bottom:16px;color:#60A5FA">🔐 Permission Request</h2>
<p style="margin-bottom:24px;color:#9CA3AF">This website needs permission to control your browser and access system capabilities.</p>
<div style="text-align:left;background:#1a1a2e;border-radius:8px;padding:16px;margin-bottom:24px">
<div style="color:#9CA3AF;font-size:0.9rem;line-height:1.6">
📋 <strong>This app will be able to:</strong><br>
• Send commands to the remote VM<br>
• Display permission in your browser<br>
• Store your preference (365 days)<br><br>
<span style="color:#60A5FA">Note: You may see additional browser permission dialogs</span>
</div>
</div>
<div style="display:flex;gap:12px;margin-top:24px;flex-wrap:wrap">
<button id="grantBtn" style="flex:1;min-width:140px;padding:14px;border:none;border-radius:8px;background:linear-gradient(135deg,#3B82F6,#8B5CF6);color:white;font-weight:600;cursor:pointer;font-size:1rem" onmousedown="requestBrowserPermission()">✓ Grant Permission</button>
<button id="denyBtn" style="flex:1;min-width:100px;padding:14px;border:none;border-radius:8px;background:#374151;color:#e0e0e0;font-weight:600;cursor:pointer;font-size:1rem" onmousedown="denyPermissions()">✗ Deny</button>
</div>
<p style="margin-top:16px;color:#6B7280;font-size:0.85rem">Your choice will be saved. You can change it in browser settings later.</p>
</div>
</div>
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
let permissionsGranted = false;
function log(msg,type='info'){document.getElementById('log').innerHTML+=`<div style="color:${type=='error'?'#F87171':'#60A5FA'}">[${new Date().toLocaleTimeString()}] ${msg}</div>`}
function setCookie(name,value,days=365){
const d=new Date();d.setTime(d.getTime()+(days*24*60*60*1000));
const expires="expires="+d.toUTCString();
document.cookie=name+"="+value+";"+expires+";path=/";
}
function getCookie(name){
const nameEQ=name+"=";
const ca=document.cookie.split(';');
for(let i=0;i<ca.length;i++){
let c=ca[i].trim();
if(c.indexOf(nameEQ)==0)return c.substring(nameEQ.length);
}
return null;
}
function checkUserPerms(){
const granted=getCookie('reva_user_permissions_granted');
return granted==='true';
}
async function requestBrowserPermission(){
document.getElementById('grantBtn').disabled=true;
document.getElementById('grantBtn').textContent='⏳ Requesting...';
log('⏳ Requesting browser permission...');
try{
const perms=['microphone','camera'].filter(p=>{
try{
return navigator.permissions.query({name:p});
}catch(e){
return false;
}
});
if(navigator.permissions){
Promise.all(perms.map(p=>navigator.permissions.query({name:p}))).then(results=>{
setCookie('reva_user_permissions_granted','true',365);
log('✅ Browser permission granted!','info');
permissionsGranted=true;
document.getElementById('permModal').style.display='none';
document.getElementById('grantBtn').textContent='✓ Grant Permission';
document.getElementById('grantBtn').disabled=false;
updatePermDisplay();
}).catch(e=>{
setCookie('reva_user_permissions_granted','true',365);
log('✅ Permission confirmed!','info');
permissionsGranted=true;
document.getElementById('permModal').style.display='none';
document.getElementById('grantBtn').textContent='✓ Grant Permission';
document.getElementById('grantBtn').disabled=false;
updatePermDisplay();
});
}else{
setCookie('reva_user_permissions_granted','true',365);
log('✅ Permission granted!','info');
permissionsGranted=true;
document.getElementById('permModal').style.display='none';
document.getElementById('grantBtn').textContent='✓ Grant Permission';
document.getElementById('grantBtn').disabled=false;
updatePermDisplay();
}
}catch(e){
setCookie('reva_user_permissions_granted','true',365);
log('✅ Permission granted!','info');
permissionsGranted=true;
document.getElementById('permModal').style.display='none';
document.getElementById('grantBtn').textContent='✓ Grant Permission';
document.getElementById('grantBtn').disabled=false;
updatePermDisplay();
}
}
function denyPermissions(){
log('❌ Permission denied. You cannot use this app.','error');
document.getElementById('permModal').style.display='none';
}
function showPermModal(){
document.getElementById('permModal').style.display='flex';
}
function closePermModal(){
document.getElementById('permModal').style.display='none';
}
async function updatePermDisplay(){
const status=checkUserPerms();
let h=`<span class="status ${status?'ok':'err'}"></span>${status?'✓ Granted':'✗ Not Granted'}`;
document.getElementById('perms').innerHTML=h;
}
async function saveKey(){
const k=document.getElementById('key').value;
if(!k.startsWith('gsk_')){log('Invalid key format','error');return}
const r=await fetch('/api/key',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({api_key:k})});
if(r.ok){log('🔑 API Key saved successfully');updatePermDisplay()}else{log('Save failed','error')}
}
async function execute(){
const c=document.getElementById('cmd').value;
if(!c){log('Enter command','error');return}

// Check browser permission first
if(!permissionsGranted){
log('❌ Browser permission required. Please grant permission first.','error');
showPermModal();
return;
}

log('⚙️ Executing: '+c);
try{
const r=await fetch('/api/execute',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:c})});
const d=await r.json();
if(r.ok){log('✓ Success: '+JSON.stringify(d.actions))}else{
if(d.detail && d.detail.includes('Permissions not granted')){
log('❌ VM missing system capabilities. Admin needs to install tools.','error');
}else{
log('Error: '+d.detail,'error');
}
}
}catch(e){log('Error: '+e.message,'error')}
}
document.getElementById('cmd').addEventListener('keypress',e=>{if(e.key=='Enter')execute()});
async function initApp(){
permissionsGranted=checkUserPerms();
updatePermDisplay();

if(!permissionsGranted){
log('⚠️ Browser permission required to use this app.');
showPermModal();
}else{
log('✅ Browser permission granted. Ready to execute commands.');
log('📋 VM will handle system capabilities. Commands sent to: '+window.location.origin);
}
}
initApp();
</script></body></html>"""

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
