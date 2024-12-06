import os
from dotenv import load_dotenv
from telebot import TeleBot, types
from database import add_person_to_db, find_person_by_iin
from database import initialize_database

# Инициализация базы данных
initialize_database()

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = TeleBot(TOKEN)

# Состояния пользователей для анкеты
user_data = {}

# Вопросы анкеты
questions = [
    "Имеется задолженность?",
    "Проблемы со здоровьем?",
    "Психически нестабилен?",
    "Употребляет наркотики/алкоголь?"
]

# Начальное состояние кнопок
def get_initial_answers():
    return {i: "Нет" for i in range(len(questions))}

# Создание кнопок анкеты
def create_survey_markup(answers):
    markup = types.InlineKeyboardMarkup()
    for i, question in enumerate(questions):
        button = types.InlineKeyboardButton(
            text=f"{question} ({answers[i]})", callback_data=f"toggle_{i}"
        )
        markup.add(button)
    # Кнопка "Отправить"
    submit_button = types.InlineKeyboardButton("Отправить", callback_data="submit")
    markup.add(submit_button)
    return markup


# Команда /start
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет! Выберите действие:",
        reply_markup=create_main_menu()
    )

# Главное меню
def create_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Поиск человека"))
    markup.add(types.KeyboardButton("Добавить человека"))
    return markup

# Обработка выбора действия
@bot.message_handler(func=lambda message: message.text in ["Добавить человека", "Поиск человека"])
def handle_choice(message):
    user_id = message.chat.id

    if message.text == "Добавить человека":
        user_data[user_id] = {"answers": get_initial_answers()}  # Начальное состояние
        bot.send_message(user_id, "Введите ИИН для добавления:", reply_markup=None)
        bot.register_next_step_handler(message, validate_and_start_survey)

    elif message.text == "Поиск человека":
        bot.send_message(user_id, "Введите ИИН для поиска:")
        bot.register_next_step_handler(message, search_person)

# Проверка ИИН и начало анкеты
def validate_and_start_survey(message):
    user_id = message.chat.id
    iin = message.text.strip()

    if not iin.isdigit() or len(iin) != 12:
        bot.send_message(user_id, "ИИН должен быть 12-значным числом. Попробуйте снова.")
        return

    if find_person_by_iin(iin):
        bot.send_message(user_id, f"Человек с ИИН {iin} уже существует в базе данных.")
    else:
        user_data[user_id]["iin"] = iin
        bot.send_message(
            user_id,
            "Заполните анкету:",
            reply_markup=create_survey_markup(user_data[user_id]["answers"])
        )

# Обработка нажатий на кнопки
@bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_") or call.data == "submit")
def handle_survey_callback(call):
    user_id = call.message.chat.id

    if call.data.startswith("toggle_"):
        # Переключение состояния
        question_id = int(call.data.split("_")[1])
        current_answer = user_data[user_id]["answers"][question_id]
        new_answer = "Да" if current_answer == "Нет" else "Нет"
        user_data[user_id]["answers"][question_id] = new_answer

        # Обновление кнопок
        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=create_survey_markup(user_data[user_id]["answers"])
        )

    elif call.data == "submit":
        # Завершение анкеты
        answers = user_data[user_id]["answers"]
        bot.send_message(
            user_id,
            "Введите описание:"
        )
        bot.register_next_step_handler(call.message, add_person_description)

# Обработка описания
def add_person_description(message):
    user_id = message.chat.id
    user_data[user_id]["description"] = message.text

    # Сохранение в базе данных
    add_person_to_db(
        user_data[user_id]["iin"],
        {
            "has_debt": user_data[user_id]["answers"][0] == "Да",
            "health_issues": user_data[user_id]["answers"][1] == "Да",
            "mentally_unstable": user_data[user_id]["answers"][2] == "Да",
            "substance_abuse": user_data[user_id]["answers"][3] == "Да",
            "description": user_data[user_id]["description"]
        }
    )

    bot.send_message(user_id, "Человек успешно добавлен в базу данных.")
    del user_data[user_id]  # Очистка данных пользователя

# Поиск человека
def search_person(message):
    iin = message.text.strip()
    user_id = message.chat.id

    if not iin.isdigit() or len(iin) != 12:
        bot.send_message(user_id, "ИИН должен быть 12-значным числом. Попробуйте снова.")
        return

    person = find_person_by_iin(iin)
    if person:
        has_debt, health_issues, mentally_unstable, substance_abuse, description = person[1:]
        bot.send_message(
            user_id,
            f"Информация о человеке:\n"
            f"ИИН: {iin}\n"
            f"Имеется задолженность: {'Да' if has_debt else 'Нет'}\n"
            f"Проблемы со здоровьем: {'Да' if health_issues else 'Нет'}\n"
            f"Психически нестабилен: {'Да' if mentally_unstable else 'Нет'}\n"
            f"Употребляет наркотики/алкоголь: {'Да' if substance_abuse else 'Нет'}\n"
            f"Описание: {description}"
        )
    else:
        bot.send_message(user_id, f"Человек с ИИН {iin} не найден.")


# Запуск бота
bot.polling()
