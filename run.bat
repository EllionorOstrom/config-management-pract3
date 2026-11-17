@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if /i "%~1"=="asm" goto asm
if /i "%~1"=="vm" goto vm
echo Usage:
echo   run.bat asm ^<source^> ^<output^> [--test]
echo   run.bat vm ^<binary^> ^<dump^> --range START END
exit /b 1
:asm
python -m src.assembler %2 %3 %4
exit /b %errorlevel%
:vm
python -m src.interpreter %2 %3 %4 %5 %6
exit /b %errorlevel%
