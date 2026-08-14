import random


def play_game(min_number=1, max_number=100, max_attempts=10):
    secret_number = random.randint(min_number, max_number)

    print("\nИгра началась!")
    print(f"Я загадал число от {min_number} до {max_number}.")
    print(f"У вас есть {max_attempts} попыток.\n")

    for attempt in range(1, max_attempts + 1):
        user_input = input(f"Попытка {attempt}. Введите число: ")

        if not user_input.isdigit():
            print("Пожалуйста, введите целое число.\n")
            continue

        guess = int(user_input)

        if guess < min_number or guess > max_number:
            print(f"Число должно быть от {min_number} до {max_number}.\n")
            continue

        if guess == secret_number:
            print(f"Поздравляем! Вы угадали число {secret_number} за {attempt} попыток!")
            return True

        if guess < secret_number:
            print("Слишком маленькое число.")
        else:
            print("Слишком большое число.")

    print(f"\nПопытки закончились. Загаданное число было: {secret_number}")
    return False


def main():
    print("Добро пожаловать в игру 'Угадай число'!")

    while True:
        play_game()

        answer = input("\nХотите сыграть ещё раз? (да/нет): ").lower()

        if answer != "да":
            print("Спасибо за игру! До встречи!")
            break


if __name__ == "__main__":
    main()
