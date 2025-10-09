import os
import csv
import customtkinter as ctk
from tkinter import messagebox
from database import connect
import datetime


# Load and merge CSVs 

folder_path = "nutrition_data/datasets/"
nutrition_data = {}

def normalize_name(name):
    return name.strip().lower().replace(" ", "_")

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
            food_raw = row.get(col_map.get("food", ""), "").strip()
            if not food_raw:
                continue
            food = normalize_name(food_raw)
            if food in nutrition_data:
                continue  # Skip duplicates
            data = {}
            for k in possible_columns.keys():
                val = row.get(col_map.get(k, ""), "0").replace(",", "").strip()
                try:
                    val_float = float(val)
                    # Convert vitamins from mg to g if > 10
                    if k == "vitamins" and val_float > 10:
                        val_float /= 1000
                    data[k] = val_float
                except (ValueError, TypeError):
                    data[k] = 0
            nutrition_data[food] = data

# Read all dataset CSVs
if os.path.exists(folder_path):
    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            load_csv(os.path.join(folder_path, file))

# Fallback: daily dataset
daily_csv = "nutrition_data/daily_food_nutrition_dataset.csv"
if os.path.exists(daily_csv):
    load_csv(daily_csv)


# Recommended daily intake

recommended = {
    "calories": 2000,
    "protein": 50,
    "carbohydrates": 275,
    "fat": 70,
    "vitamins": 1.5  # grams
}


# Nutrition GUI

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

        food_list = [normalize_name(f) for f in foods.split(",") if f.strip()]
        totals = {k: 0 for k in recommended.keys()}
        missing = []

        for food in food_list:
            if food in nutrition_data:
                for k in recommended.keys():
                    totals[k] += nutrition_data[food].get(k, 0)
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
            msg += "\n\n Not found in database: " + ", ".join(missing)

        # Save to database
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

        # Show result
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

