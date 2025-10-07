import datetime
import customtkinter as ctk
from tkinter import messagebox
from database import connect

# Thresholds for basic health advice
NORMAL_BP_SYS = (90, 120)
NORMAL_BP_DIA = (60, 80)
NORMAL_SUGAR = (70, 140)  # mg/dL
NORMAL_WEIGHT = None       # Optional: could be user-specific
NORMAL_PULSE = (60, 100)
NORMAL_SLEEP = (7, 9)     # hours

def vitals_gui(user_id):
    def save_vitals():
        today = datetime.date.today().isoformat()
        try:
            sleep_hours = float(sleep_entry.get())
            bp_systolic = int(bp_sys_entry.get())
            bp_diastolic = int(bp_dia_entry.get())
            sugar = float(sugar_entry.get())
            weight = float(weight_entry.get())
            pulse = int(pulse_entry.get())

            # Open DB connection
            conn, cur = connect()
            cur.execute("SELECT id FROM vitals WHERE user_id=? AND date=?", (user_id, today))
            row = cur.fetchone()
            if row:
                cur.execute("""
                    UPDATE vitals SET sleep_hours=?, bp_systolic=?, bp_diastolic=?, sugar=?, weight=?, pulse=?
                    WHERE id=?
                """, (sleep_hours, bp_systolic, bp_diastolic, sugar, weight, pulse, row[0]))
            else:
                cur.execute("""
                    INSERT INTO vitals(user_id, date, sleep_hours, bp_systolic, bp_diastolic, sugar, weight, pulse)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user_id, today, sleep_hours, bp_systolic, bp_diastolic, sugar, weight, pulse))
            conn.commit()
            conn.close()

            # Generate health feedback
            feedback = []
            if not (NORMAL_BP_SYS[0] <= bp_systolic <= NORMAL_BP_SYS[1]):
                feedback.append(f"Your systolic BP ({bp_systolic}) is {'high' if bp_systolic>NORMAL_BP_SYS[1] else 'low'}.")
            if not (NORMAL_BP_DIA[0] <= bp_diastolic <= NORMAL_BP_DIA[1]):
                feedback.append(f"Your diastolic BP ({bp_diastolic}) is {'high' if bp_diastolic>NORMAL_BP_DIA[1] else 'low'}.")
            if not (NORMAL_SUGAR[0] <= sugar <= NORMAL_SUGAR[1]):
                feedback.append(f"Your blood sugar ({sugar}) is {'high' if sugar>NORMAL_SUGAR[1] else 'low'}.")
            if not (NORMAL_PULSE[0] <= pulse <= NORMAL_PULSE[1]):
                feedback.append(f"Your pulse ({pulse}) is {'high' if pulse>NORMAL_PULSE[1] else 'low'}.")
            if not (NORMAL_SLEEP[0] <= sleep_hours <= NORMAL_SLEEP[1]):
                feedback.append(f"You slept {sleep_hours} hours. Recommended: 7–9 hours.")

            if feedback:
                message = "\n".join(feedback)
            else:
                message = "All your vitals are in the normal range. Great job!"

            # Display feedback in a popup window
            info_win = ctk.CTkToplevel()
            info_win.title("Health Insights")
            info_win.geometry("350x200")
            ctk.CTkLabel(info_win, text=message, wraplength=320, justify="left").pack(padx=10, pady=10)
            ctk.CTkButton(info_win, text="Close", command=lambda: [info_win.destroy(), vitals_win.destroy()]).pack(pady=10)

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers.")
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {e}")

    vitals_win = ctk.CTkToplevel()
    vitals_win.title("Enter Daily Vitals")
    vitals_win.geometry("300x400")

    # Input fields
    ctk.CTkLabel(vitals_win, text="Sleep hours").pack(pady=5)
    sleep_entry = ctk.CTkEntry(vitals_win)
    sleep_entry.pack()
    ctk.CTkLabel(vitals_win, text="BP Systolic").pack(pady=5)
    bp_sys_entry = ctk.CTkEntry(vitals_win)
    bp_sys_entry.pack()
    ctk.CTkLabel(vitals_win, text="BP Diastolic").pack(pady=5)
    bp_dia_entry = ctk.CTkEntry(vitals_win)
    bp_dia_entry.pack()
    ctk.CTkLabel(vitals_win, text="Sugar").pack(pady=5)
    sugar_entry = ctk.CTkEntry(vitals_win)
    sugar_entry.pack()
    ctk.CTkLabel(vitals_win, text="Weight").pack(pady=5)
    weight_entry = ctk.CTkEntry(vitals_win)
    weight_entry.pack()
    ctk.CTkLabel(vitals_win, text="Pulse").pack(pady=5)
    pulse_entry = ctk.CTkEntry(vitals_win)
    pulse_entry.pack()

    ctk.CTkButton(vitals_win, text="Save & Check", command=save_vitals).pack(pady=20)

def sleep_gui(user_id):
    def save_sleep():
        today = datetime.date.today().isoformat()
        try:
            sleep_hours = float(sleep_entry.get())
            conn, cur = connect()
            cur.execute("SELECT id FROM vitals WHERE user_id=? AND date=?", (user_id, today))
            row = cur.fetchone()
            if row:
                cur.execute("UPDATE vitals SET sleep_hours=? WHERE id=?", (sleep_hours, row[0]))
            else:
                cur.execute("INSERT INTO vitals(user_id, date, sleep_hours) VALUES (?, ?, ?)",
                            (user_id, today, sleep_hours))
            conn.commit()
            conn.close()

            # Feedback
            if not (NORMAL_SLEEP[0] <= sleep_hours <= NORMAL_SLEEP[1]):
                message = f"You slept {sleep_hours} hours. Recommended: 7–9 hours."
            else:
                message = f"Your sleep hours ({sleep_hours}) are within the normal range. Good job!"

            info_win = ctk.CTkToplevel()
            info_win.title("Sleep Feedback")
            info_win.geometry("300x150")
            ctk.CTkLabel(info_win, text=message, wraplength=280, justify="left").pack(padx=10, pady=10)
            ctk.CTkButton(info_win, text="Close", command=lambda: [info_win.destroy(), sleep_win.destroy()]).pack(pady=10)

        except ValueError:
            messagebox.showerror("Error", "Enter a valid number.")
        except Exception as e:
            messagebox.showerror("Error", f"Database error: {e}")

    sleep_win = ctk.CTkToplevel()
    sleep_win.title("Enter Sleep Hours")
    sleep_win.geometry("250x150")

    ctk.CTkLabel(sleep_win, text="Sleep hours").pack(pady=5)
    sleep_entry = ctk.CTkEntry(sleep_win)
    sleep_entry.pack()

    ctk.CTkButton(sleep_win, text="Save & Check", command=save_sleep).pack(pady=20)


#nut

import os
import csv
import customtkinter as ctk
from tkinter import messagebox
from database import connect
import datetime

# ----------------------------
# Load and merge multiple CSVs robustly
# ----------------------------
folder_path = "nutrition_data/datasets/"
nutrition_data = {}

def normalize_name(name):
    return name.strip().lower().replace(" ", "_")

def add_nutrients(food, data_dict):
    if food not in nutrition_data:
        nutrition_data[food] = {k: 0 for k in data_dict.keys()}
    for key, val in data_dict.items():
        try:
            nutrition_data[food][key] += float(val)
        except (ValueError, TypeError):
            pass

# Column name normalization map
possible_columns = {
    "food": ["food", "food_item", "item", "name"],
    "calories": ["calories", "calories_(kcal)", "energy"],
    "protein": ["protein", "protein_(g)"],
    "carbohydrates": ["carbohydrates", "carbs", "carbohydrates_(g)"],
    "fat": ["fat", "fat_(g)"],
    "fiber": ["fiber", "fiber_(g)"],
    "vitamins": ["vitamins", "vitamin", "vitamins_(g)", "vitamins_(mg)"]
}

def match_column(headers, possible_names):
    for name in possible_names:
        for h in headers:
            if normalize_name(h) == normalize_name(name):
                return h
    return None

def load_csv(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        if not headers:
            return
        col_map = {}
        for key, possible in possible_columns.items():
            matched = match_column(headers, possible)
            if matched:
                col_map[key] = matched
        for row in reader:
            food = row.get(col_map.get("food", ""), "").strip().lower()
            if not food:
                continue
            data = {}
            for key in possible_columns.keys():
                if key in col_map:
                    data[key] = row.get(col_map[key], 0)
                else:
                    data[key] = 0
            add_nutrients(food, data)

# Read all datasets
if os.path.exists(folder_path):
    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            load_csv(os.path.join(folder_path, file))

# Fallback: daily dataset
daily_csv = "nutrition_data/daily_food_nutrition_dataset.csv"
if os.path.exists(daily_csv):
    load_csv(daily_csv)

# ----------------------------
# Recommended daily intake
# ----------------------------
recommended = {
    "calories": 2000,
    "protein": 50,
    "carbohydrates": 275,
    "fat": 70,
    "vitamins": 1.5
}

# ----------------------------
# Nutrition GUI
# ----------------------------
def nutrition_gui(user_id):
    conn, cur = connect()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS nutrition_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            foods TEXT,
            calories REAL,
            protein REAL,
            carbohydrates REAL,
            fat REAL,
            vitamins REAL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

    def calculate():
        foods = food_entry.get().strip()
        if not foods:
            messagebox.showerror("Error", "Enter food items.")
            return

        food_list = [f.strip().lower() for f in foods.split(",") if f.strip()]
        totals = {k: 0 for k in recommended.keys()}
        missing = []

        for food in food_list:
            if food in nutrition_data:
                for k in recommended.keys():
                    totals[k] += float(nutrition_data[food].get(k, 0))
            else:
                missing.append(food)

        def diff_message(k):
            diff = totals[k] - recommended[k]
            if diff > 0:
                return f"{k.capitalize()}: {diff:.1f} more than recommended."
            elif diff < 0:
                return f"{k.capitalize()}: {abs(diff):.1f} less than recommended."
            else:
                return f"{k.capitalize()}: Perfect intake!"

        msg = (
            f"Total Calories: {totals['calories']:.1f} kcal\n"
            f"Protein: {totals['protein']:.1f} g\n"
            f"Carbohydrates: {totals['carbohydrates']:.1f} g\n"
            f"Fat: {totals['fat']:.1f} g\n"
            f"Vitamins: {totals['vitamins']:.2f} g\n\n"
            "⚖️ Comparison with Recommended Intake:\n" +
            "\n".join([diff_message(k) for k in recommended.keys()])
        )

        if missing:
            msg += "\n\n⚠️ Not found in database: " + ", ".join(missing)

        conn, cur = connect()
        today = datetime.date.today().isoformat()
        cur.execute("""
            INSERT INTO nutrition_log(user_id, date, foods, calories, protein, carbohydrates, fat, vitamins)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, today, ", ".join(food_list),
              totals["calories"], totals["protein"], totals["carbohydrates"],
              totals["fat"], totals["vitamins"]))
        conn.commit()
        conn.close()

        result = ctk.CTkToplevel()
        result.title("Nutrition Summary")
        result.geometry("450x380")
        ctk.CTkLabel(result, text=msg, wraplength=420, justify="left", font=("Arial", 12)).pack(padx=10, pady=10)
        ctk.CTkButton(result, text="Close", command=result.destroy).pack(pady=10)

    win = ctk.CTkToplevel()
    win.title("Nutrition Tracker")
    win.geometry("480x300")
    ctk.CTkLabel(win, text="Enter food items eaten today (comma separated)", font=("Arial", 14)).pack(pady=10)
    food_entry = ctk.CTkEntry(win, width=350, font=("Arial", 13))
    food_entry.pack(pady=5)
    ctk.CTkButton(win, text="Calculate & Save", command=calculate).pack(pady=10)
