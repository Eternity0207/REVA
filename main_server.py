"""REVA Web Server"""
import os
import platform
import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="REVA", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class APIKeyRequest(BaseModel):
    api_key: str

def check_permissions():
    perms = {"screenshot": False, "keyboard": False, "mouse": False}

    # Screenshot
    if platform.system() == "Linux":
        for tool in ["grim", "scrot"]:
            if subprocess.run(["which", tool], capture_output=True).returncode == 0:
                perms["screenshot"] = True
                break
    else:
        perms["screenshot"] = True

    # Input
    try:
        import pyautogui
        pyautogui.size()
        perms["keyboard"] = perms["mouse"] = True
    except:
        pass

    return perms

@app.get("/")
async def root():
    return {"status": "REVA Web Server v1.0"}

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/permissions")
async def permissions():
    return {
        "permissions": check_permissions(),
        "api_key_set": bool(os.getenv("OPENAI_API_KEY"))
    }

@app.post("/api/key")
async def save_key(request: APIKeyRequest):
    key = request.api_key.strip()
    with open(".env", "w") as f:
        f.write(f"OPENAI_API_KEY='{key}'\n")
        f.write("OPENAI_API_BASE_URL='https://api.groq.com/openai/v1'\n")
    load_dotenv(override=True)
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    print("REVA Web Server: http://localhost:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)
