@echo off
set "SHELL_EMULATOR_NO_PAUSE=1"
cd /d "%~dp0.."
call run.bat --vfs vfs\nested.csv --prompt "student$ " --script scripts\success.txt
set "RESULT=%errorlevel%"
set "SHELL_EMULATOR_NO_PAUSE="
echo.
echo ==========================================
if not "%RESULT%"=="0" echo Script ended with error code %RESULT%.
if "%RESULT%"=="0" echo Script finished successfully.
echo Press any key to close this window...
pause >nul
exit /b %RESULT%
