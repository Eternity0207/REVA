# REVA Quick Start Guide

## What is REVA?

REVA is a desktop application that lets you remotely control your computer. Download it, run it, and start executing commands.

---

## 1️⃣ Download & Run

**Visit home page:** `index.html` in your browser

Your operating system will be detected automatically:
- **Windows 11**: Download `REVA.exe`
- **macOS**: Download `REVA.app`
- **Linux**: Download `REVA`

Simply run the downloaded file. That's it!

---

## 2️⃣ Connect to Backend

When REVA launches:

1. Click **Settings** tab (bottom)
2. Enter connection details:
   ```
   Agent ID:    my-agent
   Token:       my-secret-token
   Server URL:  http://localhost:8002
   ```
3. Click **Connect** button
4. Wait for green "✅ Connected" indicator

---

## 3️⃣ Send Your First Command

1. Click **Dashboard** tab - see status
2. Click **Command Center** tab - see command buttons
3. Click any command button:
   - Press Ctrl+T
   - Click at coordinates
   - Type text
   - Take screenshot
   - Get system info
4. Watch it execute in real-time!

---

## 4️⃣ Check Results

Click **History** tab to see:
- All past commands
- Execution time
- Success/failure status
- Command results

---

## Starting the Backend

For local testing:

```bash
cd /path/to/REVA
python3 main_server.py
```

Backend runs on: `http://localhost:8002`

---

## Available Commands

| Command | What it does | Example |
|---------|-------------|---------|
| **Press Keys** | Keyboard control | Ctrl+T, Alt+Tab |
| **Click Mouse** | Click at position | X: 100, Y: 200 |
| **Type Text** | Input text | "hello world" |
| **Screenshot** | Capture screen | View current display |
| **System Info** | Get OS details | CPU, RAM, OS version |
| **Sleep** | Wait N seconds | Delay between commands |
| **Open App** | Launch program | Firefox, Notepad, etc |

---

## Troubleshooting

### App won't connect?
- Check backend is running: `curl http://localhost:8002/api/agents`
- Verify credentials are correct in Settings
- Try restarting both backend and app

### Commands not executing?
- Check green "✅ Connected" indicator
- Try "System Info" command first
- Check terminal for error messages
- Verify system permissions (admin on Windows/macOS)

### App won't start?
- **Windows**: Right-click → "Run as Administrator"
- **macOS**: Allow in System Preferences → Security
- **Linux**: `chmod +x REVA && ./REVA`

---

## Production Deployment

1. Deploy backend on server:
   ```bash
   python3 main_server.py --host 0.0.0.0 --port 8002
   ```

2. Host `index.html` on web server

3. Update REVA Settings:
   ```
   Server URL: https://your-server.com:8002
   ```

4. Users download and run app

5. Done! App connects to your backend

---

## Configuration

### In REVA App (Settings Tab):
- **Agent ID**: Unique name for this computer
- **Token**: Secret key (keep safe!)
- **Server URL**: Backend address
- **Poll Interval**: Check frequency (default 3s)

### Save Button: Saves credentials locally

---

## Security Tips

1. **Change default credentials** in production
2. **Use HTTPS** for public deployments
3. **Keep tokens secret** - like passwords
4. **Only allow trusted agents** to connect
5. **Monitor command execution** in logs

---

## Next Steps

### Learn More
- Read `README.md` for complete documentation
- Review source code in `desktop_ui/`, `desktop_agent/`
- Check `handlers/command.py` for command details
- Explore `main_server.py` for backend

### Build from Source
```bash
pip install -r requirements-desktop.txt
python3 desktop_app.py
python3 build_app.py  # Create executable
```

### Extend with Custom Commands
1. Add handler in `handlers/command.py`
2. Add UI button in `desktop_ui/command_center.py`
3. Rebuild with `python3 build_app.py`

---

## Architecture (Simple Overview)

```
You (REVA App)
    ↓
Backend Server
    ↓
Execute Keyboard/Mouse/Screenshot
    ↓
See Results
```

1. Click button in REVA
2. App sends to backend
3. Backend queues task
4. App checks every 3 seconds
5. Task executes
6. Result sent back
7. App shows result

---

## Key Files

| File | Purpose |
|------|---------|
| `index.html` | Home page with download |
| `dist/REVA` | Standalone app |
| `main_server.py` | Backend server |
| `desktop_app.py` | App source |
| `README.md` | Full documentation |

---

## Common Commands

### For Testing
```
Agent ID:  test-agent
Token:     test-token
URL:       http://localhost:8002
```

### For Production
```
Agent ID:  my-unique-id
Token:     strong-secret-key
URL:       https://api.yourserver.com:8002
```

---

## Important: First Time Setup

1. Download app from home page
2. Run the executable
3. Enter `my-agent` and `my-secret-token`
4. Enter `http://localhost:8002`
5. Click Connect
6. See green checkmark = ready!

---

## Need Help?

✅ Check troubleshooting section above
✅ Review `README.md` for detailed docs
✅ Check terminal output for error messages
✅ Verify backend is running
✅ Try System Info command to test

---

**Ready to go!** 🚀

Download REVA → Run → Connect → Execute

That's all you need to know to get started.
