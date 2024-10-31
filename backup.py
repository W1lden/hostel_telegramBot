import os
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import asyncio
from database import add_person_to_db, find_person_by_iin

# Load environment variables from .env file
load_dotenv()

# Get the token from the environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize the bot
bot = AsyncTeleBot(TOKEN)

# Dictionaries to track user states and data
user_state = {}
user_data = {}

# Create the main menu with two buttons
def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    search_button = KeyboardButton("Поиск человек")  # Search person
    add_button = KeyboardButton("Добавить человека")  # Add person
    markup.add(search_button, add_button)
    return markup

# Start command to display the menu
@bot.message_handler(commands=["start"])
async def hello_message(message):
    markup = get_main_menu()  # Create the keyboard with the buttons
    await bot.send_message(message.chat.id, "Привет! Выберите действие:", reply_markup=markup)

# Handle the user's choice of action
@bot.message_handler(func=lambda message: message.text in ["Поиск человек", "Добавить человека"])
async def handle_choice(message):
    user_id = message.chat.id

    if message.text == "Поиск человек":
        # Set user state to "search"
        user_state[user_id] = "search"
        await bot.send_message(user_id, "Введите ИИН для поиска: ")

    elif message.text == "Добавить человека":
        # Set user state to "add"
        user_state[user_id] = "add"
        await bot.send_message(user_id, "Введите ИИН для добавления: ")

# Handle ИИН input for both search and add actions
@bot.message_handler(func=lambda message: True)
async def handle_iin_input(message):
    user_id = message.chat.id
    iin = message.text  # The ИИН input by the user

    if user_id in user_state:
        if user_state[user_id] == "search":
            # Search logic (same as before)
            person = find_person_by_iin(iin)
            if person:
                is_criminal, is_man, is_child, is_student, description = person[1:]
                await bot.send_message(
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
                await bot.send_message(user_id, f"Человек с ИИН {iin} не найден.")
            del user_state[user_id]

        elif user_state[user_id] == "add":
            # Initialize user_data to collect details
            user_data[user_id] = {'iin': iin}
            await bot.send_message(user_id, "Человек является преступником? (Да/Нет)")
            user_state[user_id] = "add_is_criminal"

# Handle each step of the Add Person flow
@bot.message_handler(func=lambda message: True)
async def handle_add_person(message):
    user_id = message.chat.id
    text = message.text.lower()

    # Only proceed if the user is in the add person flow
    if user_id in user_state and user_state[user_id].startswith("add"):
        if user_state[user_id] == "add_is_criminal":
            user_data[user_id]['is_criminal'] = text == 'да'
            await bot.send_message(user_id, "Человек является мужчиной? (Да/Нет)")
            user_state[user_id] = "add_is_man"
        
        elif user_state[user_id] == "add_is_man":
            user_data[user_id]['is_man'] = text == 'да'
            await bot.send_message(user_id, "Человек является ребенком? (Да/Нет)")
            user_state[user_id] = "add_is_child"
        
        elif user_state[user_id] == "add_is_child":
            user_data[user_id]['is_child'] = text == 'да'
            await bot.send_message(user_id, "Человек является студентом? (Да/Нет)")
            user_state[user_id] = "add_is_student"
        
        elif user_state[user_id] == "add_is_student":
            user_data[user_id]['is_student'] = text == 'да'
            await bot.send_message(user_id, "Добавьте описание человека:")
            user_state[user_id] = "add_description"
        
        elif user_state[user_id] == "add_description":
            # Save the description and add the person to the database
            user_data[user_id]['description'] = message.text
            add_person_to_db(user_data[user_id]['iin'], user_data[user_id])

            await bot.send_message(user_id, "Человек успешно добавлен в базу данных.")
            # Clear the state and data for the user
            del user_state[user_id]
            del user_data[user_id]

# Start polling for messages
asyncio.run(bot.polling())
