@echo off
setlocal enabledelayedexpansion

:: ================================================================
:: Wednesday AI Assistant — Windows Setup Script
:: Run ONCE to set up your development environment.
:: Double-click this file OR run from PowerShell.
:: ================================================================

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║   WEDNESDAY — AI Assistant Setup                 ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: ── Check Python version ────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo.
    echo  Install Python 3.11+ from: https://python.org/downloads/
    echo  IMPORTANT: Check "Add Python to PATH" during install!
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version') do set pyver=%%v
echo [OK] Python %pyver% found.

:: ── Create virtual environment ───────────────────────────────────
echo.
echo [1/6] Creating virtual environment (.venv)...
if exist .venv (
    echo  .venv already exists — skipping creation.
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  .venv created successfully.
)

:: ── Activate venv ───────────────────────────────────────────────
echo.
echo [2/6] Activating virtual environment...
call .venv\Scripts\activate.bat

:: ── Upgrade pip ─────────────────────────────────────────────────
echo.
echo [3/6] Upgrading pip...
python -m pip install --upgrade pip setuptools wheel -q

:: ── Install PyAudio (Windows needs special handling) ────────────
echo.
echo [4/6] Installing PyAudio (Windows-specific)...
pip install PyAudio -q
if errorlevel 1 (
    echo  [WARN] PyAudio failed via pip. Trying pipwin...
    pip install pipwin -q
    pipwin install pyaudio -q
    if errorlevel 1 (
        echo  [WARN] PyAudio installation failed.
        echo  Voice input will be disabled.
        echo  Manual fix: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
        echo  Download the correct .whl for your Python version, then:
        echo  pip install [downloaded-file.whl]
        echo.
    ) else (
        echo  PyAudio installed via pipwin.
    )
) else (
    echo  PyAudio installed successfully.
)

:: ── Install all requirements ─────────────────────────────────────
echo.
echo [5/6] Installing Python dependencies...
echo  This may take 3-10 minutes on first run (downloading AI models).
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [WARN] Some packages may have failed. Check output above.
    echo  Common fix: pip install [package-name] manually.
    echo.
)

:: ── Set up .env file ────────────────────────────────────────────
echo.
echo [6/6] Setting up configuration...
if not exist .env (
    copy .env.example .env >nul
    echo  Created .env from template.
    echo.
    echo  ╔══════════════════════════════════════════════════╗
    echo  ║  ACTION REQUIRED:                                ║
    echo  ║                                                  ║
    echo  ║  1. Open .env in a text editor                   ║
    echo  ║  2. Replace the placeholder API keys:            ║
    echo  ║                                                  ║
    echo  ║  OPENAI_API_KEY=sk-proj-...                      ║
    echo  ║  Get it at: platform.openai.com/api-keys         ║
    echo  ║                                                  ║
    echo  ║  3. Save the file                                ║
    echo  ║  4. Run: python main.py                          ║
    echo  ╚══════════════════════════════════════════════════╝
) else (
    echo  .env already exists — skipping.
)

:: ── Print summary ────────────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║  Setup Complete!                                 ║
echo  ║                                                  ║
echo  ║  To run Wednesday:                               ║
echo  ║    .venv\Scripts\activate                        ║
echo  ║    python main.py                                ║
echo  ║                                                  ║
echo  ║  Text-only mode (no mic needed):                 ║
echo  ║    python main.py --text                         ║
echo  ║                                                  ║
echo  ║  Debug mode:                                     ║
echo  ║    python main.py --debug                        ║
echo  ║                                                  ║
echo  ║  List audio devices:                             ║
echo  ║    python main.py --devices                      ║
echo  ╚══════════════════════════════════════════════════╝
echo.
pause
