---
description: Run AKIRA STUDIO in Demo Mode (no API required)
---

# Demo Mode Workflow

Use this when API billing is disabled or for offline UI/UX testing.

## Start Demo Server

// turbo

1. Stop any running Python servers:

```
taskkill /F /IM python.exe 2>nul
```

// turbo
2. Start backend in Demo Mode:

```
set DEMO_MODE=true && python apps/server/main.py
```

// turbo
3. Start frontend (in separate terminal):

```
cmd /c "cd apps/web && npm run dev"
```

1. Open browser to <http://localhost:3000>

## Demo Features

- All API calls are bypassed
- Mock responses for: DECO*27, PinocchioP, HoneyWorks, MARETU
- Simulated streaming delay
- Full card UI testing (Style Prompt, Lyrics, Commentary)

## Exit Demo Mode

Restart server without DEMO_MODE environment variable.
