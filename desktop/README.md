# Smart Grid AI — Desktop App

## How to run in development

```bash
# 1. Make sure the Python backend is running
cd ..
python api/main.py

# 2. In another terminal, start the substations
python substations/substation_client.py --id S1 --simulate
python substations/substation_client.py --id S2 --simulate --faulty
python substations/substation_client.py --id S3 --simulate

# 3. Start the Electron app
cd desktop
npm install
npm start
```

## How to build the installer (.exe)

```bash
cd desktop
npm install
npm run build
```

The installer will be at `desktop/dist/Smart Grid AI Setup 1.0.0.exe`

## Requirements for end users

- Windows 10/11 x64
- Python 3.10+ installed (with pip)
- Run once: `pip install -r requirements.txt`

## What the installer includes

- Electron shell (the app window)
- All Python source code
- Pre-built React dashboard
- All ML models (trained on first launch)

## Architecture

```
Electron (app window)
    │
    ├── Spawns: python api/main.py          (FastAPI + socket server)
    ├── Spawns: python substations/...      (3 substation clients)
    └── Loads:  dashboard/frontend/dist/    (React app as file://)
                    │
                    └── API calls → http://localhost:8000
```
