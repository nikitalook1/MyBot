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

db, cur = init_db()
