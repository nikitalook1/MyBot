from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from keyboards import get_main_keyboard, get_subscription_levels_keyboard, check_cb, admin_cb, get_check_keyboard, get_post_payment_keyboard
from config import ADMINS, bot
from states import SubscriptionProcess
from aiogram.types import CallbackQuery

# Словарь для хранения информации о чеках, ожидающих проверки
pending_checks = {}


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
    # Отправка приветственного сообщения и главной клавиатуры
    try:
        await message.answer("Привет! Что вы хотите сделать?", reply_markup=get_main_keyboard(message.from_user.id, ADMINS))
    except Exception as e:
        await message.answer(f"Произошла ошибка при отправке приветственного сообщения: {e}")

async def payment_confirmed(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        check_file_id = data.get('check_file_id')
        subscription_level = data.get('level')

    if check_file_id:
        user_id = message.from_user.id
        pending_checks[user_id] = {'check_file_id': check_file_id, 'level': subscription_level}

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Подтвердить", callback_data=check_cb.new(user_id=user_id, action="confirm")),
            types.InlineKeyboardButton("Отклонить", callback_data=check_cb.new(user_id=user_id, action="reject"))
        )

        for admin_id in ADMINS:
            await bot.send_photo(admin_id, check_file_id,
                                 caption=f"Чек от пользователя {user_id}, уровень подписки: {subscription_level}.",
                                 reply_markup=markup)

        await message.answer("Чек отправлен на проверку.", reply_markup=get_main_keyboard(message.from_user.id, ADMINS))
    else:
        await message.answer("Чек не найден, попробуйте еще раз.")

    await state.finish()


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(start_cmd, commands=['start'])
    dp.register_message_handler(subscription_chosen, text='Подписка', state='*')
    dp.register_message_handler(subscription_level_chosen, state=SubscriptionProcess.ChoosingLevel)
    dp.register_message_handler(check_submitted, content_types=['photo'], state=SubscriptionProcess.WaitingForCheck)
    dp.register_message_handler(payment_confirmed, text='Оплатил', state=SubscriptionProcess.CheckSubmitted)


    @dp.message_handler(text='Помощь')
    async def show_help(message: types.Message):
        # Отправка сообщения с информацией о помощи
        await message.answer("Если у вас возникли вопросы, вы можете обратиться к администратору.", reply_markup=get_main_keyboard(message.from_user.id, ADMINS))


    @dp.callback_query_handler(admin_cb.filter(action="check_checks"))
    async def check_pending(callback_query: types.CallbackQuery):
        # Проверка наличия чеков и отправка их администратору
        if callback_query.from_user.id not in ADMINS:
            await callback_query.answer("У вас нет доступа.", show_alert=True)
            return
        if not pending_checks:
            await callback_query.message.answer("На данный момент нет чеков для проверки.")
            return
        for user_id, photo_id in pending_checks.items():
            markup = get_check_keyboard(user_id)
            await dp.bot.send_photo(callback_query.from_user.id, photo_id, caption="Чек на подтверждение", reply_markup=markup)
        await callback_query.answer()

    @dp.callback_query_handler(check_cb.filter(action=['confirm', 'reject']))
    async def process_check_confirmation_or_rejection(callback_query: types.CallbackQuery, callback_data: dict):
        user_id = int(callback_data['user_id'])
        action = callback_data['action']

        if callback_query.from_user.id in ADMINS:
            # Уведомление пользователя о решении администратора
            if action == "confirm":
                await bot.send_message(user_id, "Ваш чек подтвержден. Подписка активирована!")
                await callback_query.answer("Чек подтвержден.", show_alert=True)
            elif action == "reject":
                await bot.send_message(user_id, "Ваш чек был отклонен. Пожалуйста, отправьте корректный чек.")
                await callback_query.answer("Чек отклонен.", show_alert=True)

            # Удаление информации о чеке после обработки
            if user_id in pending_checks:
                del pending_checks[user_id]

            # Ответ администратору об успешной обработке действия
            await callback_query.answer("Операция выполнена.", show_alert=False)
        else:
            # Если кто-то кроме администратора пытается выполнить действие
            await callback_query.answer("У вас нет доступа к этой операции.", show_alert=True)