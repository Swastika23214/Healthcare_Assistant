import sqlite3

def connect():
    conn = sqlite3.connect("health_tracker.db")
    cur = conn.cursor()

    
    # Users table
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            sex TEXT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    
    # Daily vitals table
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vitals(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            sleep_hours REAL,
            bp_systolic INTEGER,
            bp_diastolic INTEGER,
            sugar REAL,
            weight REAL,
            pulse INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

   
    # Medicine table
   
    cur.execute("""
        CREATE TABLE IF NOT EXISTS medicine(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            type TEXT,
            dosage TEXT,
            schedule_type TEXT,
            days TEXT,
            time TEXT,
            paused INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    return conn, cur

