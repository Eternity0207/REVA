#!/bin/bash

# REVA VM Setup Script
# Run this on the VM to prepare everything

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║            REVA VM Setup - Build & Start                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

REVA_DIR="$HOME/REVA"

# Check if REVA directory exists
if [ ! -d "$REVA_DIR" ]; then
    echo -e "${RED}✗ REVA directory not found at $REVA_DIR${NC}"
    exit 1
fi

cd "$REVA_DIR"
echo -e "${GREEN}✓ Working directory: $REVA_DIR${NC}"
echo ""

# Step 1: Install Python dependencies
echo -e "${YELLOW}Step 1: Installing dependencies...${NC}"
pip install -q pyinstaller PyQt5 requests pyautogui 2>&1 | grep -v "already satisfied"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}✗ Failed to install dependencies${NC}"
    exit 1
fi
echo ""

# Step 2: Build app
echo -e "${YELLOW}Step 2: Building REVA app (5-10 minutes)...${NC}"
python build_app.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Build successful${NC}"
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi
echo ""

# Step 3: Verify dist folder
echo -e "${YELLOW}Step 3: Verifying build output...${NC}"
if [ -f "dist/REVA" ] || [ -f "dist/REVA.exe" ] || [ -f "dist/REVA.app" ]; then
    SIZE=$(du -h dist/REVA* 2>/dev/null | awk '{print $1}' | head -1)
    echo -e "${GREEN}✓ App created: $SIZE${NC}"
else
    echo -e "${RED}✗ App not found in dist/${NC}"
    exit 1
fi
echo ""

# Step 4: Fix permissions
echo -e "${YELLOW}Step 4: Setting permissions...${NC}"
chmod +x dist/REVA* 2>/dev/null
echo -e "${GREEN}✓ Permissions set${NC}"
echo ""

# Step 5: Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo -e "${GREEN}✓ ALL SETUP COMPLETE!${NC}"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Update systemd service:"
echo "     sudo nano /etc/systemd/system/reva.service"
echo ""
echo "  2. Use this for ExecStart:"
echo "     ExecStart=/home/arshgoyal_67/REVA/venv/bin/python run_reva.py"
echo ""
echo "  3. Reload and restart:"
echo "     sudo systemctl daemon-reload"
echo "     sudo systemctl restart reva"
echo ""
echo "  4. Check status:"
echo "     sudo systemctl status reva"
echo ""
echo "  5. Test:"
echo "     curl http://localhost:8002/api/health"
echo ""
