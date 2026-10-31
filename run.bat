@echo off
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 main.py %*
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo ERROR: Python not found. Install Python 3 and enable PATH.
        set "RESULT=1"
        goto finish
    )
    python main.py %*
)
set "RESULT=%errorlevel%"
:finish
if not defined SHELL_EMULATOR_NO_PAUSE (
    echo.
    echo Press any key to close this window...
    pause >nul
)
exit /b %RESULT%
