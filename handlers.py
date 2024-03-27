from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from keyboards import get_main_keyboard, get_subscription_levels_keyboard, get_admin_keyboard,get_subscription_model_keyboard, check_cb, admin_cb, get_post_payment_keyboard, get_subscription_model_keyboard
from config import ADMINS, bot
import asyncio
from states import SubscriptionProcess
from database import db, cur, init_db
import sqlite3 as sq

# Словарь для хранения информации о чеках, ожидающих проверки
pending_checks = {}
next_check_id = 1

async def subscription_chosen(message: types.Message):
    await SubscriptionProcess.ChoosingLevel.set()
    await message.answer("Выберите уровень подписки:", reply_markup=get_subscription_levels_keyboard())

async def subscription_level_chosen(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['level'] = message.text
    await SubscriptionProcess.WaitingForCheck.set()
    await message.answer("Пожалуйста, прикрепите чек об оплате.")

async def check_submitted(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['check_file_id'] = message.photo[-1].file_id
    await SubscriptionProcess.CheckSubmitted.set()
    await message.answer("Чек загружен. Нажмите 'Оплатил', если хотите отправить чек на проверку.", reply_markup=get_post_payment_keyboard())

async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    with sq.connect('tg.db') as db:
        cur = db.cursor()
        cur.execute("INSERT OR IGNORE INTO subscribers (user_id) VALUES (?)", (user_id,))
        db.commit()
        cur.execute("SELECT is_sub FROM subscribers WHERE user_id = ?", (user_id,))
        sub_status = cur.fetchone()#vjdvch

    if user_id in ADMINS:
        await message.answer("Вы администратор.", reply_markup=get_admin_keyboard())
    elif sub_status and sub_status[0]:
        await message.answer("Что вы хотите сделать?", reply_markup=get_subscription_model_keyboard())
    else:
        await message.answer("Что вы хотите сделать?", reply_markup=get_main_keyboard(user_id, ADMINS))


async def payment_confirmed(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if 'check_file_id' in data:
            user_id = message.from_user.id
            global next_check_id
            check_id = next_check_id
            next_check_id += 1

            pending_checks[check_id] = {'user_id': user_id, 'check_file_id': data['check_file_id'], 'level': data['level']}

            for admin_id in ADMINS:
                await bot.send_photo(admin_id, data['check_file_id'], caption=f"Новый чек #{check_id} от пользователя {user_id}. Для подтверждения напишите /accept {check_id}")

            await message.answer("Чек отправлен на проверку. Ожидайте подтверждения админом.")
        else:
            await message.answer("Чек не найден, попробуйте еще раз.")

    await state.finish()

async def run_in_executor(func, *args):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, func, *args)

def update_subscription_level(user_id, level):
    # List of valid subscription levels
    valid_levels = ["1 уровень", "2 уровень", "3 уровень", "4 уровень"]

    if level not in valid_levels:
        print(f"Invalid subscription level: {level}")
        return

    try:
        db, cur = init_db()
        cur.execute("UPDATE subscribers SET sub_level = ?, is_sub = 1 WHERE user_id = ?", (level, user_id))
        db.commit()
        print(f"Subscription level for user {user_id} updated to {level}.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_cmd, commands=['start'])
    dp.register_message_handler(subscription_chosen, text='Подписка', state='*')
    dp.register_message_handler(subscription_level_chosen, state=SubscriptionProcess.ChoosingLevel)
    dp.register_message_handler(check_submitted, content_types=['photo'], state=SubscriptionProcess.WaitingForCheck)
    dp.register_message_handler(payment_confirmed, text='Оплатил', state=SubscriptionProcess.CheckSubmitted)

    @dp.message_handler(commands=['accept'])
    async def accept_payment(message: types.Message):
        if message.from_user.id not in ADMINS:
            await message.answer("У вас нет доступа к этой команде.")
            return

        try:
            _, check_id_str = message.text.split()
            check_id = int(check_id_str)
        except ValueError:
            await message.answer("Некорректный формат команды. Используйте /accept {номер чека}.")
            return

        if check_id not in pending_checks:
            await message.answer(f"Чек с ID {check_id} не найден.")
            return

        check_info = pending_checks.pop(check_id)
        await run_in_executor(update_subscription_level, check_info['user_id'], check_info['level'])

        await bot.send_message(check_info['user_id'], "Ваша подписка успешно активирована.",
                               reply_markup=get_subscription_model_keyboard())
        await message.answer(f"Чек #{check_id} подтвержден. Подписка активирована.")

    @dp.callback_query_handler(text="create_model", user_id=ADMINS)
    async def handle_create_model(callback_query: types.CallbackQuery):
        # Здесь может быть логика создания модели
        await callback_query.answer("Функционал создания модели.", show_alert=True)

    @dp.callback_query_handler(text="subscribers", user_id=ADMINS)
    async def handle_subscribers(callback_query: types.CallbackQuery):
        # Получаем список всех подписчиков из базы данных
        cur.execute("SELECT user_id FROM subscribers WHERE is_sub = 1")
        subscribers = cur.fetchall()

        if not subscribers:
            await callback_query.message.answer("Список подписчиков пуст.")
            return

        # Формируем сообщение со списком подписчиков
        subscribers_list = "Список подписчиков:\n"
        for subscriber in subscribers:
            subscribers_list += f"ID: {subscriber[0]}\n"

        await callback_query.message.answer(subscribers_list)