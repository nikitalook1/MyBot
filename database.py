import sqlite3 as sq

def init_db():
    db = sq.connect('tg.db')
    cur = db.cursor()

    # Создание таблицы subscribers, если она еще не существует
    cur.execute('''
    CREATE TABLE IF NOT EXISTS subscribers (
        user_id INTEGER PRIMARY KEY,
        sub_level TEXT DEFAULT NULL,
        is_sub BOOLEAN DEFAULT 0
    );
    ''')

    # Создание таблицы models с добавлением колонки для фото, если она еще не существует
    cur.execute('''
    CREATE TABLE IF NOT EXISTS models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT NOT NULL,
        price REAL NOT NULL,
        photo TEXT  -- Добавлена новая колонка для хранения file_id фотографии
    );
    ''')

    db.commit()
    return db, cur

def update_subscription_status(user_id, is_sub):
    """Обновляет статус подписки пользователя.

    Args:
        user_id (int): Идентификатор пользователя.
        is_sub (bool): Новый статус подписки (True для активной подписки, False для неактивной).
    """
    db = sq.connect('tg.db')  # Подключаемся к базе данных
    cur = db.cursor()  # Создаем курсор

    # Выполняем обновление статуса подписки для пользователя
    cur.execute("UPDATE subscribers SET is_sub = ? WHERE user_id = ?", (is_sub, user_id))
    db.commit()  # Применяем изменения

    db.close()  # Закрываем подключение к базе данных


db, cur = init_db()


#
# def clear_subscribers_table():
#     db = sq.connect('tg.db')  # Подключение к базе данных
#     cur = db.cursor()  # Создаем курсор
#
#     # Удаляем все строки из таблицы subscribers
#     cur.execute("DELETE FROM subscribers")
#     db.commit()  # Применяем изменения
#
#     db.close()  # Закрываем подключение к базе данных
#
# clear_subscribers_table()
