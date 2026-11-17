@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0.."
if not exist build mkdir build
echo ===== 1. specification test, test mode: bytes + file size =====
python -m src.assembler programs\spec_tests.asm build\spec.bin --test
echo exit code: %errorlevel%
echo ===== 2. binary file written to disk =====
dir build\spec.bin
echo ===== 3. error: unknown mnemonic =====
>build\bad_mnemonic.asm echo FOO 1
python -m src.assembler build\bad_mnemonic.asm build\bad.bin
echo exit code: %errorlevel%
echo ===== 4. error: operand out of range =====
>build\bad_range.asm echo LOAD_CONST 9999999
python -m src.assembler build\bad_range.asm build\bad.bin
echo exit code: %errorlevel%
echo ===== 5. error: source file does not exist =====
python -m src.assembler programs\missing.asm build\bad.bin
echo exit code: %errorlevel%
