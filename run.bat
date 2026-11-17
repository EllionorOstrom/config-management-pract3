@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if /i "%~1"=="asm" goto asm
echo Usage: run.bat asm ^<source^> ^<output^> [--test]
exit /b 1
:asm
python -m src.assembler %2 %3 %4
exit /b %errorlevel%
