"""Тесты кодирования команд УВМ в байты и обратно."""

import unittest

from src.isa import Instruction, IsaError, decode, encode

SPEC_CASES = [
    (Instruction(68, 152), [0x44, 0x4C, 0x00, 0x00]),
    (Instruction(60, 316), [0x3C, 0x9E, 0x00, 0x00]),
    (Instruction(7, 715), [0x87, 0x65, 0x01, 0x00]),
    (Instruction(106), [0x6A, 0x00, 0x00, 0x00]),
]


class EncodeTests(unittest.TestCase):
    """Кодирование: промежуточное представление -> байты."""

    def test_spec_examples(self):
        """Все тесты из спецификации дают нужные байты."""
        for instruction, expected in SPEC_CASES:
            with self.subTest(instruction=instruction):
                self.assertEqual(encode(instruction), bytes(expected))

    def test_size_is_four_bytes(self):
        """Любая команда занимает 4 байта."""
        self.assertEqual(len(encode(Instruction(106))), 4)
        self.assertEqual(len(encode(Instruction(68, 8388607))), 4)


class DecodeTests(unittest.TestCase):
    """Декодирование: байты -> промежуточное представление."""

    def test_round_trip(self):
        """decode(encode(x)) возвращает исходную команду."""
        for instruction, _expected in SPEC_CASES:
            with self.subTest(instruction=instruction):
                self.assertEqual(decode(encode(instruction)), instruction)

    def test_unknown_opcode(self):
        """Неизвестный код операции - ошибка."""
        with self.assertRaises(IsaError):
            decode(bytes([0x01, 0x00, 0x00, 0x00]))

    def test_truncated_instruction(self):
        """Неполная команда - ошибка."""
        with self.assertRaises(IsaError):
            decode(bytes([0x6A, 0x00]))

    def test_reserved_bits(self):
        """Ненулевые лишние биты - ошибка."""
        with self.assertRaises(IsaError):
            decode(bytes([0x6A, 0x01, 0x00, 0x00]))


if __name__ == "__main__":
    unittest.main()
