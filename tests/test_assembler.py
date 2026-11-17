"""Тесты ассемблера: разбор языка, ошибки, командная строка."""

import contextlib
import io
import os
import tempfile
import unittest

from src.assembler import AsmError, assemble, main
from src.isa import Instruction

SPEC_PROGRAM = "LOAD_CONST 152\nREAD 316\nWRITE 715\nSUB\n"
SPEC_BYTES = bytes(
    [0x44, 0x4C, 0, 0, 0x3C, 0x9E, 0, 0, 0x87, 0x65, 0x01, 0, 0x6A, 0, 0, 0]
)


class SyntaxTests(unittest.TestCase):
    """Тесты языка ассемблера."""

    def test_intermediate_representation(self):
        """Промежуточное представление - список объектов Instruction."""
        self.assertEqual(
            assemble(SPEC_PROGRAM),
            [
                Instruction(68, 152),
                Instruction(60, 316),
                Instruction(7, 715),
                Instruction(106),
            ],
        )

    def test_comments_and_blank_lines(self):
        """Комментарии и пустые строки пропускаются."""
        self.assertEqual(
            assemble("; text\n\nSUB ; end\n"), [Instruction(106)]
        )

    def test_hex_and_lowercase(self):
        """Шестнадцатеричные числа и строчные мнемоники."""
        self.assertEqual(assemble("load_const 0x10"), [Instruction(68, 16)])

    def test_boundary_values(self):
        """Наибольшие значения операндов принимаются."""
        self.assertEqual(
            assemble("LOAD_CONST 8388607\nREAD 4095\nWRITE 4194303"),
            [
                Instruction(68, 8388607),
                Instruction(60, 4095),
                Instruction(7, 4194303),
            ],
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
        """Запустить main; вернуть код, вывод и содержимое файла."""
        with tempfile.TemporaryDirectory() as folder:
            source = os.path.join(folder, "p.asm")
            target = os.path.join(folder, "sub", "p.bin")
            with open(source, "w", encoding="utf-8") as handle:
                handle.write(text)
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = main([source, target, *extra])
            data = b""
            if os.path.exists(target):
                with open(target, "rb") as handle:
                    data = handle.read()
        return code, buffer.getvalue(), data

    def test_binary_file_matches_spec(self):
        """Двоичный файл совпадает с байтами из спецификации."""
        code, _output, data = self.run_main(SPEC_PROGRAM)
        self.assertEqual(code, 0)
        self.assertEqual(data, SPEC_BYTES)

    def test_size_is_printed(self):
        """Размер файла в байтах выводится на экран."""
        _code, output, _data = self.run_main(SPEC_PROGRAM)
        self.assertIn("Output size: 16 bytes", output)

    def test_test_mode_prints_bytes(self):
        """В режиме тестирования выводятся байты команд."""
        _code, output, _data = self.run_main(SPEC_PROGRAM, "--test")
        self.assertIn("0x44, 0x4C, 0x00, 0x00", output)
        self.assertIn("0x6A, 0x00, 0x00, 0x00", output)

    def test_error_gives_exit_code_1(self):
        """Ошибка в программе даёт код возврата 1, файл не создаётся."""
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code, _output, data = self.run_main("FOO 1")
        self.assertEqual(code, 1)
        self.assertEqual(data, b"")

    def test_missing_source(self):
        """Отсутствующий файл даёт код возврата 1."""
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = main(["no_such_file.asm", "out.bin"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
