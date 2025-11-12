import customtkinter as ctk
from tkinter import messagebox
import sqlite3
from datetime import datetime


# Database helper

def connect():
    conn = sqlite3.connect("health_tracker.db")
    cur = conn.cursor()
    return conn, cur



# VITALS GUI

def vitals_gui(user_id, user_name):
    window = ctk.CTkToplevel()
    window.title("Daily Vitals Tracker")
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    window.geometry(f"{screen_width}x{screen_height}")

    ctk.CTkLabel(window, text=f"Hello {user_name} ", font=("Arial", 18, "bold")).pack(pady=10)
    ctk.CTkLabel(window, text="Enter your vitals below:", font=("Arial", 14)).pack(pady=5)

    # --- Input fields ---
    bp_sys = ctk.CTkEntry(window, placeholder_text="BP Systolic (e.g., 120)")
    bp_dia = ctk.CTkEntry(window, placeholder_text="BP Diastolic (e.g., 80)")
    sugar = ctk.CTkEntry(window, placeholder_text="Blood Sugar (mg/dL)")
    weight = ctk.CTkEntry(window, placeholder_text="Weight (kg)")
    pulse = ctk.CTkEntry(window, placeholder_text="Pulse (bpm)")

    for entry in [bp_sys, bp_dia, sugar, weight, pulse]:
        entry.pack(pady=6, padx=20, fill="x")

  
    # Save and analyze vitals
    
    def save_vitals():
        try:
            systolic = int(bp_sys.get())
            diastolic = int(bp_dia.get())
            sugar_val = float(sugar.get())
            weight_val = float(weight.get())
            pulse_val = int(pulse.get())
            date = datetime.now().strftime("%Y-%m-%d")

            conn, cur = connect()
            cur.execute("""
                INSERT INTO vitals (user_id, date, bp_systolic, bp_diastolic, sugar, weight, pulse)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, date, systolic, diastolic, sugar_val, weight_val, pulse_val))
            conn.commit()
            conn.close()

            feedback = []

            # --- Blood Pressure ---
            if systolic > 130 or diastolic > 85:
                feedback.append(" Your blood pressure is higher than normal.")
            elif systolic < 90 or diastolic < 60:
                feedback.append(" Your blood pressure is lower than normal.")
            else:
                feedback.append("✅ Your blood pressure is normal.")

            # --- Sugar ---
            if sugar_val > 140:
                feedback.append(" High blood sugar detected. Limit sugary foods.")
            elif sugar_val < 70:
                feedback.append(" Low sugar detected. Eat something sweet.")
            else:
                feedback.append("✅ Blood sugar level is normal.")

            # --- Pulse ---
            if pulse_val > 100:
                feedback.append(" High pulse rate. Rest and hydrate.")
            elif pulse_val < 60:
                feedback.append(" Low pulse rate. Consult doctor if dizzy.")
            else:
                feedback.append("✅ Pulse rate is normal.")

            # --- Weight ---
            feedback.append(f" Your weight: {weight_val} kg. Monitor weekly for changes.")

            # --- Summary ---
            good = sum(1 for f in feedback if "✅" in f)
            if good == 4:
                feedback.append("\n Excellent! All your vitals look good.")
            elif good >= 2:
                feedback.append("\n You’re mostly fine, just watch out for warnings above.")
            else:
                feedback.append("\n Multiple vitals are out of range. Please monitor regularly.")

            show_feedback("Vitals Summary", feedback)

        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values in all fields.")

    
    # Show feedback window
    
    def show_feedback(title, messages):
        fb = ctk.CTkToplevel(window)
        fb.title(title)
        fb.geometry("360x420")
        ctk.CTkLabel(fb, text="🩺 Vitals Analysis", font=("Arial", 18, "bold")).pack(pady=10)
        for msg in messages:
            ctk.CTkLabel(fb, text=msg, wraplength=320, justify="left").pack(pady=4, padx=10)
        ctk.CTkButton(fb, text="Close", command=fb.destroy).pack(pady=15)

    ctk.CTkButton(window, text="Save & Analyze", command=save_vitals).pack(pady=20)
    ctk.CTkButton(window, text="Close", command=window.destroy).pack(pady=10)



# SLEEP GUI

def sleep_gui(user_id, user_name):
    sleep_win = ctk.CTkToplevel()
    sleep_win.title("Sleep Tracker")
    sleep_win.geometry("300x300")

    ctk.CTkLabel(sleep_win, text=f"Sleep Tracker for {user_name}", font=("Arial", 16, "bold")).pack(pady=10)
    ctk.CTkLabel(sleep_win, text="Enter sleep hours (e.g., 7.5):").pack(pady=5)
    sleep_entry = ctk.CTkEntry(sleep_win)
    sleep_entry.pack(pady=5)

    def save_sleep():
        try:
            sleep_hours = float(sleep_entry.get())
            today = datetime.now().strftime("%Y-%m-%d")

            conn, cur = connect()
            cur.execute("SELECT id FROM vitals WHERE user_id=? AND date=?", (user_id, today))
            row = cur.fetchone()
            if row:
                cur.execute("UPDATE vitals SET sleep_hours=? WHERE id=?", (sleep_hours, row[0]))
            else:
                cur.execute("INSERT INTO vitals (user_id, date, sleep_hours) VALUES (?, ?, ?)",
                            (user_id, today, sleep_hours))
            conn.commit()
            conn.close()

            feedback = []
            if sleep_hours < 7:
                feedback.append(" You should try to sleep at least 7 hours.")
            elif sleep_hours > 9:
                feedback.append(" You might be oversleeping. 7–8 hours is ideal.")
            else:
                feedback.append("✅ You’re getting good quality sleep.")

            show_feedback("Sleep Summary", feedback)

        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number.")

    def show_feedback(title, messages):
        fb = ctk.CTkToplevel(sleep_win)
        fb.title(title)
        fb.geometry("300x200")
        for msg in messages:
            ctk.CTkLabel(fb, text=msg, wraplength=280, justify="left").pack(pady=8)
        ctk.CTkButton(fb, text="Close", command=fb.destroy).pack(pady=10)

    ctk.CTkButton(sleep_win, text="Save & Analyze", command=save_sleep).pack(pady=15)
    ctk.CTkButton(sleep_win, text="Close", command=sleep_win.destroy).pack(pady=5)


