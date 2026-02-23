# REVA - AI OS Controlling Agent

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/AI-Groq-orange.svg" alt="Groq">
</p>

**REVA** is an AI-powered desktop automation system using vision-language models.

## Features

- Natural language computer control
- Vision understanding with Llama 4 Scout
- Cross-platform (Linux, macOS, Windows)
- Web UI + Desktop GUI
- Groq LPU powered

## Quick Start

```bash
git clone https://github.com/Eternity0207/REVA.git
cd REVA
pip install -r requirements.txt

# Configure
echo "OPENAI_API_KEY='gsk_your_key'" > .env
echo "OPENAI_API_BASE_URL='https://api.groq.com/openai/v1'" >> .env

# Run Web UI
python main_server.py  # http://localhost:8002

# Or Desktop GUI
python main_ui.py
```

## Architecture

```
REVA/
├── main_server.py      # Web interface
├── main_ui.py          # Desktop GUI
├── operate/            # Core engine
│   ├── models/apis.py  # LLM integration
│   └── utils/          # Screenshot, OS control
├── ui/                 # PyQt6 components
└── OmniParser/         # UI detection
```

## License

MIT License - See LICENSE file.

---
Built with love by Eternity0207
