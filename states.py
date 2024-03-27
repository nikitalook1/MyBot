from aiogram.dispatcher.filters.state import StatesGroup, State

class SubscriptionProcess(StatesGroup):
    ChoosingLevel = State()  # Пользователь выбирает уровень подписки
    WaitingForCheck = State()  # Ожидание прикрепления чека пользователем
    CheckSubmitted = State()  # Пользователь прикрепил чек и выбирает дальнейшее действие

class ModelCreation(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_price = State()