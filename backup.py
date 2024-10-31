import os
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from database import add_person_to_db, find_person_by_iin, initialize_database

# Initialize the database on startup
initialize_database()

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
        bot.register_next_step_handler(message, add_person_iin)

# Search Person Flow
def search_person(message):
    iin = message.text
    user_id = message.chat.id
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

# Add Person Flow - Step-by-Step
def add_person_iin(message):
    user_id = message.chat.id
    user_data[user_id]['iin'] = message.text  # Store ИИН
    bot.send_message(user_id, "Человек является преступником? (Да/Нет)")
    bot.register_next_step_handler(message, add_person_is_criminal)

def add_person_is_criminal(message):
    user_id = message.chat.id
    user_data[user_id]['is_criminal'] = message.text.lower() == 'да'
    bot.send_message(user_id, "Человек является мужчиной? (Да/Нет)")
    bot.register_next_step_handler(message, add_person_is_man)

def add_person_is_man(message):
    user_id = message.chat.id
    user_data[user_id]['is_man'] = message.text.lower() == 'да'
    bot.send_message(user_id, "Человек является ребенком? (Да/Нет)")
    bot.register_next_step_handler(message, add_person_is_child)

def add_person_is_child(message):
    user_id = message.chat.id
    user_data[user_id]['is_child'] = message.text.lower() == 'да'
    bot.send_message(user_id, "Человек является студентом? (Да/Нет)")
    bot.register_next_step_handler(message, add_person_is_student)

def add_person_is_student(message):
    user_id = message.chat.id
    user_data[user_id]['is_student'] = message.text.lower() == 'да'
    bot.send_message(user_id, "Добавьте описание человека:")
    bot.register_next_step_handler(message, add_person_description)

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