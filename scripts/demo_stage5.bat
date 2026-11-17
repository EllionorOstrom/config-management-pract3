@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0.."
if not exist build mkdir build
call :demo vector_sub_23 "TEST TASK: vector 40 25 23 100 7 minus 23. Expected result 105..109: 17 2 0 77 -16"
call :demo example_1 "EXAMPLE 1: vector 100 90 80 70 60 minus 23. Expected: 77 67 57 47 37"
call :demo example_2 "EXAMPLE 2: vector 8 16 32 64 128 minus 5. Expected: 3 11 27 59 123"
call :demo example_3 "EXAMPLE 3: vector 1 2 3 4 5 minus 23. Expected: -22 -21 -20 -19 -18"
exit /b 0
:demo
echo.
echo ===== %~2 =====
python -m src.assembler programs\%~1.asm build\%~1.bin
python -m src.interpreter build\%~1.bin build\%~1.json --range 100 110
type build\%~1.json
exit /b 0
