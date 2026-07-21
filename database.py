import sqlite3

def create_database():

    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT UNIQUE,

        password TEXT

    )
    """)

    # Interview History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interviews(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        username TEXT,

        domain TEXT,

        score REAL,

        interview_date TEXT

    )
    """)

    conn.commit()
    conn.close()

create_database()