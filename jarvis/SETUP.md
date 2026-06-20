# Run JARVIS on your own machine (local Claude Code)

## Why this matters
"Claude Code on the web" (claude.ai/code) and the mobile app run in a **throwaway
cloud container** — it can't see your files, mic, or accounts. To have Claude
actually control **your** PC, run Claude Code **locally**. A session is local only
when you start it locally.

## A. Install local Claude Code (Windows, one time)
1. Install (PowerShell):
   ```powershell
   irm https://claude.ai/install.ps1 | iex
   ```
   (or `winget install Anthropic.ClaudeCode`, or `npm install -g @anthropic-ai/claude-code`)
2. Recommended: install Git for Windows (gives Claude the Bash tool):
   https://git-scm.com/downloads/win
3. Verify: `claude --version`  then  `claude doctor`
4. Start it **in your project** and log in when the browser opens:
   ```powershell
   cd path\to\Keshanar\jarvis
   claude
   ```
   Log in with your Claude Pro/Max account (or set `ANTHROPIC_API_KEY`).

**Rule to avoid the cloud in future:** start from your terminal (`claude`) or the
Desktop app → Code tab → **Local**. Don't start from claude.ai/code (that's remote).

## B. Set up JARVIS
From the `jarvis\` folder:
```powershell
.\setup.ps1                      # creates venv, installs core, makes .env
#   then edit .env:  ANTHROPIC_API_KEY=...,  JARVIS_MODEL_FAST=claude-sonnet-4-6,
#                    JARVIS_MODEL_HEAVY=claude-opus-4-8
py -m jarvis.doctor --ping       # should be all OK + a live model ping
py -m jarvis.chat                # prove it: type -> Claude -> reply
```
Add the rest when ready:
```powershell
.\.venv\Scripts\Activate.ps1
pip install -e ".[voice,capture,hud]"    # mic, screen capture, orb bridge
py -m jarvis.main                        # full voice + orb
```

## Or just let local Claude Code do it
Open local Claude Code in this folder and say:
> "Run setup.ps1, then `py -m jarvis.doctor --ping`, and fix anything that fails."
