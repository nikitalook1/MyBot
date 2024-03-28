from aiogram.dispatcher.filters.state import StatesGroup, State

class SubscriptionProcess(StatesGroup):
    ChoosingLevel = State()  # Пользователь выбирает уровень подписки
    WaitingForCheck = State()  # Ожидание прикрепления чека пользователем
    CheckSubmitted = State()  # Пользователь прикрепил чек и выбирает дальнейшее действие

class ModelCreation(StatesGroup):
    waiting_for_nickname = State()  # Уже существующее состояние для никнейма
    waiting_for_price = State()     # Уже существующее состояние для цены
    waiting_for_photo = State()     # Новое состояние для фотографии
