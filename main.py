import json
import os
import random
import time
from datetime import datetime

SAVE_FILE = "save.json"
STATS_FILE = "stats.json"

MIN_NUMBER = 1
MAX_NUMBER = 100
MAX_ATTEMPTS = 10

SAVE_COMMANDS = {"save", "s", "сохранить"}
YES_ANSWERS = {"да", "yes", "y", "д"}


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


def create_new_game_state(min_number=MIN_NUMBER, max_number=MAX_NUMBER, max_attempts=MAX_ATTEMPTS):
    """
    Создаёт новое состояние игры.
    """
    return {
        "secret_number": random.randint(min_number, max_number),
        "min_number": min_number,
        "max_number": max_number,
        "max_attempts": max_attempts,
        "attempts_used": 0,
        "history": [],
        "elapsed_seconds": 0.0,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "saved_at": None
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

    if state["max_attempts"] <= 0:
        return None

    if state["attempts_used"] < 0 or state["attempts_used"] > state["max_attempts"]:
        return None

    if state["min_number"] > state["max_number"]:
        return None

    if not (state["min_number"] <= state["secret_number"] <= state["max_number"]):
        return None

    if state["elapsed_seconds"] < 0:
        state["elapsed_seconds"] = 0.0

    return state


def ask_yes_no(question):
    """
    Задаёт вопрос с ответом да/нет.
    """
    answer = input(question).strip().lower()
    return answer in YES_ANSWERS


def ask_guess_or_command(state):
    """
    Запрашивает у пользователя число или команду сохранения.
    Возвращает:
    - "SAVE", если пользователь хочет сохранить игру;
    - None, если ввод некорректный;
    - int, если введено корректное число.
    """
    prompt = (
        f"Попытка {state['attempts_used'] + 1} из {state['max_attempts']}. "
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
        "range": f"{state['min_number']}-{state['max_number']}"
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
            result_text = "победа" if game.get("result") == "win" else "поражение"
            finished_at = game.get("finished_at", "неизвестно")
            attempts_used = game.get("attempts_used", "?")
            time_seconds = game.get("time_seconds", "?")
            game_range = game.get("range", "?")

            print(
                f"- {finished_at}: {result_text}, "
                f"попыток: {attempts_used}, "
                f"время: {time_seconds} сек., "
                f"диапазон: {game_range}"
            )
    else:
        print("\nИстория игр пока пуста.")


def play_game(state, stats):
    """
    Основной игровой процесс.
    Возвращает:
    - True, если игрок победил;
    - False, если игрок проиграл;
    - None, если игра была сохранена и завершена без результата.
    """
    # Если игра загружена из сохранения, учитываем уже прошедшее время.
    start_time = time.time() - float(state.get("elapsed_seconds", 0.0))

    print("\nИгра началась!")
    print(f"Я загадал число от {state['min_number']} до {state['max_number']}.")
    print(f"У вас есть {state['max_attempts']} попыток.")

    if state["attempts_used"] > 0:
        print(f"Это сохранённая игра. Уже использовано попыток: {state['attempts_used']}.")
        print(f"Ваши прошлые попытки: {', '.join(map(str, state['history']))}")

    # Сохраняем состояние при входе в игру, чтобы можно было возобновить даже до первого хода.
    save_game_state(state)

    while state["attempts_used"] < state["max_attempts"]:
        user_input = ask_guess_or_command(state)

        if user_input is None:
            continue

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

        attempts_left = state["max_attempts"] - state["attempts_used"]
        print(f"Осталось попыток: {attempts_left}.")

        # Автоматическое сохранение после каждой неправильной попытки.
        state["elapsed_seconds"] = time.time() - start_time
        save_game_state(state)

    elapsed_seconds = time.time() - start_time

    print("\nПопытки закончились.")
    print(f"Загаданное число было: {state['secret_number']}.")
    print(f"Время игры: {elapsed_seconds:.1f} сек.")

    update_stats(stats, False, state["attempts_used"], elapsed_seconds, state)
    save_stats(stats)
    clear_save()

    return False


def main():
    """
    Главная функция программы.
    """
    stats = load_stats()

    print("=" * 45)
    print("Игра «Угадай число» с сохранением и статистикой")
    print("=" * 45)

    while True:
        print("\nМеню:")
        print("1 - Новая игра")
        print("2 - Продолжить сохранённую игру")
        print("3 - Показать статистику")
        print("4 - Выход")

        choice = input("Выберите пункт: ").strip().lower()

        if choice == "1":
            if os.path.exists(SAVE_FILE):
                if not ask_yes_no("Найдено сохранение. Новая игра удалит его. Продолжить? (да/нет): "):
                    continue

                clear_save()

            state = create_new_game_state()
            play_game(state, stats)

        elif choice == "2":
            state = load_game_state()

            if state is None:
                print("Сохранённая игра не найдена или файл сохранения повреждён.")
            else:
                play_game(state, stats)

        elif choice == "3":
            show_stats(stats)

        elif choice == "4":
            print("Спасибо за игру! До встречи!")
            break

        else:
            print("Неверный пункт меню. Введите 1, 2, 3 или 4.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nИгра прервана пользователем.")
    except EOFError:
        print("\nИгра остановлена.")
