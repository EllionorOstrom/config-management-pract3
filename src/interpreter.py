"""Интерпретатор УВМ: выполнение машинного кода и дамп памяти в JSON.

Память команд (байты программы) и память данных (список ячеек)
разделены. Для вычислений используется стек.
"""

import argparse
import json
import os
import sys
from typing import Callable, Dict, List, Optional

from src.isa import (
    INSTRUCTION_SIZE,
    OP_LOAD_CONST,
    OP_READ,
    OP_SUB,
    OP_WRITE,
    Instruction,
    IsaError,
    decode,
)

DATA_MEMORY_SIZE = 1 << 16
EXIT_OK = 0
EXIT_ERROR = 1


class VmError(Exception):
    """Ошибка выполнения программы на УВМ."""


class Machine:
    """Модель УВМ: память команд, память данных и стек."""

    def __init__(self, code: bytes, data_size: int = DATA_MEMORY_SIZE):
        """Создать машину с программой ``code`` и пустой памятью данных."""
        if len(code) % INSTRUCTION_SIZE:
            raise VmError(
                f"program size is not a multiple of {INSTRUCTION_SIZE}"
            )
        self.code = code
        self.data = [0] * data_size
        self.stack: List[int] = []
        self.counter = 0
        self.handlers: Dict[int, Callable[[Instruction], None]] = {
            OP_LOAD_CONST: self.load_const,
            OP_READ: self.read,
            OP_WRITE: self.write,
            OP_SUB: self.sub,
        }

    def pop(self) -> int:
        """Снять элемент с вершины стека."""
        if not self.stack:
            raise VmError("stack is empty")
        return self.stack.pop()

    def cell(self, address: int) -> int:
        """Проверить адрес в памяти данных и вернуть его."""
        if address not in range(len(self.data)):
            raise VmError(f"address out of range: {address}")
        return address

    def load_const(self, instruction: Instruction) -> None:
        """LOAD_CONST: положить константу B на стек."""
        self.stack.append(instruction.operand)

    def read(self, instruction: Instruction) -> None:
        """READ: положить на стек значение по адресу (стек + B)."""
        address = self.pop() + instruction.operand
        self.stack.append(self.data[self.cell(address)])

    def write(self, instruction: Instruction) -> None:
        """WRITE: снять значение со стека и записать по адресу B."""
        value = self.pop()
        self.data[self.cell(instruction.operand)] = value

    def sub(self, _instruction: Instruction) -> None:
        """SUB: записать (первый - второй) по адресу, снятому со стека.

        Со стека снимаются: первый операнд (вершина), второй операнд
        и адрес результата.
        """
        first = self.pop()
        second = self.pop()
        address = self.pop()
        self.data[self.cell(address)] = first - second

    def step(self) -> None:
        """Выполнить одну команду: выборка, декодирование, исполнение."""
        end = self.counter + INSTRUCTION_SIZE
        instruction = decode(self.code[self.counter:end])
        self.counter = end
        self.handlers[instruction.opcode](instruction)

    def run(self) -> None:
        """Выполнять команды, пока не закончится память команд."""
        while self.counter < len(self.code):
            self.step()


def parse_int(text: str) -> int:
    """Разобрать целое число (десятичное или 0x...) из аргумента."""
    try:
        return int(text, 0)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"bad number: {text}") from error


def check_range(start: int, end: int, size: int) -> None:
    """Проверить диапазон адресов дампа: [start, end) внутри памяти."""
    if start not in range(size) or end not in range(start, size + 1):
        raise VmError(f"bad address range: {start}..{end}")


def make_dump(machine: Machine, start: int, end: int) -> dict:
    """Собрать дамп ячеек памяти данных с адреса start до end (не вкл.)."""
    check_range(start, end, len(machine.data))
    memory = [
        {"address": address, "value": machine.data[address]}
        for address in range(start, end)
    ]
    return {"range": {"start": start, "end": end}, "memory": memory}


def save_dump(path: str, dump: dict) -> None:
    """Сохранить дамп памяти в JSON-файл, создав недостающие папки."""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as output:
        json.dump(dump, output, indent=2)
        output.write("\n")


def read_binary(path: str) -> bytes:
    """Прочитать двоичный файл с программой."""
    with open(path, "rb") as binary:
        return binary.read()


def build_parser() -> argparse.ArgumentParser:
    """Создать разбор аргументов командной строки."""
    parser = argparse.ArgumentParser(
        prog="interpreter", description="Интерпретатор учебной УВМ"
    )
    parser.add_argument("binary", help="путь к двоичному файлу программы")
    parser.add_argument("dump", help="путь к JSON-файлу с дампом памяти")
    parser.add_argument(
        "--range",
        nargs=2,
        type=parse_int,
        required=True,
        metavar=("START", "END"),
        help="диапазон адресов дампа: от START до END (не включая)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Точка входа интерпретатора; вернуть код возврата."""
    args = build_parser().parse_args(argv)
    start, end = args.range
    try:
        machine = Machine(read_binary(args.binary))
        machine.run()
        save_dump(args.dump, make_dump(machine, start, end))
    except (VmError, IsaError, OSError) as error:
        print(f"vm error: {error}", file=sys.stderr)
        return EXIT_ERROR
    print(f"Memory dump [{start}, {end}) saved to {args.dump}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
