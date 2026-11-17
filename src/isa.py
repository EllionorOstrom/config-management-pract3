"""Спецификация учебной виртуальной машины (УВМ), вариант 17.

Каждая команда занимает 4 байта (порядок байт little-endian).
Младшие 7 бит слова занимает поле A (код операции), далее идёт
поле B (операнд), ширина которого зависит от команды. Модуль также
кодирует команды в байты и декодирует их обратно.
"""

from dataclasses import dataclass
from typing import Dict, Optional

OPCODE_BITS = 7
OPCODE_MASK = (1 << OPCODE_BITS) - 1
INSTRUCTION_SIZE = 4
BYTE_ORDER = "little"
OP_LOAD_CONST = 68
OP_READ = 60
OP_WRITE = 7
OP_SUB = 106
CONST_BITS = 23
OFFSET_BITS = 12
ADDRESS_BITS = 22


class IsaError(Exception):
    """Ошибка описания или кодирования команды."""


@dataclass(frozen=True)
class CommandSpec:
    """Описание одной команды: мнемоника, код и ширина операнда."""

    mnemonic: str
    opcode: int
    operand_bits: int

    @property
    def has_operand(self) -> bool:
        """Есть ли у команды поле B."""
        return bool(self.operand_bits)

    @property
    def max_operand(self) -> int:
        """Наибольшее значение, помещающееся в поле B."""
        return (1 << self.operand_bits) - 1


COMMANDS = (
    CommandSpec("LOAD_CONST", OP_LOAD_CONST, CONST_BITS),
    CommandSpec("READ", OP_READ, OFFSET_BITS),
    CommandSpec("WRITE", OP_WRITE, ADDRESS_BITS),
    CommandSpec("SUB", OP_SUB, 0),
)
BY_MNEMONIC: Dict[str, CommandSpec] = {c.mnemonic: c for c in COMMANDS}
BY_OPCODE: Dict[int, CommandSpec] = {c.opcode: c for c in COMMANDS}


@dataclass(frozen=True)
class Instruction:
    """Команда в промежуточном представлении (поля A и B)."""

    opcode: int
    operand: Optional[int] = None


def validate_operand(spec: CommandSpec, value: int) -> None:
    """Проверить, что значение помещается в поле B команды."""
    if value not in range(spec.max_operand + 1):
        raise IsaError(
            f"{spec.mnemonic}: operand {value} is out of range "
            f"0..{spec.max_operand}"
        )


def encode(instruction: Instruction) -> bytes:
    """Упаковать команду в 4 байта машинного кода."""
    word = instruction.opcode | ((instruction.operand or 0) << OPCODE_BITS)
    return word.to_bytes(INSTRUCTION_SIZE, BYTE_ORDER)


def decode(chunk: bytes) -> Instruction:
    """Распаковать 4 байта машинного кода в команду."""
    if len(chunk) != INSTRUCTION_SIZE:
        raise IsaError(f"truncated instruction: {len(chunk)} bytes")
    word = int.from_bytes(chunk, BYTE_ORDER)
    opcode = word & OPCODE_MASK
    spec = BY_OPCODE.get(opcode)
    if spec is None:
        raise IsaError(f"unknown opcode: {opcode}")
    if word >> (OPCODE_BITS + spec.operand_bits):
        raise IsaError(f"{spec.mnemonic}: reserved bits are not zero")
    if not spec.has_operand:
        return Instruction(opcode)
    return Instruction(opcode, (word >> OPCODE_BITS) & spec.max_operand)
