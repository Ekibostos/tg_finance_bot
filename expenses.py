""" Работа с расходами — их добавление, удаление, статистики"""
import datetime
import re
from typing import List, NamedTuple, Optional

import pytz
from datetime import timezone

import db
import exceptions
from categories import Categories


class Message(NamedTuple):
    """Структура распаршенного сообщения о новом расходе"""
    amount: int
    category_text: str


class Expense(NamedTuple):
    """Структура добавленного в БД нового расхода"""
    id: Optional[int]
    amount: int
    category_name: str


def add_expense_in_one_srtep(raw_message: str) -> Expense:
    parsed_message = _parse_message(raw_message)
    return add_expense(parsed_message)


def add_expense_in_two_steps(amount: int, message_text: str) -> Expense:
    parsed_message = Message(amount=amount, category_text=message_text)
    return add_expense(parsed_message)


def add_expense(parsed_message) -> Expense:
    """Добавляет новое сообщение.
    Принимает на вход текст сообщения, пришедшего в бот."""
    category = Categories().get_category(
        parsed_message.category_text)
    inserted_row_id = db.insert("expense", {
        "amount": parsed_message.amount,
        "created": _get_now_formatted(),
        "category_codename": category.codename,
        "raw_text": (str(parsed_message.amount) + " " + parsed_message.category_text)
    })
    return Expense(id=None,
                   amount=parsed_message.amount,
                   category_name=category.name)


def get_today_statistics() -> str:
    """Возвращает строкой статистику расходов за сегодня"""
    cursor = db.get_cursor()
    cursor.execute("select sum(amount)"
                   "from expense where date(created)=date('now', 'localtime')")
    result = cursor.fetchone()
    if not result[0]:
        return "Сегодня ещё нет расходов"
    all_today_expenses = result[0]
    cursor.execute("select sum(amount) "
                   "from expense where date(created)=date('now', 'localtime') "
                   "and category_codename in (select codename "
                   "from category where is_base_expense=true)")
    result = cursor.fetchone()
    base_today_expenses = result[0] if result[0] else 0
    return (f"Расходы сегодня:\n"
            f"всего — {all_today_expenses} руб.\n"
            f"базовые — {base_today_expenses} руб. из {_get_budget_limit()} руб.\n\n"
            f"{get_remainder()}")


def get_month_statistics() -> str:
    """Возвращает строкой статистику расходов за текущий месяц"""
    now = _get_now_datetime()
    first_day_of_month = f'{now.year:04d}-{now.month:02d}-01'
    cursor = db.get_cursor()
    cursor.execute(f"select sum(amount) "
                   f"from expense where date(created) >= '{first_day_of_month}'")
    result = cursor.fetchone()
    if not result[0]:
        return "В этом месяце ещё нет расходов"
    all_today_expenses = result[0]
    cursor.execute(f"select sum(amount) "
                   f"from expense where date(created) >= '{first_day_of_month}' "
                   f"and category_codename in (select codename "
                   f"from category where is_base_expense=true)")
    result = cursor.fetchone()
    base_today_expenses = result[0] if result[0] else 0
    return (f"Расходы в текущем месяце:\n"
            f"всего — {all_today_expenses} руб.\n"
            f"базовые — {base_today_expenses} руб. из "
            f"{now.day * _get_budget_limit()} руб.\n\n"
            f"{get_remainder()}")


def get_remainder() -> str:
    cursor = db.get_cursor()
    now = _get_now_datetime()
    first_day_of_month = f'{now.year:04d}-{now.month:02d}-01'
    cursor.execute(f"select sum(amount) "
                   f"from expense where date(created) >= '{first_day_of_month}' "
                   f"and category_codename in (select codename "
                   f"from category where is_base_expense=true)")
    result = cursor.fetchone()
    base_today_expenses = result[0] if result[0] else 0
    return (f"Сегодня вы можете потратить ещё:\n"
            f"{(now.day * _get_budget_limit()) - base_today_expenses} руб.")


def get_month_category_statistics(category_name) -> str:
    """Возвращает строкой статистику расходов за текущий месяц"""
    search_month_expenses = month_category_statistics(category_name)
    if search_month_expenses == 0:
        return "В этом месяце ещё нет расходов"
    return (f"Расходы в текущем месяце:\n"
            f"в категории {category_name} — {search_month_expenses} руб.\n")


def month_category_statistics(category_name) -> str:
    """Возвращает сумму расходов по имени категории"""
    now = _get_now_datetime()
    first_day_of_month = f'{now.year:04d}-{now.month:02d}-01'
    cursor = db.get_cursor()
    cursor.execute(f"select sum(amount) "
                   f"from expense where date(created) >= '{first_day_of_month}' "
                   f"and category_codename in (select codename "
                   f"from category where name='{category_name}')")
    result = cursor.fetchone()
    if not result[0]:
        return 0
    search_month_expenses = result[0] if result[0] else 0
    return search_month_expenses


def get_sort_string_categories(categories):
    """Возвращает строку, перечисляет все категории разбитые на две группы"""
    base_categories = []
    other_categories = []
    for c in categories:
        if c.is_base_expense:
            base_categories.append(c)
        else:
            other_categories.append(c)
    answer_message = "Категории трат:\n\n Необходимые: \n\n* " + \
            ("\n* ".join([c.name+' ('+", ".join(c.aliases)+')' for c in base_categories])) + \
            "\n\nОстальные: \n\n*" + \
            ("\n* ".join([c.name+' ('+", ".join(c.aliases)+')' for c in other_categories]))
    return(answer_message)


def last() -> List[Expense]:
    """Возвращает последние несколько расходов"""
    cursor = db.get_cursor()
    cursor.execute(
        "select e.id, e.amount, c.name "
        "from expense e left join category c "
        "on c.codename=e.category_codename "
        "order by created desc limit 10")
    rows = cursor.fetchall()
    last_expenses = [Expense(id=row[0], amount=row[1], category_name=row[2]) for row in rows]
    return last_expenses


def delete_expense(row_id: int) -> None:
    """Удаляет сообщение по его идентификатору"""
    db.delete("expense", row_id)


def _parse_message(raw_message: str) -> Message:
    """Парсит текст пришедшего сообщения о новом расходе."""
    regexp_result = re.match(r"([\d ]+) (.*)", raw_message)
    if not regexp_result or not regexp_result.group(0) \
            or not regexp_result.group(1) or not regexp_result.group(2):
        raise exceptions.NotCorrectMessage(
            "Не могу понять сообщение. Напишите сообщение в формате, "
            "например:\n1500 метро\nЕсли нужна помощь введи /help")

    amount = regexp_result.group(1).replace(" ", "")
    category_text = regexp_result.group(2).strip().lower()
    return Message(amount=amount, category_text=category_text)


def _get_now_formatted() -> str:
    """Возвращает сегодняшнюю дату строкой"""
    return _get_now_datetime().strftime("%Y-%m-%d %H:%M:%S")


def _get_now_datetime() -> datetime.datetime:
    """Возвращает сегодняшний datetime с учётом времненной зоны Екб."""
    tz = pytz.timezone("Asia/Yekaterinburg")
    now = datetime.datetime.now(tz)
    return now


def _get_budget_limit() -> int:
    """Возвращает дневной лимит трат для основных базовых трат"""
    return db.fetchall("budget", ["daily_limit"])[0]["daily_limit"]
