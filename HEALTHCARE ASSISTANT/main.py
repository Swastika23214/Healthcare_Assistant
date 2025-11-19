# main.py
import customtkinter as ctk
from auth import login_gui, register_gui
from user_input import vitals_gui, sleep_gui
from medicine import medicine_gui
from nutrition import nutrition_gui
from symptom_checker import symptom_checker_gui
from report_generation import report_generation_gui  
from tkinter import messagebox
import threading
import time
import sqlite3
import plyer
from datetime import datetime


user_id = None
user_name = ""


def reminder_loop():
    """Checks every 60s for medicines to remind."""
    while True:
        try:
            conn = sqlite3.connect("health_tracker.db")
            cur = conn.cursor()
            now = datetime.now().strftime("%H:%M")
            # Get medicines for all users (or filter by logged-in user if you want)
            cur.execute("SELECT name FROM medicine WHERE time=? AND paused=0", (now,))
            meds = cur.fetchall()
            conn.close()

            for med in meds:
                plyer.notification.notify(
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
    screen_width = dash.winfo_screenwidth()
    screen_height = dash.winfo_screenheight()
    dash.geometry(f"{screen_width}x{screen_height}")
    dash.title("Healthcare Assistant - Dashboard")

    # Header with improved styling
    header_frame = ctk.CTkFrame(dash, fg_color="transparent")
    header_frame.pack(pady=15)
    
    ctk.CTkLabel(
        header_frame, 
        text=f"Welcome back, {user_name}!", 
        font=("Arial", 22, "bold")
    ).pack()
    
    ctk.CTkLabel(
        header_frame, 
        text="Your Personal Healthcare Dashboard", 
        font=("Arial", 12),
        text_color="gray"
    ).pack()

    # Main buttons frame
    button_frame = ctk.CTkFrame(dash, fg_color="transparent")
    button_frame.pack(pady=10, padx=20, fill="both", expand=True)

    # Button styling helper
    button_config = {
        "width": 400,
        "height": 45,
        "font": ("Arial", 14),
        "corner_radius": 10
    }

    # Main feature buttons
    ctk.CTkButton(
        button_frame, 
        text="🩺 Enter Daily Vitals", 
        command=lambda: vitals_gui(user_id, user_name),
        **button_config
    ).pack(pady=8)
    
    ctk.CTkButton(
        button_frame, 
        text=" Enter Sleep Hours", 
        command=lambda: sleep_gui(user_id, user_name),
        **button_config
    ).pack(pady=8)
    
    ctk.CTkButton(
        button_frame, 
        text=" Track Nutrition", 
        command=lambda: nutrition_gui(user_id),
        **button_config
    ).pack(pady=8)
    
    ctk.CTkButton(
    button_frame, 
    text=" Medicine Scheduler", 
    command=lambda: medicine_gui(user_id),  # Pass user_id here
    **button_config
    ).pack(pady=8)

    # Symptom Checker Button
    ctk.CTkButton(
        button_frame, 
        text="🔍 Symptom Checker", 
        command=lambda: symptom_checker_gui(user_id),
        **button_config
    ).pack(pady=8)
    
    # NEW REPORT GENERATION BUTTON
    ctk.CTkButton(
        button_frame, 
        text=" Generate Health Report", 
        command=lambda: report_generation_gui(user_id, user_name),
        **button_config
    ).pack(pady=8)

    # Logout button
    def logout():
        global user_id, user_name
        user_id = None
        user_name = ""
        messagebox.showinfo("Logout", "You have been logged out successfully.")
        dash.destroy()
        show_homepage()

    ctk.CTkButton(
        button_frame, 
        text=" Logout", 
        fg_color="#E74C3C",
        hover_color="#C0392B",
        command=logout,
        width=200,
        height=40
    ).pack(pady=20)
    
    dash.mainloop()


# Homepage (Login/Register)

def show_homepage():
    home = ctk.CTk()
    screen_width = home.winfo_screenwidth()
    screen_height = home.winfo_screenheight()
    home.geometry(f"{screen_width}x{screen_height}")

    home.title("Healthcare Assistant - Login/Register")

    # Header
    ctk.CTkLabel(
        home, 
        text="🏥 Healthcare Assistant", 
        font=("Arial", 24, "bold")
    ).pack(pady=15)
    
    ctk.CTkLabel(
        home, 
        text="Register / Login to Continue", 
        font=("Arial", 14)
    ).pack(pady=5)

    # Input frame
    input_frame = ctk.CTkFrame(home, fg_color="transparent")
    input_frame.pack(pady=10, padx=30)

    ctk.CTkLabel(input_frame, text="Name", font=("Arial", 12)).pack(pady=3, anchor="w")
    name_entry = ctk.CTkEntry(input_frame, width=350, height=35)
    name_entry.pack(pady=5)

    ctk.CTkLabel(input_frame, text="Age", font=("Arial", 12)).pack(pady=3, anchor="w")
    age_entry = ctk.CTkEntry(input_frame, width=350, height=35)
    age_entry.pack(pady=5)

    ctk.CTkLabel(input_frame, text="Sex (M/F)", font=("Arial", 12)).pack(pady=3, anchor="w")
    sex_entry = ctk.CTkEntry(input_frame, width=350, height=35)
    sex_entry.pack(pady=5)

    ctk.CTkLabel(input_frame, text="Username", font=("Arial", 12)).pack(pady=3, anchor="w")
    username_entry = ctk.CTkEntry(input_frame, width=350, height=35)
    username_entry.pack(pady=5)

    ctk.CTkLabel(input_frame, text="Password", font=("Arial", 12)).pack(pady=3, anchor="w")
    password_entry = ctk.CTkEntry(input_frame, width=350, height=35, show="*")
    password_entry.pack(pady=5)

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

    # Buttons
    button_frame = ctk.CTkFrame(home, fg_color="transparent")
    button_frame.pack(pady=15)
    
    ctk.CTkButton(
        button_frame, 
        text="Register", 
        command=register_action,
        width=150,
        height=40,
        font=("Arial", 13, "bold")
    ).pack(pady=8)
    
    ctk.CTkButton(
        button_frame, 
        text="Login", 
        command=login_action,
        width=150,
        height=40,
        font=("Arial", 13, "bold"),
        fg_color="#27AE60",
        hover_color="#229954"
    ).pack(pady=8)
    
    home.mainloop()


# Main Entry

if __name__ == "__main__":
    threading.Thread(target=reminder_loop, daemon=True).start()
    show_homepage()
