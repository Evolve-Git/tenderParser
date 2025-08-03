import sqlite3

def init_db(db_path):
    with sqlite3.connect(db_path) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tenders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT,
                categories TEXT,
                title TEXT,
                organizer TEXT,
                end_date TEXT,
                positions TEXT,
                url TEXT
            )
        ''')

def save_to_sqlite(tenders, db_path):
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany('''
            INSERT INTO tenders (number, categories, title, organizer, end_date, positions, url)
            VALUES (:number, :categories, :title, :organizer, :end_date, :positions, :url)
        ''', tenders)