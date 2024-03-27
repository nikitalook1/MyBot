from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.callback_data import CallbackData

# Инициализация CallbackData для админских действий и пользовательских выборов
admin_cb = CallbackData("admin", "action")
check_cb = CallbackData("check", "user_id", "action")

def get_main_keyboard(user_id, admins):
    """
    Создает главную клавиатуру пользователя, добавляя кнопку админ-панели для администраторов.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    markup.add(KeyboardButton(text="Подписка"))
    markup.add(KeyboardButton(text="Модель"))
    return markup

def get_subscription_model_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("моя подписка"))
    keyboard.add(KeyboardButton("модель"))
    return keyboard

def get_admin_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    markup.row_width = 2
    markup.add(KeyboardButton("Создать модель", callback_data="create_model"),
               KeyboardButton("Подписчики", callback_data="subscribers"))
    return markup


def get_subscription_levels_keyboard():
    """
    Создает клавиатуру для выбора уровня подписки.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    markup.add(KeyboardButton(text="1 уровень"), KeyboardButton(text="2 уровень"), KeyboardButton(text="3 уровень"),
               KeyboardButton(text="4 уровень"))
    return markup

def get_post_payment_keyboard():
    """
    Создает клавиатуру после оплаты, предлагая варианты действий.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=1)
    markup.add(
        KeyboardButton(text="Назад"),
        KeyboardButton(text="Оплатил"),
        KeyboardButton(text="Меню")
    )
    return markup


def get_subscription_model_keyboard():
    # Возвращаем клавиатуру для пользователей с активной подпиской
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    markup.add(KeyboardButton(text="Моя подписка"))
    markup.add(KeyboardButton(text="Модели"))
    return markup