; Этап 3: копирование массива из 5 элементов.
; Исходный массив: ячейки 100-104, приёмник: ячейки 105-109.

; Заполняем исходный массив константами.
LOAD_CONST 11
WRITE 100
LOAD_CONST 22
WRITE 101
LOAD_CONST 33
WRITE 102
LOAD_CONST 44
WRITE 103
LOAD_CONST 55
WRITE 104

; Копируем: кладём на стек базовый адрес 0, READ прибавляет к нему
; смещение и читает ячейку, WRITE записывает значение в приёмник.
LOAD_CONST 0
READ 100
WRITE 105
LOAD_CONST 0
READ 101
WRITE 106
LOAD_CONST 0
READ 102
WRITE 107
LOAD_CONST 0
READ 103
WRITE 108
LOAD_CONST 0
READ 104
WRITE 109
