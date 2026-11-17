@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0.."
if not exist build mkdir build
echo ===== 1. assemble the SUB test program =====
python -m src.assembler programs\sub_demo.asm build\sub_demo.bin
echo ===== 2. run it, dump memory 50..62 =====
echo expected: 50=7, 51=0, 52=-7, 53=999, 60=40, 61=15, 62=25
python -m src.interpreter build\sub_demo.bin build\sub_demo.json --range 50 63
echo exit code: %errorlevel%
type build\sub_demo.json
echo ===== 3. error: SUB with only two items on the stack =====
>build\sub_short.asm echo LOAD_CONST 1
>>build\sub_short.asm echo LOAD_CONST 2
>>build\sub_short.asm echo SUB
python -m src.assembler build\sub_short.asm build\sub_short.bin
python -m src.interpreter build\sub_short.bin build\x.json --range 0 1
echo exit code: %errorlevel%
