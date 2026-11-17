@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0.."
if not exist build mkdir build
echo ===== 1. assemble the array copy program =====
python -m src.assembler programs\copy_array.asm build\copy_array.bin
echo ===== 2. run it, dump memory 100..109 (source 100-104, copy 105-109) =====
python -m src.interpreter build\copy_array.bin build\copy_array.json --range 100 110
echo exit code: %errorlevel%
type build\copy_array.json
echo ===== 3. error: SUB is not implemented yet =====
>build\sub_early.asm echo LOAD_CONST 1
>>build\sub_early.asm echo LOAD_CONST 2
>>build\sub_early.asm echo LOAD_CONST 3
>>build\sub_early.asm echo SUB
python -m src.assembler build\sub_early.asm build\sub_early.bin
python -m src.interpreter build\sub_early.bin build\x.json --range 0 1
echo exit code: %errorlevel%
echo ===== 4. error: wrong address range =====
python -m src.interpreter build\copy_array.bin build\x.json --range 100 999999
echo exit code: %errorlevel%
echo ===== 5. error: binary file does not exist =====
python -m src.interpreter build\missing.bin build\x.json --range 0 1
echo exit code: %errorlevel%
