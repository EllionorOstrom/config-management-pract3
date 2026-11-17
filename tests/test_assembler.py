"""Тесты ассемблера: примеры из спецификации УВМ и обработка ошибок."""

import contextlib
import io
import os
import tempfile
import unittest

from src.assembler import AsmError, assemble, format_fields, main
from src.isa import Instruction


def fields(source: str) -> list:
    """Ассемблировать текст и вернуть поля команд строками."""
    return [format_fields(item) for item in assemble(source)]


class SpecTests(unittest.TestCase):
    """Тесты из спецификации: поля и значения должны совпасть."""

    def test_load_const(self):
        """Загрузка константы: A=68, B=152."""
        self.assertEqual(fields("LOAD_CONST 152"), ["A=68, B=152"])

    def test_read(self):
        """Чтение из памяти: A=60, B=316."""
        self.assertEqual(fields("READ 316"), ["A=60, B=316"])

    def test_write(self):
        """Запись в память: A=7, B=715."""
        self.assertEqual(fields("WRITE 715"), ["A=7, B=715"])

    def test_sub(self):
        """Вычитание: A=106, поля B нет."""
        self.assertEqual(fields("SUB"), ["A=106"])

    def test_intermediate_representation(self):
        """Промежуточное представление - список объектов Instruction."""
        self.assertEqual(
            assemble("LOAD_CONST 152\nSUB"),
            [Instruction(68, 152), Instruction(106)],
        )


class SyntaxTests(unittest.TestCase):
    """Тесты языка ассемблера."""

    def test_comments_and_blank_lines(self):
        """Комментарии и пустые строки пропускаются."""
        self.assertEqual(fields("; text\n\nSUB ; end\n"), ["A=106"])

    def test_hex_and_lowercase(self):
        """Шестнадцатеричные числа и строчные мнемоники."""
        self.assertEqual(fields("load_const 0x10"), ["A=68, B=16"])

    def test_boundary_values(self):
        """Наибольшие значения операндов принимаются."""
        self.assertEqual(
            fields("LOAD_CONST 8388607\nREAD 4095\nWRITE 4194303"),
            ["A=68, B=8388607", "A=60, B=4095", "A=7, B=4194303"],
        )


class ErrorTests(unittest.TestCase):
    """Обработка ошибок в тексте программы."""

    def test_unknown_mnemonic(self):
        """Неизвестная мнемоника."""
        with self.assertRaises(AsmError):
            assemble("JUMP 5")

    def test_missing_operand(self):
        """У команды с операндом нет аргумента."""
        with self.assertRaises(AsmError):
            assemble("READ")

    def test_extra_operand(self):
        """У команды без операнда есть лишний аргумент."""
        with self.assertRaises(AsmError):
            assemble("SUB 1")

    def test_bad_number(self):
        """Аргумент не является числом."""
        with self.assertRaises(AsmError):
            assemble("WRITE abc")

    def test_operand_too_large(self):
        """Операнд не помещается в своё поле."""
        for text in ("LOAD_CONST 8388608", "READ 4096", "WRITE -1"):
            with self.subTest(text=text):
                with self.assertRaises(AsmError):
                    assemble(text)

    def test_line_number_in_message(self):
        """В сообщении об ошибке указан номер строки."""
        with self.assertRaises(AsmError) as context:
            assemble("SUB\nBAD")
        self.assertIn("line 2", str(context.exception))


class CliTests(unittest.TestCase):
    """Тесты командной строки."""

    def run_main(self, text: str, *extra: str):
        """Запустить main на временном файле, вернуть код и вывод."""
        with tempfile.TemporaryDirectory() as folder:
            source = os.path.join(folder, "p.asm")
            with open(source, "w", encoding="utf-8") as handle:
                handle.write(text)
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = main([source, os.path.join(folder, "p.bin"), *extra])
        return code, buffer.getvalue()

    def test_test_mode_prints_fields(self):
        """В режиме тестирования выводятся поля и значения."""
        code, output = self.run_main("LOAD_CONST 152\nSUB", "--test")
        self.assertEqual(code, 0)
        self.assertIn("A=68, B=152", output)
        self.assertIn("A=106", output)

    def test_missing_source(self):
        """Отсутствующий файл даёт код возврата 1."""
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = main(["no_such_file.asm", "out.bin"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
