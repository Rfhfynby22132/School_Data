import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import TOKEN, DATABASE
from logict import Data1
import threading
import time
from datetime import datetime

bot = telebot.TeleBot(TOKEN)
manager = Data1(DATABASE)

# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
def main_menu_keyboard():
    """Главное меню с выбором роли"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Ученик"), KeyboardButton("Учитель"))
    return markup

def student_menu_keyboard():
    """Кнопки для ученика"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Всё расписание", callback_data="student_all"))
    markup.add(InlineKeyboardButton("Расписание на день", callback_data="student_day"))
    return markup

def teacher_menu_keyboard():
    """Кнопки для учителя"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Всё расписание", callback_data="teacher_all"))
    markup.add(InlineKeyboardButton("Редактировать расписание", callback_data="teacher_edit"))
    return markup

def days_keyboard():
    """Клавиатура с днями недели"""
    markup = InlineKeyboardMarkup(row_width=2)
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    buttons = [InlineKeyboardButton(day, callback_data=f"day_{day}") for day in days]
    markup.add(*buttons)
    markup.add(InlineKeyboardButton("Назад", callback_data="back_to_student"))
    return markup

def format_schedule(rows):
    """Форматирует расписание в красивую строку"""
    if not rows:
        return "Расписание пусто."
    result = ""
    current_day = ""
    for row in rows:
        if row["day"] != current_day:
            current_day = row["day"]
            result += f"\n\n *{current_day}*\n"
        result += f" {row['time']}  |  {row['class']}  |  {row['lessons']}\n"
    return result.strip()

# ---------- ОБРАБОТЧИКИ КОМАНД ----------
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        " *Школьный расписание-бот*\n\n"
        "Я помогаю ученикам и учителям.\n"
        "• Ученики могут посмотреть расписание на любой день или всё сразу.\n"
        "• Учителя могут просматривать и *редактировать* расписание.\n\n"
        "Используй кнопки внизу ",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text == " Ученик")
def student_role(message):
    bot.send_message(
        message.chat.id,
        "Выбери, что хочешь увидеть:",
        reply_markup=student_menu_keyboard()
    )

@bot.message_handler(func=lambda message: message.text == " Учитель")
def teacher_role(message):
    bot.send_message(
        message.chat.id,
        "Выбери действие:",
        reply_markup=teacher_menu_keyboard()
    )

# ---------- INLINE CALLBACKS ----------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    # Ученик: всё расписание
    if call.data == "student_all":
        rows = manager.get_all_schedule()
        text = format_schedule(rows)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f" *Полное расписание*\n{text}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton(" Назад", callback_data="back_to_student")
            )
        )
    # Ученик: выбрать день
    elif call.data == "student_day":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Выбери день недели:",
            reply_markup=days_keyboard()
        )
    # Ученик: расписание на конкретный день
    elif call.data.startswith("day_"):
        day = call.data.split("_", 1)[1]
        rows = manager.get_schedule_by_day(day)
        text = format_schedule(rows)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f" *{day}*\n{text}",
            parse_mode="Markdown",
            reply_markup=days_keyboard()
        )
    # Учитель: всё расписание
    elif call.data == "teacher_all":
        rows = manager.get_all_schedule()
        text = format_schedule(rows)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f" *Расписание для учителя*\n{text}",
            parse_mode="Markdown",
            reply_markup=teacher_menu_keyboard()
        )
    # Учитель: редактирование (вызов команды /edit_lesson)
    elif call.data == "teacher_edit":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=" *Редактирование расписания*\n\n"
                 "Используй команды:\n"
                 "▪ `/add_lesson` – добавить новый урок\n"
                 "▪ `/edit_lesson` – изменить существующий (по ID)\n"
                 "▪ `/delete_lesson` – удалить урок (по ID)\n"
                 "▪ `/view_all` – посмотреть ID всех уроков\n\n"
                 "Формат `/add_lesson`:\n"
                 "`/add_lesson Класс : День : Время : Предмет : Преподаватель : Кабинет`\n"
                 "Пример:\n"
                 "`/add_lesson 10А : Понедельник : 09:00 : Математика : Иванов И.И. : 201`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("Назад", callback_data="back_to_teacher")
            )
        )
    # Навигация назад
    elif call.data == "back_to_student":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Выбери, что хочешь увидеть:",
            reply_markup=student_menu_keyboard()
        )
    elif call.data == "back_to_teacher":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Выбери действие:",
            reply_markup=teacher_menu_keyboard()
        )
    bot.answer_callback_query(call.id)

# ---------- КОМАНДЫ ДЛЯ УЧИТЕЛЕЙ (РЕДАКТИРОВАНИЕ) ----------
@bot.message_handler(commands=['add_lesson'])
def add_lesson_command(message):
    try:
        text = message.text[len('/add_lesson'):].strip()
        if not text:
            bot.reply_to(message, " Формат: /add_lesson Класс : День : Время : Предмет : Преподаватель : Кабинет")
            return
        parts = [p.strip() for p in text.split(" : ")]
        if len(parts) != 6:
            bot.reply_to(message, " Нужно 6 частей, разделённых ` : `\nПример: /add_lesson 10А : Понедельник : 09:00 : Математика : Иванов И.И. : 201")
            return
        class_name, day, time, subject, teacher, room = parts
        lessons = f"{subject} : {teacher} : {room}"
        success, msg = manager.add_schedule_entry(class_name, day, time, lessons)
        bot.reply_to(message, msg)
    except Exception as e:
        bot.reply_to(message, f" Ошибка: {e}")

@bot.message_handler(commands=['view_all'])
def view_all_ids(message):
    rows = manager.get_all_schedule()
    if not rows:
        bot.reply_to(message, " Расписание пусто.")
        return
    text = " *ID уроков:*\n"
    for row in rows:
        text += f"ID `{row['id']}` – {row['class']}, {row['day']}, {row['time']} – {row['lessons']}\n"
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['edit_lesson'])
def edit_lesson_command(message):
    try:
        args = message.text[len('/edit_lesson'):].strip().split()
        if len(args) < 6:
            bot.reply_to(message, " Формат: /edit_lesson ID Класс : День : Время : Предмет : Преподаватель : Кабинет")
            return
        entry_id = args[0]
        rest = " ".join(args[1:]).split(" : ")
        if len(rest) != 5:
            bot.reply_to(message, "Нужно указать: Класс : День : Время : Предмет : Преподаватель : Кабинет")
            return
        class_name, day, time, subject, teacher, room = [rest[0], rest[1], rest[2], rest[3], rest[4], rest[5]] if len(rest)==6 else (None,)
        lessons = f"{subject} : {teacher} : {room}"
        success, msg = manager.edit_schedule_entry(entry_id, class_name, day, time, lessons)
        bot.reply_to(message, msg)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

@bot.message_handler(commands=['delete_lesson'])
def delete_lesson_command(message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, " Формат: /delete_lesson ID_урока")
            return
        entry_id = parts[1]
        success, msg = manager.delete_schedule_entry(entry_id)
        bot.reply_to(message, msg)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")
 
 
# ---------- ЗАПУСК БОТА ----------
if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()