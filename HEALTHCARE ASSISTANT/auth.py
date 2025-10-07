# auth.py
from database import connect
import hashlib
import customtkinter as ctk
from tkinter import messagebox

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_gui(name, age, sex, username, password):
    conn, cur = connect()
    try:
        cur.execute(
            "INSERT INTO users (name, age, sex, username, password) VALUES (?, ?, ?, ?, ?)",
            (name, age, sex, username, hash_password(password))
        )
        conn.commit()
        messagebox.showinfo("Success", "Registration successful!")
    except Exception as e:
        messagebox.showerror("Error", f"Registration failed: {e}")
    finally:
        conn.close()


def login_gui(username, password):
    conn, cur = connect()
    hashed = hash_password(password)
    try:
        cur.execute("SELECT id, name FROM users WHERE username=? AND password=?", (username, hashed))
        user = cur.fetchone()
        if user:
            return user[0], user[1]  # user_id, name
        else:
            messagebox.showerror("Error", "Invalid Credentials!")
            return None, None
    finally:
        conn.close()
