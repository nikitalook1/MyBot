import sqlite3 as sq

def init_db():
    db = sq.connect('tg.db')
    cur = db.cursor()

    # Создание таблицы subscribers
    cur.execute('''
    CREATE TABLE IF NOT EXISTS subscribers (
        user_id INTEGER PRIMARY KEY,
        sub_level TEXT DEFAULT NULL,
        is_sub BOOLEAN DEFAULT 0
    );
    ''')

    # Создание таблицы models
    cur.execute('''
    CREATE TABLE IF NOT EXISTS models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT NOT NULL,
        price REAL NOT NULL
    );
    ''')

    db.commit()
    return db, cur

db, cur = init_db()