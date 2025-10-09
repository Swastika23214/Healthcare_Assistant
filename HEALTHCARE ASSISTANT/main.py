# main.py
import customtkinter as ctk
from auth import login_gui, register_gui
from user_input import vitals_gui, sleep_gui
from medicine import medicine_gui
from nutrition import nutrition_gui
from tkinter import messagebox
import threading
import time
import sqlite3
from plyer import notification
from datetime import datetime


user_id = None
user_name = ""


# Background Reminder Thread

def reminder_loop():
    """Checks every 60s for medicines to remind."""
    while True:
        try:
            conn = sqlite3.connect("health_tracker.db")
            cur = conn.cursor()
            now = datetime.now().strftime("%H:%M")
            cur.execute("SELECT name FROM medicine WHERE time=? AND paused=0", (now,))
            meds = cur.fetchall()
            conn.close()

            for med in meds:
                notification.notify(
                    title="Medicine Reminder",
                    message=f"Time to take {med[0]}",
                    timeout=10
                )
        except Exception as e:
            print("Reminder error:", e)
        time.sleep(60)


# Dashboard after login

def show_dashboard():
    global user_id, user_name

    dash = ctk.CTk()
    dash.geometry("500x550")
    dash.title("Healthcare Assistant - Dashboard")

    ctk.CTkLabel(dash, text=f"Welcome {user_name}!", font=("Arial", 18, "bold")).pack(pady=10)

    # Main buttons
    ctk.CTkButton(dash, text="Enter Daily Vitals", command=lambda: vitals_gui(user_id,user_name)).pack(pady=5)
    ctk.CTkButton(dash, text="Enter Sleep Hours", command=lambda: sleep_gui(user_id,user_name)).pack(pady=5)
    ctk.CTkButton(dash, text="Track Nutrition", command=lambda: nutrition_gui(user_id)).pack(pady=5)
    ctk.CTkButton(dash, text="Medicine Scheduler", command=lambda: medicine_gui()).pack(pady=5)

    # Logout
    def logout():
        global user_id, user_name
        user_id = None
        user_name = ""
        messagebox.showinfo("Logout", "You have been logged out.")
        dash.destroy()
        show_homepage()

    ctk.CTkButton(dash, text="Logout", fg_color="red", command=logout).pack(pady=20)
    dash.mainloop()


# Homepage (Login/Register)

def show_homepage():
    home = ctk.CTk()
    home.geometry("400x500")
    home.title("Healthcare Assistant - Login/Register")

    ctk.CTkLabel(home, text="Register / Login", font=("Arial", 16, "bold")).pack(pady=10)

    ctk.CTkLabel(home, text="Name").pack()
    name_entry = ctk.CTkEntry(home)
    name_entry.pack()

    ctk.CTkLabel(home, text="Age").pack()
    age_entry = ctk.CTkEntry(home)
    age_entry.pack()

    ctk.CTkLabel(home, text="Sex (M/F)").pack()
    sex_entry = ctk.CTkEntry(home)
    sex_entry.pack()

    ctk.CTkLabel(home, text="Username").pack()
    username_entry = ctk.CTkEntry(home)
    username_entry.pack()

    ctk.CTkLabel(home, text="Password").pack()
    password_entry = ctk.CTkEntry(home, show="*")
    password_entry.pack()

    # Register action
    def register_action():
        try:
            register_gui(
                name_entry.get(),
                int(age_entry.get()),
                sex_entry.get(),
                username_entry.get(),
                password_entry.get()
            )
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid age.")

    # Login action
    def login_action():
        global user_id, user_name
        user_id, user_name = login_gui(username_entry.get(), password_entry.get())
        if user_id:
            home.destroy()
            show_dashboard()

    ctk.CTkButton(home, text="Register", command=register_action).pack(pady=10)
    ctk.CTkButton(home, text="Login", command=login_action).pack(pady=10)
    home.mainloop()


# Main Entry

if __name__ == "__main__":
    threading.Thread(target=reminder_loop, daemon=True).start()
    show_homepage()


