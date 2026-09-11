@echo off
REM << DigitRollCall: launch recognition UI + attendance system >>
cd /d "%~dp0"

REM Prefer the project's conda env; fall back to whatever python is on PATH.
set PY=%USERPROFILE%\anaconda3\envs\mnist-rdr\python.exe
if not exist "%PY%" set PY=python

"%PY%" "%~dp0start_all.py"
if errorlevel 1 pause
