#!/usr/bin/env python3
"""
REVA Unified Launcher - Single Port Architecture
Backend (FastAPI) serves frontend, app download, and all APIs on port 8002
"""
import os
import sys
import time
import socket
from pathlib import Path

os.chdir(Path(__file__).parent)

def is_port_open(port):
    """Check if port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def main():
    print("\n╔" + "="*78 + "╗")
    print("║" + "🤖 REVA - Remote Execution & Visualization Agent".center(78) + "║")
    print("║" + "Single Port Architecture (Everything on :8002)".center(78) + "║")
    print("╚" + "="*78 + "╝\n")
    
    # ❌ REMOVED: pkill (was killing systemd process)
    # ❌ REMOVED: lsof kill (was killing own server)

    print("⚡ Checking ports...")
    if is_port_open(8002):
        print("   ⚠️  Port 8002 already in use (expected under systemd)")
    
    print("\n✅ Starting REVA System...\n")
    
    # Start backend
    import uvicorn
    from main_server import app
    
    print("╔" + "="*78 + "╗")
    print("║ SERVICE STATUS".ljust(79) + "║")
    print("╚" + "="*78 + "╝")
    print("🟢 Frontend:     http://localhost:8002")
    print("🟢 Backend API:  http://localhost:8002/api")
    print("🟢 Download:     http://localhost:8002/dist/REVA")
    print("🟢 Credentials:  Agent ID: my-agent | Token: my-secret-token")
    print("\n" + "="*80)
    print("Press CTRL+C to stop REVA\n")
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
    except KeyboardInterrupt:
        print("\n" + "="*80)
        print("✅ REVA Stopped")
        print("="*80 + "\n")
        sys.exit(0)

if __name__ == "__main__":
    main()