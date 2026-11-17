"""Ассемблер УВМ: текст программы -> IR -> машинный код.

Формат строки: ``МНЕМОНИКА [аргумент]``. Всё после ``;`` - комментарий.
"""

import argparse
import os
import sys
from typing import List, Optional

from src.isa import (
    BY_MNEMONIC,
    Instruction,
    IsaError,
    encode,
    validate_operand,
)

COMMENT_MARK = ";"
EXIT_OK = 0
EXIT_ERROR = 1


class AsmError(Exception):
    """Ошибка в тексте программы на языке ассемблера."""


def parse_number(token: str) -> int:
    """Разобрать число: десятичное или шестнадцатеричное (0x...)."""
    try:
        return int(token, 0)
    except ValueError as error:
        raise AsmError(f"bad number: {token}") from error


def parse_line(line: str) -> Optional[Instruction]:
    """Разобрать одну строку; для пустой строки вернуть None."""
    text = line.split(COMMENT_MARK, 1)[0].replace(",", " ")
    tokens = text.split()
    if not tokens:
        return None
    spec = BY_MNEMONIC.get(tokens[0].upper())
    if spec is None:
        raise AsmError(f"unknown mnemonic: {tokens[0]}")
    args = tokens[1:]
    if len(args) != int(spec.has_operand):
        raise AsmError(f"{spec.mnemonic}: wrong number of arguments")
    if not spec.has_operand:
        return Instruction(spec.opcode)
    value = parse_number(args[0])
    validate_operand(spec, value)
    return Instruction(spec.opcode, value)


def assemble(text: str) -> List[Instruction]:
    """Преобразовать текст программы в список команд (IR)."""
    program = []
    for number, line in enumerate(text.splitlines(), start=1):
        try:
            instruction = parse_line(line)
        except (AsmError, IsaError) as error:
            raise AsmError(f"line {number}: {error}") from error
        if instruction is not None:
            program.append(instruction)
    return program


def to_machine_code(program: List[Instruction]) -> bytes:
    """Преобразовать команды промежуточного представления в байты."""
    return b"".join(encode(instruction) for instruction in program)


def format_bytes(instruction: Instruction) -> str:
    """Записать байты команды, например ``0x44, 0x4C, 0x00, 0x00``."""
    return ", ".join(f"0x{byte:02X}" for byte in encode(instruction))


def read_source(path: str) -> str:
    """Прочитать исходный файл программы."""
    with open(path, encoding="utf-8-sig") as source:
        return source.read()


def write_binary(path: str, data: bytes) -> None:
    """Записать двоичный файл, создав недостающие папки."""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "wb") as output:
        output.write(data)


def build_parser() -> argparse.ArgumentParser:
    """Создать разбор аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="assembler", description="Ассемблер учебной виртуальной машины"
    )
    parser.add_argument("source", help="путь к файлу с текстом программы")
    parser.add_argument("output", help="путь к двоичному файлу-результату")
    parser.add_argument(
        "--test", action="store_true", help="режим тестирования"
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Точка входа ассемблера; вернуть код возврата."""
    args = build_parser().parse_args(argv)
    try:
        program = assemble(read_source(args.source))
        code = to_machine_code(program)
        write_binary(args.output, code)
    except (AsmError, OSError) as error:
        print(f"assembler error: {error}", file=sys.stderr)
        return EXIT_ERROR
    print(f"Output size: {len(code)} bytes")
    if args.test:
        for instruction in program:
            print(format_bytes(instruction))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
