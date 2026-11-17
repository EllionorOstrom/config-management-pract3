"""Тесты программ из папки programs: результаты в памяти данных."""

import os
import unittest

from src.assembler import assemble, to_machine_code
from src.interpreter import Machine

PROGRAMS = os.path.join(os.path.dirname(__file__), "..", "programs")
VECTOR = slice(100, 105)
RESULT = slice(105, 110)

CASES = [
    ("vector_sub_23.asm", [40, 25, 23, 100, 7], 23),
    ("example_1.asm", [100, 90, 80, 70, 60], 23),
    ("example_2.asm", [8, 16, 32, 64, 128], 5),
    ("example_3.asm", [1, 2, 3, 4, 5], 23),
]


def run_program(name: str) -> Machine:
    """Ассемблировать и выполнить программу из папки programs."""
    with open(os.path.join(PROGRAMS, name), encoding="utf-8") as handle:
        machine = Machine(to_machine_code(assemble(handle.read())))
    machine.run()
    return machine


class VectorTests(unittest.TestCase):
    """Поэлементное вычитание числа из вектора длины 5."""

    def test_vector_programs(self):
        """Исходный вектор не меняется, результат - в новом векторе."""
        for name, vector, number in CASES:
            with self.subTest(program=name):
                machine = run_program(name)
                self.assertEqual(machine.data[VECTOR], vector)
                expected = [item - number for item in vector]
                self.assertEqual(machine.data[RESULT], expected)

    def test_main_task_values(self):
        """Тестовая задача: вектор 40, 25, 23, 100, 7 минус 23."""
        machine = run_program("vector_sub_23.asm")
        self.assertEqual(machine.data[RESULT], [17, 2, 0, 77, -16])

    def test_stack_is_empty_after_run(self):
        """После выполнения программ на стеке ничего не остаётся."""
        for name, _vector, _number in CASES:
            with self.subTest(program=name):
                self.assertEqual(run_program(name).stack, [])


if __name__ == "__main__":
    unittest.main()
