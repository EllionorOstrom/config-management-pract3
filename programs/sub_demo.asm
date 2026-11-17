; Этап 4: проверка команды вычитания SUB.
; Порядок на стеке: адрес результата, второй операнд, первый операнд
; (вершина). SUB записывает по адресу (первый - второй).

; 10 - 3 -> ячейка 50 (ожидается 7)
LOAD_CONST 50
LOAD_CONST 3
LOAD_CONST 10
SUB

; 5 - 5 -> ячейка 51 (ожидается 0)
LOAD_CONST 51
LOAD_CONST 5
LOAD_CONST 5
SUB

; 3 - 10 -> ячейка 52 (ожидается -7)
LOAD_CONST 52
LOAD_CONST 10
LOAD_CONST 3
SUB

; 1000 - 1 -> ячейка 53 (ожидается 999)
LOAD_CONST 53
LOAD_CONST 1
LOAD_CONST 1000
SUB

; Операнды из памяти: ячейка 60 = 40, ячейка 61 = 15.
; Результат 40 - 15 записывается в ячейку 62 (ожидается 25).
LOAD_CONST 40
WRITE 60
LOAD_CONST 15
WRITE 61
LOAD_CONST 62
LOAD_CONST 0
READ 61
LOAD_CONST 0
READ 60
SUB
