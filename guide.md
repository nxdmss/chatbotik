# Python: краткий конспект и практикум

Практичный конспект Python с примерами, мини‑упражнениями и мини‑проектами. Держите этот файл под рукой и возвращайтесь к нему в любое время.

## Содержание
- Как пользоваться этим файлом
- Установка и запуск
- Базовый синтаксис и типы
- Ввод и вывод
- Операторы
- Строки
- Коллекции
- Управляющие конструкции
- Функции
- Обработка ошибок
- Работа с файлами
- Модули и импорт
- Классы (ООП)
- Стандартная библиотека
- Установка пакетов (pip)
- Стиль кода
- Мини‑упражнения
- Мини‑проекты
- План на неделю
- Шаблон структуры проекта

---

## Как пользоваться этим файлом
- Читайте по разделам и сразу запускайте примеры в REPL или отдельном файле.
- Выполняйте мини‑упражнения после разделов.
- Раз в неделю делайте мини‑проект для закрепления.

Совет: создайте папку practice/ и сохраняйте туда все решения.

---

## Установка и запуск
- Проверить версию: `python --version` (или `python3 --version`)
- REPL: запустите `python` и вводите команды.
- Скрипт: сохраните `main.py`, запустите `python main.py`

Виртуальное окружение (рекомендуется):
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install --upgrade pip
```

---

## Базовый синтаксис и типы
- Отступы важны (обычно 4 пробела).
- Комментарии: `# ...`
- Переменные создаются присваиванием.

```python
x = 10           # int
pi = 3.14        # float
ok = True        # bool
name = "Alex"    # str
nothing = None   # NoneType

print(type(x), type(name))
```

Полезно:
```python
dir(obj)   # список атрибутов/методов
help(obj)  # справка по объекту
len(s)     # длина (строки/коллекции)
```

---

## Ввод и вывод
```python
name = input("Введите имя: ")
age = int(input("Сколько вам лет? "))
print(f"Меня зовут {name}, мне {age}")
```

---

## Операторы
- Арифметика: `+ - * / // % **`
- Сравнения: `== != > >= < <=`
- Логика: `and or not`
- Принадлежность/тождество: `in`, `is`
- Сокращённые присваивания: `x += 1`, `y *= 2`

---

## Строки
```python
s = "  Hello, Python  "
print(s.strip().lower())      # "hello, python"
print(s[0], s[-1])            # индексы
print(s[1:5], s[::-1])        # срезы
print("a,b,c".split(','))     # ['a','b','c']
print(" ".join(["Hello","you"]))
print(r"C:\path\file.txt")    # сырьевая строка
```

Частые методы: `lower()`, `upper()`, `strip()`, `split()`, `replace(a,b)`, `startswith()`, `endswith()`.

---

## Коллекции
Список (list, изменяемый):
```python
nums = [1, 2, 3]
nums.append(4)
nums[0] = 10
```

Кортеж (tuple, неизменяемый):
```python
pt = (10, 20)
```

Словарь (dict: ключ -> значение):
```python
user = {"name": "Alex", "age": 21}
print(user.get("email", "нет"))
user["age"] = 22
```

Множество (set, только уникальные):
```python
st = {1, 2, 2, 3}  # {1,2,3}
```

Генераторы:
```python
squares = [x*x for x in range(5)]
even = {x for x in range(10) if x % 2 == 0}
index_by_name = {u["name"]: u for u in [{"name":"A"},{"name":"B"}]}
```

---

## Управляющие конструкции
```python
x = 7
if x > 10:
    print("больше 10")
elif x == 10:
    print("равно 10")
else:
    print("меньше 10")

for i in range(3):  # 0,1,2
    print(i)

i = 0
while i < 3:
    print(i)
    i += 1

for idx, val in enumerate(["a", "b"]):
    print(idx, val)

for a, b in zip([1,2,3], [10,20,30]):
    print(a, b)
```

Ключевые слова: `break`, `continue`, `pass`.

---

## Функции
```python
def greet(name="мир"):
    return f"Привет, {name}!"

print(greet("Alex"))
```

Аргументы:
```python
def total(*nums: int) -> int:
    return sum(nums)

def describe(**fields):
    return ", ".join(f"{k}={v}" for k, v in fields.items())

print(total(1,2,3), describe(name="Alex", age=21))
```

Аннотации типов не обязательны, но помогают: `x: int`, `-> str`.

---

## Обработка ошибок
```python
try:
    x = int(input("Число: "))
    print(10 / x)
except ZeroDivisionError:
    print("Деление на ноль!")
except ValueError:
    print("Введите целое число")
else:
    print("Ошибок не было")
finally:
    print("Готово")
```

Выброс исключения:
```python
def sqrt_nonneg(x: float) -> float:
    if x < 0:
        raise ValueError("x должен быть >= 0")
    return x ** 0.5
```

---

## Работа с файлами
```python
from pathlib import Path

# запись
with open("data.txt", "w", encoding="utf-8") as f:
    f.write("Привет\n")

# чтение целиком
with open("data.txt", "r", encoding="utf-8") as f:
    text = f.read()

# чтение построчно
for line in Path("data.txt").read_text(encoding="utf-8").splitlines():
    print(line)
```

Менеджеры контекста автоматически закрывают файл.

---

## Модули и импорт
```python
import math
from random import randint
import datetime as dt

# свой модуль:
# файл utils.py в той же папке
# import utils  или  from utils import func
```

Запуск как скрипт:
```python
def main():
    print("Hello")

if __name__ == "__main__":
    main()
```

---

## Классы (ООП)
```python
class Person:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
    def say(self) -> str:
        return f"Я {self.name}, мне {self.age}"

p = Person("Alex", 21)
print(p.say())
```

Наследование:
```python
class Student(Person):
    def __init__(self, name, age, group):
        super().__init__(name, age)
        self.group = group
```

---

## Стандартная библиотека (полезные модули)
- pathlib — пути и файлы
- json — сериализация данных
- datetime — даты и время
- collections — Counter, defaultdict, deque
- itertools — комбинаторика и итераторы
- statistics — простая статистика

Примеры:
```python
from pathlib import Path
import json
from collections import Counter

Path("files").mkdir(exist_ok=True)
p = Path("files") / "data.json"
data = {"a": 1, "b": [1,2,3]}
p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

words = "a b a c b a".split()
print(Counter(words).most_common(2))  # [('a',3), ('b',2)]
```

---

## Установка пакетов (pip)
```bash
pip install requests
```
```python
import requests
r = requests.get("https://httpbin.org/get", timeout=10)
print(r.status_code, r.json()["url"])
```

---

## Стиль кода
- Следуйте PEP 8 (наименование, отступы, длина строки).
- Инструменты: 
  - Форматирование: `black`
  - Линтинг: `ruff` (или `flake8`)
- Именование: функции/переменные — snake_case, классы — PascalCase, константы — UPPER_CASE.

---

## Мини‑упражнения
1) Приветствие: спросите имя через input и выведите "Привет, <имя>!"  
2) Калькулятор: считайте два числа и операцию (+, -, *, /), выведите результат, обработайте деление на ноль.  
3) Сумма массива: прочитайте строку чисел "1 2 3", превратите в список int и посчитайте сумму/среднее.  
4) Поиск в тексте: посчитайте, сколько раз слово встречается в строке (без учета регистра).  
5) Работа с файлами: прочитайте файл, посчитайте количество строк и слов, запишите отчет в новый файл.  
6) Словарь частот: по входной строке постройте dict частоты слов, выведите топ‑3.  
7) FizzBuzz: для чисел 1..100 печатайте Fizz/Buzz/FizzBuzz или число.  
8) Генераторы: сделайте список квадратов четных чисел 1..50; словарь {число: квадрат}.  
9) Функции: напишите функцию `validate_email(s) -> bool` с простыми проверками.  
10) Классы: класс `BankAccount` с методами `deposit`, `withdraw` (с проверкой), `balance`.

Подсказка для 3):
```python
nums = list(map(int, input().split()))
print(sum(nums), sum(nums)/len(nums) if nums else 0)
```

---

## Мини‑проекты (на выбор)
- Угадай число: компьютер загадывает число 1..100; подсказывает больше/меньше, считает попытки.
- Менеджер заметок: сохранить/читать/искать заметки в файле JSON.
- Парсер логов: прочитать лог, посчитать статистику по уровням (INFO/WARN/ERROR), выгрузить отчет.

Идея для «Угадай число»:
```python
import random

secret = random.randint(1, 100)
tries = 0
while True:
    n = int(input("Ваш вариант: "))
    tries += 1
    if n < secret:
        print("Больше")
    elif n > secret:
        print("Меньше")
    else:
        print(f"Угадали за {tries} попыток!")
        break
```

---

## План на неделю (пример)
- День 1: базовый синтаксис, переменные, ввод/вывод
- День 2: условия и циклы, enumerate/zip
- День 3: коллекции и генераторы
- День 4: функции, обработка ошибок
- День 5: файлы, модули, стандартная библиотека
- День 6: классы и простые проекты
- День 7: мини‑проект + разбор ошибок

---

## Шаблон структуры проекта
```
python-basics/
  ├─ README.md
  ├─ .venv/               # виртуальное окружение (в .gitignore)
  ├─ requirements.txt
  ├─ src/
  │   ├─ main.py
  │   └─ utils.py
  └─ practice/
      ├─ exercises/
      └─ projects/
```

Пример `src/main.py`:
```python
from utils import greet

def main():
    print(greet("мир"))

if __name__ == "__main__":
    main()
```

Пример `src/utils.py`:
```python
def greet(name: str) -> str:
    return f"Привет, {name}!"
```

Файл `requirements.txt` добавляйте по мере установки библиотек (например, `requests`).

---

Удачи в изучении! Если нужно — добавлю автопроверку упражнений, тесты или создам дополнительные файлы.