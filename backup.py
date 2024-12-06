import os
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from database import add_person_to_db, find_person_by_iin

# Load environment variables from .env file
load_dotenv()

# Get the token from the environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize the bot
bot = TeleBot(TOKEN)

# Create the main menu with two buttons
def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    search_button = KeyboardButton("Поиск человек")  # Search person
    add_button = KeyboardButton("Добавить человека")  # Add person
    markup.add(search_button, add_button)
    return markup

# Dictionary to hold temporary data for each user during the add person flow
user_data = {}

# Start command to display the menu
@bot.message_handler(commands=["start"])
def hello_message(message):
    markup = get_main_menu()  # Create the keyboard with the buttons
    bot.send_message(message.chat.id, "Привет! Выберите действие:", reply_markup=markup)

# Handle the user's choice of action
@bot.message_handler(func=lambda message: message.text in ["Поиск человек", "Добавить человека"])
def handle_choice(message):
    user_id = message.chat.id

    if message.text == "Поиск человек":
        # Ask for ИИН and set the handler to search
        bot.send_message(user_id, "Введите ИИН для поиска: ")
        bot.register_next_step_handler(message, search_person)

    elif message.text == "Добавить человека":
        # Set up user_data and ask for ИИН to start the add person flow
        user_data[user_id] = {}
        bot.send_message(user_id, "Введите ИИН для добавления: ")
        bot.register_next_step_handler(message, validate_and_add_person_iin)

# Validate ИИН and Check for Existing Person
def validate_and_add_person_iin(message):
    user_id = message.chat.id
    iin = message.text.strip()

    # Check if ИИН is a 12-digit integer
    if not iin.isdigit() or len(iin) != 12:
        bot.send_message(user_id, "ИИН должен быть 12-значным числом. Попробуйте снова.")
        return  # End here if the ИИН is invalid

    # Check if the person already exists in the database
    if find_person_by_iin(iin):
        bot.send_message(user_id, f"Человек с ИИН {iin} уже существует в базе данных.")
    else:
        # If the ИИН is valid and the person doesn't exist, proceed with questions
        user_data[user_id]['iin'] = iin  # Store ИИН
        bot.send_message(
            user_id,
            "Отлично! Теперь ответьте на следующие вопросы:\n"
            "Человек является преступником? (Да/Нет)\n"
            "Человек является мужчиной? (Да/Нет)\n"
            "Человек является ребенком? (Да/Нет)\n"
            "Человек является студентом? (Да/Нет)\n"
            "Пожалуйста, ответьте одной строкой, разделяя ответы пробелами (например: да нет да да)"
        )
        bot.register_next_step_handler(message, add_person_questions)

# Search Person Flow
def search_person(message):
    iin = message.text.strip()
    user_id = message.chat.id

    # Validate ИИН for search as well
    if not iin.isdigit() or len(iin) != 12:
        bot.send_message(user_id, "ИИН должен быть 12-значным числом. Попробуйте снова.")
        return

    # Search for the person
    person = find_person_by_iin(iin)
    if person:
        is_criminal, is_man, is_child, is_student, description = person[1:]
        bot.send_message(
            user_id,
            f"Информация о человеке:\n"
            f"ИИН: {iin}\n"
            f"Преступник: {'Да' if is_criminal else 'Нет'}\n"
            f"Мужчина: {'Да' if is_man else 'Нет'}\n"
            f"Ребёнок: {'Да' if is_child else 'Нет'}\n"
            f"Студент: {'Да' if is_student else 'Нет'}\n"
            f"Описание: {description}"
        )
    else:
        bot.send_message(user_id, f"Человек с ИИН {iin} не найден.")

# Handle responses to all questions in a single message
def add_person_questions(message):
    user_id = message.chat.id
    responses = message.text.strip().lower().split()  # Split responses by spaces

    if len(responses) != 4:
        bot.send_message(user_id, "Пожалуйста, введите ровно 4 ответа, разделяя их пробелами (например: да нет да да).")
        return

    # Parse and store each response
    user_data[user_id]['is_criminal'] = responses[0] == 'да'
    user_data[user_id]['is_man'] = responses[1] == 'да'
    user_data[user_id]['is_child'] = responses[2] == 'да'
    user_data[user_id]['is_student'] = responses[3] == 'да'

    # Ask for a description after storing the responses
    bot.send_message(user_id, "Добавьте описание человека:")
    bot.register_next_step_handler(message, add_person_description)

# Save the description and add person to the database
def add_person_description(message):
    user_id = message.chat.id
    user_data[user_id]['description'] = message.text  # Save description

    # Save person to the database
    add_person_to_db(user_data[user_id]['iin'], user_data[user_id])

    bot.send_message(user_id, "Человек успешно добавлен в базу данных.")
    # Clear user data after adding the person
    del user_data[user_id]

# Start the bot in polling mode
bot.polling()
