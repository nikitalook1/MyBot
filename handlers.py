from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from keyboards import get_main_keyboard, get_subscription_levels_keyboard, get_admin_keyboard, get_post_payment_keyboard, get_subscription_model_keyboard
from config import ADMINS, bot
import asyncio
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from states import SubscriptionProcess, ModelCreation
from database import cur, init_db
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

            pending_checks[check_id] = {'user_id': user_id, 'check_file_id': data['check_file_id'],
                                        'level': data['level']}

            await message.answer("Чек отправлен на проверку. Ожидайте подтверждения админом.")
        else:
            await message.answer("Чек не найден, попробуйте еще раз.")

    await state.finish()

async def run_in_executor(func, *args):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, func, *args)

def update_subscription_level(user_id, level):
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

async def create_model_callback_handler(query: types.CallbackQuery):
    await ModelCreation.waiting_for_nickname.set()
    await query.message.answer("Введите никнейм модели:")

async def model_nickname_received(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['nickname'] = message.text
    await ModelCreation.next()
    await message.answer("Теперь введите цену сборов:")

async def model_price_received(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['price'] = float(message.text)
    await ModelCreation.waiting_for_photo.set()
    await message.answer("Теперь отправьте фото модели.")


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_cmd, commands=['start'])
    dp.register_message_handler(subscription_chosen, text='Подписка', state='*')
    dp.register_message_handler(subscription_level_chosen, state=SubscriptionProcess.ChoosingLevel)
    dp.register_message_handler(check_submitted, content_types=['photo'], state=SubscriptionProcess.WaitingForCheck)
    dp.register_message_handler(payment_confirmed, text='Оплатил', state=SubscriptionProcess.CheckSubmitted)
    dp.register_callback_query_handler(create_model_callback_handler, lambda c: c.data == 'create_model', state='*')
    dp.register_message_handler(model_nickname_received, state=ModelCreation.waiting_for_nickname)
    dp.register_message_handler(model_price_received, state=ModelCreation.waiting_for_price)

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

    @dp.message_handler(lambda message: message.text == "Создать модель", state='*')
    async def handle_create_model(message: types.Message):
        # Установка состояния для ввода никнейма модели
        await ModelCreation.waiting_for_nickname.set()
        await message.answer("Введите никнейм модели:")

    @dp.message_handler(lambda message: message.text == "Подписчики", user_id=ADMINS)
    async def get_checks(message: types.Message):
        if not pending_checks:
            await message.answer("Нет чеков, ожидающих подтверждения.")
            return

        # Отправляем каждый чек администратору
        for check_id, info in pending_checks.items():
            user_id = info['user_id']
            file_id = info['check_file_id']
            level = info.get('level', 'Не указан')
            caption = f"Чек #{check_id} от пользователя {user_id}, Уровень подписки: {level}."
            await bot.send_photo(message.from_user.id, file_id, caption=caption)

    @dp.message_handler(lambda message: message.text == "Моя подписка")
    async def show_subscription_info(message: types.Message):
        user_id = message.from_user.id
        with sq.connect('tg.db') as db:
            cur = db.cursor()
            # Запрос к базе данных для получения информации о подписке пользователя
            cur.execute("SELECT sub_level, is_sub FROM subscribers WHERE user_id = ?", (user_id,))
            subscription_info = cur.fetchone()

        if subscription_info and subscription_info[1]:  # Проверяем, что подписка активна
            # Формируем и отправляем сообщение с информацией о подписке
            subscription_level = subscription_info[0]
            response_text = f"Ваша подписка: {subscription_level}.\n\nДетали подписки: [Детали подписки здесь]"
            await message.answer(response_text, parse_mode=types.ParseMode.MARKDOWN)
        else:
            # Сообщение пользователю, если подписка не найдена или не активна
            await message.answer("У вас нет активной подписки.")

    @dp.message_handler(lambda message: message.text == "Модели")
    async def handle_models_request(message: types.Message):
        user_id = message.from_user.id
        with sq.connect('tg.db') as db:
            cur = db.cursor()
            # Проверяем наличие подписки у пользователя
            cur.execute("SELECT is_sub FROM subscribers WHERE user_id = ?", (user_id,))
            sub_status = cur.fetchone()

        if not sub_status or not sub_status[0]:
            await message.answer("У вас нет подписки, сначала приобретите её.")
            return

        # Изменено на получение всех данных модели, включая photo и collected_amount
        cur.execute("SELECT id, nickname, price, photo, collected_amount FROM models")
        models = cur.fetchall()

        if not models:
            await message.answer("Моделей пока нет.")
            return

        # Изменено на отправку каждой модели с фото, описанием и суммой поддержки напрямую
        for model in models:
            model_id, nickname, price, photo_file_id, collected_amount = model
            response_text = f"Никнейм: {nickname}\nЦель: {price}\nСобрано: {collected_amount}"

            # Создаем inline кнопку "Поддержать"
            support_button = InlineKeyboardMarkup().add(
                InlineKeyboardButton("Поддержать", callback_data=f"support_{model_id}")
            )

            if photo_file_id:
                await bot.send_photo(message.chat.id, photo=photo_file_id, caption=response_text,
                                     reply_markup=support_button)
            else:
                await message.answer(text=response_text, reply_markup=support_button)

    @dp.message_handler(content_types=['photo'], state=ModelCreation.waiting_for_photo)
    async def model_photo_received(message: types.Message, state: FSMContext):
        async with state.proxy() as data:
            # Предполагаем, что фотография одна и берем последнюю в списке
            data['photo'] = message.photo[-1].file_id
            # Сохраняем модель в базу данных
            with sq.connect('tg.db') as db:
                cur = db.cursor()
                cur.execute("INSERT INTO models (nickname, price, photo) VALUES (?, ?, ?)",
                            (data['nickname'], data['price'], data['photo']))
                db.commit()
        await state.finish()
        await message.answer("Модель успешно создана с фото!")

    @dp.callback_query_handler(lambda c: c.data and c.data.startswith("show_"))
    async def show_model_details(callback_query: types.CallbackQuery):
        model_id = callback_query.data.split("_")[1]
        with sq.connect('tg.db') as db:
            cur = db.cursor()
            cur.execute("SELECT nickname, price, photo FROM models WHERE id=?", (model_id,))
            model = cur.fetchone()

        if model:
            nickname, price, photo_file_id = model
            response_text = f"Никнейм: {nickname}\nЦена: {price}"
            await bot.send_photo(callback_query.from_user.id, photo=photo_file_id, caption=response_text)
        else:
            await bot.send_message(callback_query.from_user.id, "Модель не найдена.")
        await callback_query.answer()

    @dp.callback_query_handler(lambda c: c.data and c.data.startswith("support_"))
    async def prompt_support_amount(callback_query: types.CallbackQuery, state: FSMContext):
        await state.update_data(model_id=callback_query.data.split("_")[1])
        await ModelCreation.waiting_for_support_amount.set()
        await bot.send_message(callback_query.from_user.id, "Введите сумму вашей поддержки:")
        await callback_query.answer()

    @dp.message_handler(state=ModelCreation.waiting_for_support_amount, content_types=types.ContentTypes.TEXT)
    async def process_support_amount(message: types.Message, state: FSMContext):
        try:
            amount = float(message.text)
            user_data = await state.get_data()
            model_id = user_data['model_id']

            with sq.connect('tg.db') as db:
                cur = db.cursor()
                cur.execute("UPDATE models SET collected_amount = collected_amount + ? WHERE id = ?",
                            (amount, model_id))
                db.commit()

            await message.answer("Благодарим за вашу поддержку!")
            await state.reset_state()
        except ValueError:
            await message.answer("Пожалуйста, введите корректную сумму.")
