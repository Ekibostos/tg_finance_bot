"""Сервер Telegram бота, запускаемый непосредственно"""
import logging
import os

import telebot;
from telebot import types;

import exceptions
import expenses
import graph
from categories import Categories


# Для авторизации бота в телеграм
bot = telebot.TeleBot('TG_BOT_TOKEN');


vvod = 0 # Глобальная переменная


# Блокирует доступ всем пользователям кроме тех кто в списке users
# 
# Печатает в консоль user_id пользователей которые обращались к боту, но отсутствуют в списке
# Это сделано чтоб упростить поиск и добавление новых пользователей
def block_users(user_id):
    users = ['USER_ID]
    if user_id in users:
        return False
    else:
        print(user_id)
        bot.send_message(message.chat.id, 'Администратор не добавил вас в список пользователей этого бота')
        return True


def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn5 = types.KeyboardButton("Помощь")
    btn1 = types.KeyboardButton("Категории")
    btn2 = types.KeyboardButton("Статистика за месяц")
    btn3 = types.KeyboardButton("Статистика за день")
    btn4 = types.KeyboardButton("Последние записи")
    btn6 = types.KeyboardButton("График расходов")
    markup.add(btn1)
    markup.add(btn2)
    markup.add(btn3)
    markup.add(btn4)
    markup.add(btn5)
    markup.add(btn6)
    return markup


@bot.message_handler(commands=['start'])
def start(message):
    if block_users(str(message.from_user.id)):
        return
    markup = main_menu()
    bot.send_message(message.chat.id, text="Привет, {0.first_name}! Я бот для учёта финансов,\
                                             отправь мне сумму и категорию затрат и я их запомню"\
                                             .format(message.from_user), reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == '/help' or message.text == "Помощь")
def help(message):
    if block_users(str(message.from_user.id)):
        return
    markup = main_menu()
    """Отправляет приветственное сообщение и помощь по боту"""
    bot.send_message(message.chat.id, "Бот для учёта финансов\n\n"
        "Добавить расход: 250 такси\n"
        "Или просто 250, а потом выбрать категорию из меню\n\n"
        "Сегодняшняя статистика: /today\n"
        "За текущий месяц: /month\n"
        "Последние внесённые расходы: /expenses\n"
        "Категории трат: /categories")
    categories = Categories().get_all_categories()
    bot.send_message(message.chat.id, expenses.get_sort_string_categories(categories), reply_markup=markup)


@bot.message_handler(func=lambda message: message.text.startswith('/del'))
def delit(message):
    if block_users(str(message.from_user.id)):
        return
    """Удаляет одну запись о расходе по её идентификатору"""
    row_id = int(message.text[4:])
    expenses.delete_expense(row_id)
    bot.send_message(message.chat.id, "Удалил")


@bot.message_handler(func=lambda message: message.text == "/categories" or message.text == "Категории")
def list_categories(message):
    if block_users(str(message.from_user.id)):
        return
    """Выводит в меню список категорий расходов"""
    markup = get_menu_category(True)
    bot.send_message(message.chat.id, "Выберите категорию", reply_markup=markup)
    bot.register_next_step_handler(message, category_list)


@bot.message_handler(func=lambda message: message.text == "/graph" or message.text == "График расходов")
def list_categories(message):
    if block_users(str(message.from_user.id)):
        return
    """Выводит картинку с графиком расходов"""
    markup = main_menu()
    category_list = []
    summ_list = []
    categories = Categories().get_all_categories()
    i = False
    for c in categories:
        summ_name = expenses.month_category_statistics(c.name)
        if summ_name == 0:
            pass
        else:
            category_list.append(c.name)
            summ_list.append(summ_name)
            i = True
    if i:
        pass
    else:
        bot.send_message(message.chat.id, "В этом месяце ещё нет расходов", reply_markup=markup)
        return
    bot.send_photo(message.chat.id, graph.get_graph(category_list, summ_list))



@bot.message_handler(func=lambda message: message.text == "/today" or message.text == "Статистика за день")
def day_srtstistic(message):
    if block_users(str(message.from_user.id)):
        return
    """Отправляет сегодняшнюю статистику трат"""
    answer_message = expenses.get_today_statistics()
    bot.send_message(message.chat.id, answer_message)


@bot.message_handler(func=lambda message: message.text == "/month" or message.text == "Статистика за месяц")
def month_statistic(message):
    if block_users(str(message.from_user.id)):
        return
    """Отправляет статистику трат текущего месяца"""
    answer_message = expenses.get_month_statistics()
    bot.send_message(message.chat.id, answer_message)


@bot.message_handler(func=lambda message: message.text == "/expenses" or message.text == "Последние записи")
def list_expenses(message):
    if block_users(str(message.from_user.id)):
        return
    """Отправляет последние несколько записей о расходах"""
    last_expenses = expenses.last()
    if not last_expenses:
        bot.send_message(message.chat.id, "Расходы ещё не заведены")
        return

    last_expenses_rows = [
        f"{expense.amount} руб. на {expense.category_name} — нажми "
        f"/del{expense.id} для удаления"
        for expense in last_expenses]
    answer_message = "Последние сохранённые траты:\n\n* " + "\n\n* "\
            .join(last_expenses_rows)
    bot.send_message(message.chat.id, answer_message)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if block_users(str(message.from_user.id)):
        return
    try:
        x = int(message.text)
        markup = get_menu_category(False)
        global vvod
        vvod = int(message.text)
        bot.send_message(message.chat.id, "Выберете категорию", reply_markup=markup)
        bot.register_next_step_handler(message, add_in_two_steps)
    except:
        """Добавляет новый расход"""
        try:
            expense = expenses.add_expense_in_one_srtep(message.text)
        except exceptions.NotCorrectMessage as e:
            markup = main_menu()
            bot.send_message(message.chat.id, str(e), reply_markup=markup)
            return
        answer_message = (
            f"Добавлены траты {expense.amount} руб на {expense.category_name}.\n\n"
            f"{expenses.get_today_statistics()}")
        bot.send_message(message.chat.id, answer_message)


def get_menu_category(all: bool):
    categories = Categories().get_all_categories()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if all:
        markup.add("Все категории")
    for c in categories:
        markup.add(c.name)
    return markup


def add_in_two_steps(message):
    global vvod
    markup = main_menu()
    expense = expenses.add_expense_in_two_steps(vvod, message.text)
    answer_message = (
            f"Добавлены траты {vvod} руб на {message.text}.\n\n"
            f"{expenses.get_today_statistics()}")
    bot.send_message(message.chat.id, answer_message, reply_markup=markup)


def category_list(message):
    markup = main_menu()
    if message.text == "Все категории":
        categories = Categories().get_all_categories()
        i = False
        for c in categories:
            if expenses.get_month_category_statistics(c.name) == "В этом месяце ещё нет расходов":
                pass
            else:
                bot.send_message(message.chat.id, expenses.get_month_category_statistics(c.name), reply_markup=markup)
                i = True
        if i:
            pass
        else:
            bot.send_message(message.chat.id, "В этом месяце ещё нет расходов", reply_markup=markup)
        return
    else:
        try:
            bot.send_message(message.chat.id, expenses.get_month_category_statistics(message.text), reply_markup=markup)
            return
        except:
            bot.send_message(message.chat.id, "Не нашёл категорию", reply_markup=markup)
            return


bot.polling(none_stop=True, interval=0)

