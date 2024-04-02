from aiogram.dispatcher.filters.state import StatesGroup, State

class SubscriptionProcess(StatesGroup):
    ChoosingLevel = State()  # Пользователь выбирает уровень подписки
    WaitingForCheck = State()  # Ожидание прикрепления чека пользователем
    CheckSubmitted = State()  # Пользователь прикрепил чек и выбирает дальнейшее действие
    WaitingForAmount = State()
    WaitingForDonationCheck = State()

class ModelCreation(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_price = State()
    waiting_for_photo = State()
    waiting_for_support_amount = State()

class DonationProcess(StatesGroup):
    AwaitingDonationAmount = State()  # Ожидание ввода суммы пожертвования