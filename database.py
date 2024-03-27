import sqlite3 as sq

def init_db():
    db = sq.connect('tg.db')
    cur = db.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS subscribers (
        user_id INTEGER PRIMARY KEY,
        sub_level TEXT DEFAULT NULL,
        is_sub BOOLEAN DEFAULT 0
    )
    ''')

    db.commit()
    return db, cur

db, cur = init_db()
