from aiogram.dispatcher.filters.state import StatesGroup, State

class SubscriptionProcess(StatesGroup):
    ChoosingLevel = State()  # Пользователь выбирает уровень подписки
    WaitingForCheck = State()  # Ожидание прикрепления чека пользователем
    CheckSubmitted = State()  # Пользователь прикрепил чек и выбирает дальнейшее действие
