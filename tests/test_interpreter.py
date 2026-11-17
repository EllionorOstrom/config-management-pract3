"""Тесты интерпретатора УВМ: память, команды, дамп в JSON."""

import contextlib
import io
import json
import os
import tempfile
import unittest

from src.assembler import assemble, to_machine_code
from src.interpreter import (
    Machine,
    VmError,
    check_range,
    main,
    make_dump,
    save_dump,
)
from src.isa import IsaError

PROGRAMS = os.path.join(os.path.dirname(__file__), "..", "programs")


def run_text(text: str) -> Machine:
    """Ассемблировать текст, выполнить и вернуть машину."""
    machine = Machine(to_machine_code(assemble(text)))
    machine.run()
    return machine


class CommandTests(unittest.TestCase):
    """Тесты команд загрузки константы, чтения и записи."""

    def test_load_const_and_write(self):
        """Константа кладётся на стек и записывается в память."""
        machine = run_text("LOAD_CONST 5\nWRITE 10")
        self.assertEqual(machine.data[10], 5)
        self.assertEqual(machine.stack, [])

    def test_read_adds_offset_to_stack_address(self):
        """READ читает по адресу: вершина стека + смещение."""
        machine = run_text(
            "LOAD_CONST 7\nWRITE 20\nLOAD_CONST 15\nREAD 5\nWRITE 30"
        )
        self.assertEqual(machine.data[30], 7)

    def test_code_and_data_memory_are_separate(self):
        """Запись в память данных не меняет память команд."""
        code = to_machine_code(assemble("LOAD_CONST 5\nWRITE 0"))
        machine = Machine(code)
        machine.run()
        self.assertEqual(machine.code, code)

    def test_step_executes_one_instruction(self):
        """step выполняет ровно одну команду."""
        machine = Machine(to_machine_code(assemble("LOAD_CONST 1\nSUB")))
        machine.step()
        self.assertEqual(machine.stack, [1])
        self.assertEqual(machine.counter, 4)

    def test_copy_array_program(self):
        """Тестовая программа копирует массив из ячеек 100-104 в 105-109."""
        path = os.path.join(PROGRAMS, "copy_array.asm")
        with open(path, encoding="utf-8") as handle:
            machine = run_text(handle.read())
        self.assertEqual(machine.data[100:105], [11, 22, 33, 44, 55])
        self.assertEqual(machine.data[105:110], [11, 22, 33, 44, 55])


class ErrorTests(unittest.TestCase):
    """Ошибки выполнения."""

    def test_empty_stack(self):
        """Снятие со стека из пустого стека - ошибка."""
        with self.assertRaises(VmError):
            run_text("WRITE 1")

    def test_address_out_of_range(self):
        """Адрес за пределами памяти данных - ошибка."""
        with self.assertRaises(VmError):
            run_text("LOAD_CONST 8000000\nREAD 0")

    def test_sub_not_implemented_yet(self):
        """На этапе 3 команда SUB ещё не реализована."""
        with self.assertRaises(VmError):
            run_text("LOAD_CONST 1\nLOAD_CONST 2\nLOAD_CONST 3\nSUB")

    def test_truncated_program(self):
        """Размер программы должен быть кратен 4 байтам."""
        with self.assertRaises(VmError):
            Machine(bytes([0x44, 0x4C, 0x00]))

    def test_unknown_opcode(self):
        """Неизвестная команда в двоичном файле - ошибка."""
        machine = Machine(bytes([0x01, 0x00, 0x00, 0x00]))
        with self.assertRaises(IsaError):
            machine.run()


class DumpTests(unittest.TestCase):
    """Дамп памяти в формате JSON."""

    def test_dump_content(self):
        """В дамп попадают ячейки диапазона [start, end)."""
        machine = run_text("LOAD_CONST 9\nWRITE 3")
        dump = make_dump(machine, 2, 5)
        self.assertEqual(dump["range"], {"start": 2, "end": 5})
        self.assertEqual(
            dump["memory"],
            [
                {"address": 2, "value": 0},
                {"address": 3, "value": 9},
                {"address": 4, "value": 0},
            ],
        )

    def test_bad_ranges(self):
        """Неверные диапазоны отклоняются."""
        for start, end in ((5, 2), (-1, 3), (0, 70000), (70000, 70001)):
            with self.subTest(start=start, end=end):
                with self.assertRaises(VmError):
                    check_range(start, end, 65536)

    def test_save_dump_is_valid_json(self):
        """Файл дампа читается как JSON."""
        machine = run_text("LOAD_CONST 9\nWRITE 3")
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "sub", "dump.json")
            save_dump(path, make_dump(machine, 3, 4))
            with open(path, encoding="utf-8") as handle:
                loaded = json.load(handle)
        self.assertEqual(loaded["memory"], [{"address": 3, "value": 9}])


class CliTests(unittest.TestCase):
    """Тесты командной строки интерпретатора."""

    def run_main(self, text: str, *extra: str):
        """Выполнить программу через main; вернуть код и дамп."""
        with tempfile.TemporaryDirectory() as folder:
            binary = os.path.join(folder, "p.bin")
            dump = os.path.join(folder, "dump.json")
            with open(binary, "wb") as handle:
                handle.write(to_machine_code(assemble(text)))
            stdout, stderr = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(stdout):
                with contextlib.redirect_stderr(stderr):
                    code = main([binary, dump, *extra])
            loaded = None
            if os.path.exists(dump):
                with open(dump, encoding="utf-8") as handle:
                    loaded = json.load(handle)
        return code, loaded

    def test_run_and_dump(self):
        """Программа выполняется, дамп сохраняется."""
        code, loaded = self.run_main(
            "LOAD_CONST 4\nWRITE 1", "--range", "0", "3"
        )
        self.assertEqual(code, 0)
        self.assertEqual(loaded["memory"][1], {"address": 1, "value": 4})

    def test_hex_range(self):
        """Диапазон можно задать шестнадцатеричными числами."""
        code, loaded = self.run_main(
            "LOAD_CONST 1\nWRITE 1", "--range", "0x0", "0x2"
        )
        self.assertEqual(code, 0)
        self.assertEqual(len(loaded["memory"]), 2)

    def test_error_gives_exit_code_1(self):
        """Ошибка выполнения даёт код 1 и не создаёт дамп."""
        code, loaded = self.run_main("WRITE 1", "--range", "0", "3")
        self.assertEqual(code, 1)
        self.assertIsNone(loaded)

    def test_missing_binary(self):
        """Отсутствующий двоичный файл даёт код 1."""
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = main(["none.bin", "dump.json", "--range", "0", "1"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
