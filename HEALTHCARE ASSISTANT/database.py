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

   
# Medicine table with notes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS medicine(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            days TEXT,
            time TEXT,
            notes TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    
    # Symptom table
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS symptom_checks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            symptoms TEXT,
            top_diseases TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    return conn, cur


def save_symptom_check(user_id, symptoms, top_diseases):
    """Save symptom check to database"""
    try:
        from datetime import datetime
        conn, cur = connect()
        
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        symptoms_str = ", ".join(symptoms)
        diseases_str = "; ".join([f"{d[0]} ({d[1]:.0f}%)" for d in top_diseases[:3]])
        
        cur.execute("""
            INSERT INTO symptom_checks(user_id, date, symptoms, top_diseases)
            VALUES (?, ?, ?, ?)
        """, (user_id, date, symptoms_str, diseases_str))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving symptom check: {e}")
        return False


def get_symptom_history(user_id, limit=20):
    """Get symptom check history for a user"""
    try:
        conn, cur = connect()
        cur.execute("""
            SELECT date, symptoms, top_diseases 
            FROM symptom_checks 
            WHERE user_id=? 
            ORDER BY date DESC 
            LIMIT ?
        """, (user_id, limit))
        
        records = cur.fetchall()
        conn.close()
        return records
    except Exception as e:
        print(f"Error fetching symptom history: {e}")
        return []
