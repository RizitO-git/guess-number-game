import json
import os
import random
import time
from datetime import datetime

SAVE_FILE = "save.json"
STATS_FILE = "stats.json"

MODE_CLASSIC = "classic"
MODE_UNLIMITED = "unlimited"
MODE_TIME = "time"

SAVE_COMMANDS = {"save", "s", "сохранить"}
YES_ANSWERS = {"да", "yes", "y", "д"}


def mode_name(mode):
    """
    Возвращает понятное название режима игры.
    """
    names = {
        MODE_CLASSIC: "Классический",
        MODE_UNLIMITED: "Без ограничения попыток",
        MODE_TIME: "На время"
    }
    return names.get(mode, mode)


def default_stats():
    """
    Возвращает структуру статистики по умолчанию.
    """
    return {
        "games_played": 0,
        "wins": 0,
        "losses": 0,
        "best_attempts": None,
        "total_attempts_in_wins": 0,
        "total_time_seconds": 0.0,
        "last_games": []
    }


def load_stats():
    """
    Загружает статистику из файла stats.json.
    Если файл отсутствует или повреждён, возвращает статистику по умолчанию.
    """
    stats = default_stats()

    if not os.path.exists(STATS_FILE):
        return stats

    try:
        with open(STATS_FILE, "r", encoding="utf-8") as file:
            loaded_stats = json.load(file)
    except json.JSONDecodeError:
        print("Файл статистики повреждён. Создана новая статистика.")
        return default_stats()
    except OSError:
        print("Не удалось прочитать файл статистики. Создана новая статистика.")
        return default_stats()

    if not isinstance(loaded_stats, dict):
        print("Файл статистики имеет неверный формат. Создана новая статистика.")
        return default_stats()

    stats.update(loaded_stats)

    try:
        stats["games_played"] = max(0, int(stats.get("games_played", 0)))
        stats["wins"] = max(0, int(stats.get("wins", 0)))
        stats["losses"] = max(0, int(stats.get("losses", 0)))
        stats["total_attempts_in_wins"] = max(0, int(stats.get("total_attempts_in_wins", 0)))
        stats["total_time_seconds"] = float(stats.get("total_time_seconds", 0.0))

        if stats.get("best_attempts") is not None:
            best_attempts = int(stats["best_attempts"])
            stats["best_attempts"] = best_attempts if best_attempts > 0 else None

        if not isinstance(stats.get("last_games"), list):
            stats["last_games"] = []

        if stats["total_time_seconds"] < 0:
            stats["total_time_seconds"] = 0.0

    except (TypeError, ValueError):
        print("Файл статистики содержит некорректные данные. Создана новая статистика.")
        return default_stats()

    return stats


def save_json(filename, data):
    """
    Сохраняет словарь data в файл filename в формате JSON.
    """
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        return True
    except OSError:
        print(f"Ошибка: не удалось записать файл {filename}.")
        return False


def save_stats(stats):
    """
    Сохраняет статистику игры в файл stats.json.
    """
    return save_json(STATS_FILE, stats)


def create_new_game_state(
        min_number,
        max_number,
        max_attempts,
        mode,
        difficulty,
        time_limit_seconds=None
):
    """
    Создаёт новое состояние игры.
    """
    if min_number > max_number:
        min_number, max_number = max_number, min_number

    if mode == MODE_CLASSIC and max_attempts <= 0:
        max_attempts = 10

    if mode in {MODE_UNLIMITED, MODE_TIME}:
        max_attempts = 0

    if mode == MODE_TIME and time_limit_seconds is None:
        time_limit_seconds = 60

    return {
        "secret_number": random.randint(min_number, max_number),
        "min_number": min_number,
        "max_number": max_number,
        "max_attempts": max_attempts,
        "attempts_used": 0,
        "history": [],
        "elapsed_seconds": 0.0,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "saved_at": None,
        "mode": mode,
        "difficulty": difficulty,
        "time_limit_seconds": time_limit_seconds
    }


def save_game_state(state):
    """
    Сохраняет текущее состояние игры в файл save.json.
    """
    state["saved_at"] = datetime.now().isoformat(timespec="seconds")
    return save_json(SAVE_FILE, state)


def clear_save():
    """
    Удаляет файл сохранения игры.
    """
    try:
        os.remove(SAVE_FILE)
    except FileNotFoundError:
        pass
    except OSError:
        print("Не удалось удалить файл сохранения.")


def load_game_state():
    """
    Загружает сохранённое состояние игры из файла save.json.
    Если файл отсутствует или повреждён, возвращает None.
    """
    if not os.path.exists(SAVE_FILE):
        return None

    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as file:
            state = json.load(file)
    except json.JSONDecodeError:
        print("Файл сохранения повреждён.")
        return None
    except OSError:
        print("Не удалось прочитать файл сохранения.")
        return None

    if not isinstance(state, dict):
        return None

    required_fields = [
        "secret_number",
        "min_number",
        "max_number",
        "max_attempts",
        "attempts_used",
        "history",
        "elapsed_seconds"
    ]

    for field in required_fields:
        if field not in state:
            return None

    try:
        state["secret_number"] = int(state["secret_number"])
        state["min_number"] = int(state["min_number"])
        state["max_number"] = int(state["max_number"])
        state["max_attempts"] = int(state["max_attempts"])
        state["attempts_used"] = int(state["attempts_used"])
        state["elapsed_seconds"] = float(state["elapsed_seconds"])
        state["history"] = [int(item) for item in state["history"]]
    except (TypeError, ValueError):
        return None

    if state["max_attempts"] < 0:
        state["max_attempts"] = 0

    if state["attempts_used"] < 0 or state["attempts_used"] > state["max_attempts"] and state["max_attempts"] > 0:
        return None

    if state["min_number"] > state["max_number"]:
        return None

    if not (state["min_number"] <= state["secret_number"] <= state["max_number"]):
        return None

    if state["elapsed_seconds"] < 0:
        state["elapsed_seconds"] = 0.0

    state.setdefault("mode", MODE_CLASSIC)
    state.setdefault("difficulty", "Стандартный")
    state.setdefault("time_limit_seconds", None)

    if state["mode"] not in {MODE_CLASSIC, MODE_UNLIMITED, MODE_TIME}:
        state["mode"] = MODE_CLASSIC

    if state["time_limit_seconds"] is not None:
        try:
            state["time_limit_seconds"] = float(state["time_limit_seconds"])
        except (TypeError, ValueError):
            state["time_limit_seconds"] = None
        else:
            if state["time_limit_seconds"] <= 0:
                state["time_limit_seconds"] = None

    if state["mode"] == MODE_TIME and state["time_limit_seconds"] is None:
        state["time_limit_seconds"] = 60.0

    if state["mode"] == MODE_CLASSIC and state["max_attempts"] <= 0:
        state["max_attempts"] = 10

    if state["mode"] in {MODE_UNLIMITED, MODE_TIME}:
        state["max_attempts"] = 0

    return state


def ask_yes_no(question):
    """
    Задаёт вопрос с ответом да/нет.
    """
    answer = input(question).strip().lower()
    return answer in YES_ANSWERS


def ask_integer(prompt, min_value=None, max_value=None):
    """
    Запрашивает у пользователя целое число.
    """
    while True:
        raw_input = input(prompt).strip()

        try:
            value = int(raw_input)
        except ValueError:
            print("Ошибка: нужно ввести целое число.")
            continue

        if min_value is not None and value < min_value:
            print(f"Число должно быть не меньше {min_value}.")
            continue

        if max_value is not None and value > max_value:
            print(f"Число должно быть не больше {max_value}.")
            continue

        return value


def ask_range():
    """
    Запрашивает у пользователя диапазон чисел.
    """
    while True:
        min_number = ask_integer("Введите минимальное число диапазона: ")
        max_number = ask_integer("Введите максимальное число диапазона: ")

        if min_number >= max_number:
            print("Максимальное число должно быть больше минимального.")
        else:
            return min_number, max_number


def ask_custom_settings(mode):
    """
    Запрашивает пользовательские настройки для новой игры.
    """
    print("\nПользовательские настройки")

    min_number, max_number = ask_range()

    max_attempts = 0
    time_limit_seconds = None

    if mode == MODE_CLASSIC:
        max_attempts = ask_integer("Введите количество попыток: ", min_value=1, max_value=1000)
    elif mode == MODE_TIME:
        time_limit_seconds = ask_integer("Введите лимит времени в секундах: ", min_value=1, max_value=3600)

    return (
        mode,
        "Пользовательский",
        min_number,
        max_number,
        max_attempts,
        time_limit_seconds
    )


def choose_mode():
    """
    Позволяет пользователю выбрать режим игры.
    """
    while True:
        print("\nВыберите режим игры:")
        print("1 - Классический (ограниченные попытки)")
        print("2 - Без ограничения попыток")
        print("3 - На время")
        print("4 - Вернуться в меню")

        choice = input("Режим: ").strip().lower()

        if choice == "1":
            return MODE_CLASSIC
        if choice == "2":
            return MODE_UNLIMITED
        if choice == "3":
            return MODE_TIME
        if choice == "4":
            return None

        print("Неверный режим. Введите 1, 2, 3 или 4.")


def choose_game_settings():
    """
    Полный выбор настроек новой игры:
    режим, сложность, диапазон, попытки, время.
    """
    while True:
        mode = choose_mode()

        if mode is None:
            return None

        settings = choose_difficulty(mode)

        if settings is None:
            continue

        return settings


def choose_difficulty(mode):
    """
    Позволяет выбрать уровень сложности или пользовательские настройки.
    """
    while True:
        print("\nВыберите уровень сложности:")

        if mode == MODE_CLASSIC:
            print("1 - Лёгкий: числа 1-50, 15 попыток")
            print("2 - Средний: числа 1-100, 10 попыток")
            print("3 - Сложный: числа 1-1000, 10 попыток")
            print("4 - Экстремальный: числа 1-1000, 5 попыток")
        elif mode == MODE_UNLIMITED:
            print("1 - Лёгкий: числа 1-50")
            print("2 - Средний: числа 1-100")
            print("3 - Сложный: числа 1-1000")
            print("4 - Экстремальный: числа 1-10000")
        elif mode == MODE_TIME:
            print("1 - Лёгкий: числа 1-50, 60 секунд")
            print("2 - Средний: числа 1-100, 75 секунд")
            print("3 - Сложный: числа 1-1000, 120 секунд")
            print("4 - Экстремальный: числа 1-1000, 45 секунд")

        print("5 - Пользовательские настройки")
        print("6 - Вернуться к выбору режима")

        choice = input("Сложность: ").strip().lower()

        if choice == "6":
            return None

        if choice == "5":
            return ask_custom_settings(mode)

        if mode == MODE_CLASSIC:
            presets = {
                "1": (mode, "Лёгкий", 1, 50, 15, None),
                "2": (mode, "Средний", 1, 100, 10, None),
                "3": (mode, "Сложный", 1, 1000, 10, None),
                "4": (mode, "Экстремальный", 1, 1000, 5, None)
            }
        elif mode == MODE_UNLIMITED:
            presets = {
                "1": (mode, "Лёгкий", 1, 50, 0, None),
                "2": (mode, "Средний", 1, 100, 0, None),
                "3": (mode, "Сложный", 1, 1000, 0, None),
                "4": (mode, "Экстремальный", 1, 10000, 0, None)
            }
        else:
            presets = {
                "1": (mode, "Лёгкий", 1, 50, 0, 60),
                "2": (mode, "Средний", 1, 100, 0, 75),
                "3": (mode, "Сложный", 1, 1000, 0, 120),
                "4": (mode, "Экстремальный", 1, 1000, 0, 45)
            }

        if choice in presets:
            return presets[choice]

        print("Неверный выбор. Введите число от 1 до 6.")


def ask_guess_or_command(state, time_left=None):
    """
    Запрашивает у пользователя число или команду сохранения.
    Возвращает:
    - "SAVE", если пользователь хочет сохранить игру;
    - None, если ввод некорректный;
    - int, если введено корректное число.
    """
    if state["max_attempts"] > 0:
        attempt_info = f"Попытка {state['attempts_used'] + 1} из {state['max_attempts']}."
    else:
        attempt_info = f"Попытка {state['attempts_used'] + 1}. Лимит попыток отсутствует."

    time_info = ""

    if time_left is not None:
        time_info = f"[Осталось времени: {time_left:.1f} сек.] "

    prompt = (
        f"{time_info}"
        f"{attempt_info} "
        f"Введите число от {state['min_number']} до {state['max_number']} "
        f"или 'save' для сохранения и выхода: "
    )

    raw_input = input(prompt).strip().lower()

    if raw_input in SAVE_COMMANDS:
        return "SAVE"

    if raw_input == "":
        print("Ввод не может быть пустым.")
        return None

    try:
        guess = int(raw_input)
    except ValueError:
        print("Ошибка: нужно ввести целое число.")
        return None

    if guess < state["min_number"] or guess > state["max_number"]:
        print(f"Число должно быть от {state['min_number']} до {state['max_number']}.")
        return None

    return guess


def get_time_left(state, start_time):
    """
    Возвращает оставшееся время для режима 'На время'.
    Для остальных режимов возвращает None.
    """
    if state.get("mode") == MODE_TIME and state.get("time_limit_seconds") is not None:
        elapsed = time.time() - start_time
        return max(0.0, float(state["time_limit_seconds"]) - elapsed)

    return None


def finish_loss(state, stats, start_time, reason="attempts"):
    """
    Завершает игру поражением и обновляет статистику.
    """
    elapsed_seconds = time.time() - start_time

    if reason == "time":
        print("\nВремя закончилось.")
    else:
        print("\nПопытки закончились.")

    print(f"Загаданное число было: {state['secret_number']}.")
    print(f"Время игры: {elapsed_seconds:.1f} сек.")

    update_stats(stats, False, state["attempts_used"], elapsed_seconds, state)
    save_stats(stats)
    clear_save()

    return False


def update_stats(stats, won, attempts_used, elapsed_seconds, state):
    """
    Обновляет статистику после завершения игры.
    """
    stats["games_played"] = int(stats.get("games_played", 0)) + 1

    if won:
        stats["wins"] = int(stats.get("wins", 0)) + 1
        stats["total_attempts_in_wins"] = int(stats.get("total_attempts_in_wins", 0)) + attempts_used

        best_attempts = stats.get("best_attempts")

        if best_attempts is None or attempts_used < best_attempts:
            stats["best_attempts"] = attempts_used
    else:
        stats["losses"] = int(stats.get("losses", 0)) + 1

    stats["total_time_seconds"] = round(
        float(stats.get("total_time_seconds", 0.0)) + elapsed_seconds,
        2
    )

    if not isinstance(stats.get("last_games"), list):
        stats["last_games"] = []

    record = {
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "result": "win" if won else "loss",
        "attempts_used": attempts_used,
        "time_seconds": round(elapsed_seconds, 2),
        "range": f"{state['min_number']}-{state['max_number']}",
        "mode": state.get("mode", MODE_CLASSIC),
        "difficulty": state.get("difficulty", "")
    }

    stats["last_games"].append(record)

    # Храним только последние 10 игр, чтобы файл не разрастался.
    stats["last_games"] = stats["last_games"][-10:]


def show_stats(stats):
    """
    Показывает статистику игр пользователя.
    """
    print("\n=== Статистика ===")

    games_played = stats.get("games_played", 0)
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    best_attempts = stats.get("best_attempts")
    total_attempts_in_wins = stats.get("total_attempts_in_wins", 0)
    total_time_seconds = stats.get("total_time_seconds", 0.0)
    last_games = stats.get("last_games", [])

    winrate = (wins / games_played * 100) if games_played > 0 else 0.0
    average_attempts = (total_attempts_in_wins / wins) if wins > 0 else None

    print(f"Всего сыграно игр: {games_played}")
    print(f"Побед: {wins}")
    print(f"Поражений: {losses}")
    print(f"Процент побед: {winrate:.1f}%")

    if best_attempts is not None:
        print(f"Лучший результат: {best_attempts} попыток")
    else:
        print("Лучший результат: пока нет побед")

    if average_attempts is not None:
        print(f"Среднее количество попыток при победе: {average_attempts:.1f}")

    print(f"Общее время в играх: {total_time_seconds:.1f} сек.")

    if last_games:
        print("\nПоследние игры:")

        for game in reversed(last_games):
            if not isinstance(game, dict):
                continue

            result_text = "победа" if game.get("result") == "win" else "поражение"
            finished_at = game.get("finished_at", "неизвестно")
            attempts_used = game.get("attempts_used", "?")
            time_seconds = game.get("time_seconds", "?")
            game_range = game.get("range", "?")

            mode_value = game.get("mode")
            difficulty_value = game.get("difficulty")

            extra_info = ""

            if mode_value:
                extra_info += f", режим: {mode_name(mode_value)}"

            if difficulty_value:
                extra_info += f", сложность: {difficulty_value}"

            print(
                f"- {finished_at}: {result_text}, "
                f"попыток: {attempts_used}, "
                f"время: {time_seconds} сек., "
                f"диапазон: {game_range}"
                f"{extra_info}"
            )
    else:
        print("\nИстория игр пока пуста.")


def print_instructions():
    """
    Показывает инструкцию по игре.
    """
    instructions = """
=================================================
                    ИНСТРУКЦИЯ
=================================================

Цель игры:
Угадать число, которое загадала программа.

Главное меню:
1 - Новая игра
2 - Продолжить сохранённую игру
3 - Инструкция
4 - Показать статистику
5 - Выход

Как начать новую игру:
1. Выберите пункт "1 - Новая игра".
2. Выберите режим игры.
3. Выберите уровень сложности или пользовательские настройки.
4. После этого игра начнётся.

Режимы игры:
1. Классический
   Программа загадывает число, а вы пытаетесь его угадать
   за ограниченное количество попыток.

2. Без ограничения попыток
   Программа загадывает число, а вы угадываете его без лимита попыток.
   Игра продолжается до победы или ручного сохранения.

3. На время
   Нужно угадать число за отведённое время.
   Количество попыток не ограничено, но время ограничено.

Уровни сложности:
Для каждого режима есть предустановленные уровни сложности:
- Лёгкий
- Средний
- Сложный
- Экстремальный

Также можно выбрать "Пользовательские настройки".

Пользовательские настройки:
В пользовательских настройках можно изменить:
- диапазон чисел;
- количество попыток для классического режима;
- лимит времени для режима "На время".

Команды во время игры:
- Введите целое число из указанного диапазона, чтобы сделать попытку.
- Введите save, s или сохранить, чтобы сохранить игру и выйти в меню.

Подсказки:
Если число не угадано, программа подскажет:
- "Слишком маленькое число" — загаданное число больше;
- "Слишком большое число" — загаданное число меньше.

Сохранение игры:
- Игра автоматически сохраняется после каждой неправильной попытки.
- Также игру можно сохранить вручную командой save.
- Сохранение находится в файле save.json.
- Чтобы продолжить сохранённую игру, выберите пункт 2 в главном меню.
- Если начать новую игру, старое сохранение будет удалено после подтверждения.

Статистика:
- Статистика сохраняется в файле stats.json.
- Она обновляется только после завершённой игры.
- Если вы сохранили игру и вышли, статистика за эту игру не обновляется,
  потому что игра ещё не завершена.

Совет:
Используйте стратегию деления диапазона пополам.
Например, если диапазон 1-100, первой попыткой можно ввести 50.
Если программа скажет "слишком большое число", дальше ищите число от 1 до 49.
=================================================
"""

    print(instructions)
    input("Нажмите Enter, чтобы вернуться в меню...")


def play_game(state, stats):
    """
    Основной игровой процесс.
    Возвращает:
    - True, если игрок победил;
    - False, если игрок проиграл;
    - None, если игра была сохранена и завершена без результата.
    """
    start_time = time.time() - float(state.get("elapsed_seconds", 0.0))

    print("\nИгра началась!")
    print(f"Я загадал число от {state['min_number']} до {state['max_number']}.")
    print(f"Режим: {mode_name(state.get('mode', MODE_CLASSIC))}")
    print(f"Сложность: {state.get('difficulty', 'Стандартный')}")

    if state.get("mode") == MODE_TIME and state.get("time_limit_seconds") is not None:
        print(f"Лимит времени: {float(state['time_limit_seconds']):.0f} сек.")

    if state["max_attempts"] > 0:
        print(f"У вас есть {state['max_attempts']} попыток.")
    else:
        print("Количество попыток не ограничено.")

    if state["attempts_used"] > 0:
        print(f"Это сохранённая игра. Уже использовано попыток: {state['attempts_used']}.")

        if state["history"]:
            print(f"Ваши прошлые попытки: {', '.join(map(str, state['history']))}")

    # Сохраняем состояние при входе в игру, чтобы можно было возобновить даже до первого хода.
    save_game_state(state)

    while True:
        elapsed = time.time() - start_time

        if state.get("mode") == MODE_TIME and state.get("time_limit_seconds") is not None:
            if elapsed >= float(state["time_limit_seconds"]):
                return finish_loss(state, stats, start_time, reason="time")

        if state["max_attempts"] > 0 and state["attempts_used"] >= state["max_attempts"]:
            break

        time_left = get_time_left(state, start_time)
        user_input = ask_guess_or_command(state, time_left)

        if user_input is None:
            continue

        if state.get("mode") == MODE_TIME and state.get("time_limit_seconds") is not None:
            if time.time() - start_time >= float(state["time_limit_seconds"]):
                return finish_loss(state, stats, start_time, reason="time")

        if user_input == "SAVE":
            state["elapsed_seconds"] = time.time() - start_time

            if save_game_state(state):
                print("Игра сохранена. Вы можете продолжить позже.")
                return None

            print("Игра не была сохранена из-за ошибки. Попробуйте сохранить позже.")
            continue

        guess = user_input

        state["attempts_used"] += 1
        state["history"].append(guess)

        if guess == state["secret_number"]:
            elapsed_seconds = time.time() - start_time

            print(f"Поздравляем! Вы угадали число {state['secret_number']}.")
            print(f"Вы победили за {state['attempts_used']} попыток.")
            print(f"Время игры: {elapsed_seconds:.1f} сек.")

            update_stats(stats, True, state["attempts_used"], elapsed_seconds, state)
            save_stats(stats)
            clear_save()

            return True

        if guess < state["secret_number"]:
            print("Слишком маленькое число.")
        else:
            print("Слишком большое число.")

        if state["max_attempts"] > 0:
            attempts_left = state["max_attempts"] - state["attempts_used"]
            print(f"Осталось попыток: {attempts_left}.")

        # Автоматическое сохранение после каждой неправильной попытки.
        state["elapsed_seconds"] = time.time() - start_time
        save_game_state(state)

    return finish_loss(state, stats, start_time, reason="attempts")


def main():
    """
    Главная функция программы.
    """
    stats = load_stats()

    print("=" * 55)
    print("Игра «Угадай число»: режимы, сложности, сохранение, статистика")
    print("=" * 55)

    while True:
        print("\nМеню:")
        print("1 - Новая игра")
        print("2 - Продолжить сохранённую игру")
        print("3 - Инструкция")
        print("4 - Показать статистику")
        print("5 - Выход")

        choice = input("Выберите пункт: ").strip().lower()

        if choice == "1":
            if os.path.exists(SAVE_FILE):
                if not ask_yes_no("Найдено сохранение. Новая игра удалит его. Продолжить? (да/нет): "):
                    continue

                clear_save()

            settings = choose_game_settings()

            if settings is None:
                continue

            (
                mode,
                difficulty,
                min_number,
                max_number,
                max_attempts,
                time_limit_seconds
            ) = settings

            state = create_new_game_state(
                min_number=min_number,
                max_number=max_number,
                max_attempts=max_attempts,
                mode=mode,
                difficulty=difficulty,
                time_limit_seconds=time_limit_seconds
            )

            play_game(state, stats)

        elif choice == "2":
            state = load_game_state()

            if state is None:
                print("Сохранённая игра не найдена или файл сохранения повреждён.")
            else:
                play_game(state, stats)

        elif choice == "3":
            print_instructions()

        elif choice == "4":
            show_stats(stats)

        elif choice == "5":
            print("Спасибо за игру! До встречи!")
            break

        else:
            print("Неверный пункт меню. Введите 1, 2, 3, 4 или 5.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nИгра прервана пользователем.")
    except EOFError:
        print("\nИгра остановлена.")
