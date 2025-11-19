import os
import csv
import customtkinter as ctk
from tkinter import messagebox, scrolledtext
from database import connect
import datetime
import re
import json
import traceback

# Load and merge CSVs 
folder_path = "nutrition_data/datasets/"
nutrition_data = {}
food_list = []  # Store list of available foods for search functionality

def normalize_name(name):
    """Normalize food names for consistent matching"""
    return name.strip().lower().replace(" ", "_").replace("-", "_")

def clean_numeric_value(value):
    """Clean and convert numeric values from CSV data"""
    if not value or value.strip() == "":
        return 0
    
    # Remove any non-numeric characters except decimal point
    cleaned = re.sub(r'[^\d.]', '', str(value))
    
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return 0

# Column name normalization map - expanded to handle more variations
#Dish Name,Calories (kcal),Carbohydrates (g),Protein (g),Fats (g),Free Sugar (g),Fibre (g),Sodium (mg),Calcium (mg),Iron (mg),Vitamin C (mg),Folate (µg)

possible_columns = {
    "food": ["food", "food_name", "Food", "Dish_Name", "Item"],
    "calories": ["calories", "Calories", "Calories (kcal)", "energy_kcal"],
    "protein": ["protein", "Protein", "Protein (g)", "protein_g"],
    "carbohydrates": ["carbohydrates", "Carbohydrates", "Carbohydrates (g)", "carb_g"],
    "fat": ["fat", "Fat", "Fats (g)", "fat_g"],
    "fiber": ["fiber", "Fibre", "Fibre (g)", "fibre_g"],
    "sugar": ["sugar", "Free_Sugar (g)", "freesugar_g"],
    "sodium": ["sodium", "Sodium (mg)", "sodium_mg"],
     "folate": ["Folate (ug)", "Folate (µg)"],
}



def match_column(headers, possible_names):
    """Match column names in CSV to our standard names"""
    for name in possible_names:
        for h in headers:
            if normalize_name(h) == normalize_name(name):
                return h
    return None

def load_csv(file_path):
    """Load nutrition data from a CSV file with data cleaning"""
    try:
        print(f"Loading {file_path}...")
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            if not headers:
                print(f"No headers found in {file_path}")
                return
            
            col_map = {}
            for key, possible in possible_columns.items():
                matched = match_column(headers, possible)
                if matched:
                    col_map[key] = matched
            
            print(f"Column mapping: {col_map}")
            
            count = 0
            for row in reader:
                food_raw = row.get(col_map.get("food", ""), "").strip()
                if not food_raw:
                    continue
                
                food = normalize_name(food_raw)
                
                # Skip if we already have this food (first dataset takes precedence)
                if food in nutrition_data:
                    continue
                
                data = {}
                for k in possible_columns.keys():
                    val = row.get(col_map.get(k, ""), "0")
                    data[k] = clean_numeric_value(val)
                
                nutrition_data[food] = data
                food_list.append(food_raw)  # Keep original name for display
                count += 1
                
        print(f"Loaded {count} food items from {os.path.basename(file_path)}")
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        traceback.print_exc()

# Load all datasets
if os.path.exists(folder_path):
    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            load_csv(os.path.join(folder_path, file))
else:
    print(f"Folder {folder_path} does not exist!")

# Save the loaded data to a cache file for faster loading next time
try:
    os.makedirs("nutrition_data", exist_ok=True)
    with open("nutrition_data/cache.json", "w") as f:
        json.dump(nutrition_data, f)
    print(f"Saved {len(nutrition_data)} food items to cache")
except Exception as e:
    print(f"Error saving cache: {e}")
    traceback.print_exc()

# Recommended daily intake based on average adult
recommended = {
    "calories": 2000,
    "protein": 50,
    "carbohydrates": 275,
    "fat": 70,
    "fiber": 25,
    "vitamins": 1.5,  # grams
    "sugar": 50,
    "sodium": 2.3,  # grams
    "cholesterol": 0.3  # grams
}

def convert_to_grams(quantity, unit):
    """Convert quantity and unit to grams"""
    if unit in ['g', 'gram', 'grams']:
        return quantity
    elif unit in ['kg', 'kilogram', 'kilograms']:
        return quantity * 1000
    elif unit in ['mg', 'milligram', 'milligrams']:
        return quantity / 1000
    elif unit in ['oz', 'ounce', 'ounces']:
        return quantity * 28.35
    elif unit in ['lb', 'pound', 'pounds']:
        return quantity * 453.592
    elif unit in ['cup', 'cups']:
        # Approximate conversion: 1 cup ≈ 240g for most foods
        return quantity * 240
    elif unit in ['tbsp', 'tablespoon', 'tablespoons']:
        # Approximate conversion: 1 tbsp ≈ 15g
        return quantity * 15
    elif unit in ['tsp', 'teaspoon', 'teaspoons']:
        # Approximate conversion: 1 tsp ≈ 5g
        return quantity * 5
    elif unit in ['medium', 'large', 'small']:
        # These are rough estimates for fruits
        if unit == 'small':
            return 100  # Small fruit ≈ 100g
        elif unit == 'medium':
            return 150  # Medium fruit ≈ 150g
        else:  # large
            return 200  # Large fruit ≈ 200g
    elif unit in ['slice', 'slices']:
        # Approximate conversion: 1 slice ≈ 30g for bread
        return quantity * 30
    elif unit in ['piece', 'pieces']:
        # Approximate conversion: 1 piece ≈ 50g
        return quantity * 50
    else:
        # Unknown unit, assume grams
        return quantity

def find_similar_foods(search_term, limit=10):
    """Find foods similar to the search term"""
    search_term = normalize_name(search_term)
    matches = []
    
    for food in nutrition_data:
        if search_term in food:
            matches.append(food)
    
    # Sort by similarity (how much of the search term is in the food name)
    matches.sort(key=lambda x: x.count(search_term), reverse=True)
    
    return matches[:limit]

def setup_database():
    """Setup or update the database table as needed"""
    try:
        conn, cur = connect()
        
        # Check if table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nutrition_log'")
        table_exists = cur.fetchone() is not None
        
        if table_exists:
            # Check if quantities column exists
            cur.execute("PRAGMA table_info(nutrition_log)")
            columns = [column[1] for column in cur.fetchall()]
            
            if "quantities" not in columns:
                print("Adding missing 'quantities' column to nutrition_log table")
                cur.execute("ALTER TABLE nutrition_log ADD COLUMN quantities TEXT")
                conn.commit()
            
            # Check if other required columns exist
            required_columns = ["fiber", "vitamins", "sugar", "sodium", "cholesterol"]
            for column in required_columns:
                if column not in columns:
                    print(f"Adding missing '{column}' column to nutrition_log table")
                    cur.execute(f"ALTER TABLE nutrition_log ADD COLUMN {column} REAL")
                    conn.commit()
        else:
            # Create the table with all required columns
            print("Creating nutrition_log table")
            cur.execute("""
                CREATE TABLE nutrition_log(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    date TEXT,
                    foods TEXT,
                    quantities TEXT,
                    calories REAL,
                    protein REAL,
                    carbohydrates REAL,
                    fat REAL,
                    fiber REAL,
                    vitamins REAL,
                    sugar REAL,
                    sodium REAL,
                    cholesterol REAL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            conn.commit()
        
        conn.close()
        print("Database table setup completed successfully")
        return True
    except Exception as e:
        print(f"Error setting up database: {e}")
        traceback.print_exc()
        return False

def nutrition_gui(user_id):
    print(f"Opening nutrition GUI for user {user_id}")
    print(f"Loaded {len(nutrition_data)} food items")
    
    # Setup or update database
    if not setup_database():
        messagebox.showerror("Database Error", "Failed to setup database table")
        return

    # Create the main window
    win = ctk.CTkToplevel()
    win.title("Nutrition Tracker")
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()
    win.geometry(f"{screen_width}x{screen_height}")

    
    # Store selected foods with their quantities
    selected_foods = []
    
    # Title
    ctk.CTkLabel(win, text="Nutrition Tracker", font=("Arial", 18, "bold")).pack(pady=10)
    
    # Create a frame for food selection
    food_frame = ctk.CTkFrame(win)
    food_frame.pack(fill="x", padx=20, pady=10)
    
    # Food search with autocomplete
    ctk.CTkLabel(food_frame, text="Search Food:", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
    
    # Single search/dropdown combo
    food_dropdown = ctk.CTkComboBox(food_frame, width=400)
    food_dropdown.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
    
    # Update dropdown when typing
    def update_search(event=None):
        search_term = food_dropdown.get()
        if search_term and len(search_term) >= 2:  # Start searching after 2 characters
            matches = find_similar_foods(search_term, limit=15)
            food_options = [food.replace("_", " ").title() for food in matches]
            food_dropdown.configure(values=food_options)
        else:
            food_dropdown.configure(values=[])
    
    # Bind to dropdown entry
    food_dropdown.bind("<KeyRelease>", update_search)
    
    # Quantity input
    ctk.CTkLabel(food_frame, text="Quantity:", font=("Arial", 12)).grid(row=1, column=0, padx=5, pady=5, sticky="w")
    quantity_entry = ctk.CTkEntry(food_frame, width=100)
    quantity_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    
    # Unit dropdown
    unit_dropdown = ctk.CTkComboBox(food_frame, values=["g", "kg", "mg", "oz", "lb", "cup", "cups", "tbsp", "tsp", "medium", "large", "small", "slice", "slices", "piece", "pieces"], width=100)
    unit_dropdown.set("g")
    unit_dropdown.grid(row=1, column=2, padx=5, pady=5, sticky="w")
    
    # Add food button
    def add_food():
        food_name = food_dropdown.get()
        quantity_str = quantity_entry.get()
        unit = unit_dropdown.get()
        
        if not food_name:
            messagebox.showerror("Error", "Please select a food.")
            return
        
        if not quantity_str:
            messagebox.showerror("Error", "Please enter a quantity.")
            return
        
        try:
            quantity = float(quantity_str)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity.")
            return
        
        # Convert to normalized name for database lookup
        food_normalized = normalize_name(food_name)
        
        # Check if food exists in database
        if food_normalized not in nutrition_data:
            messagebox.showerror("Error", f"Food '{food_name}' not found in database.")
            return
        
        # Add to selected foods list
        selected_foods.append((food_name, food_normalized, quantity, unit))
        
        # Update the list
        update_food_list()
        
        # Clear inputs
        food_dropdown.set("")
        quantity_entry.delete(0, "end")
    
    # Create a frame for the selected foods list
    list_frame = ctk.CTkFrame(win)
    list_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    ctk.CTkLabel(list_frame, text="Selected Foods:", font=("Arial", 14, "bold")).pack(pady=5)
    
    # Scrollable frame for selected foods
    foods_scroll = ctk.CTkScrollableFrame(list_frame, height=200)
    foods_scroll.pack(fill="both", expand=True, padx=10, pady=5)
    
    def update_food_list():
        # Clear the current list
        for widget in foods_scroll.winfo_children():
            widget.destroy()
        
        # Add each food to the list
        for i, (food_name, food_normalized, quantity, unit) in enumerate(selected_foods):
            food_item_frame = ctk.CTkFrame(foods_scroll)
            food_item_frame.pack(fill="x", pady=5)
            
            # Food name and quantity
            ctk.CTkLabel(food_item_frame, text=f"{food_name}: {quantity} {unit}").pack(side="left", padx=10)
            
            # Remove button
            ctk.CTkButton(food_item_frame, text="Remove", width=80, 
                          command=lambda idx=i: remove_food(idx)).pack(side="right", padx=10)
    
    def remove_food(index):
        del selected_foods[index]
        update_food_list()
    
    # Add food button
    ctk.CTkButton(food_frame, text="Add Food", command=add_food, width=100).grid(row=2, column=1, padx=5, pady=10)
    
    # Calculate function with extensive debugging
    def calculate():
        print("Calculate button clicked")
        try:
            if not selected_foods:
                messagebox.showerror("Error", "Please add at least one food.")
                return
            
            print(f"Processing {len(selected_foods)} foods")
            totals = {k: 0 for k in recommended.keys()}
            food_list_display = []
            quantity_list = []

            for food_name, food_normalized, quantity, unit in selected_foods:
                print(f"Processing {food_name} ({food_normalized})")
                food_list_display.append(food_name)
                
                # Convert quantity to grams
                quantity_grams = convert_to_grams(quantity, unit)
                quantity_list.append(f"{quantity} {unit} ({quantity_grams:.1f}g)")
                
                # Get nutrition data for this food
                food_nutrition = nutrition_data.get(food_normalized, {})
                print(f"Nutrition data for {food_name}: {food_nutrition}")
                
                # Calculate nutrition based on quantity
                # Base data is per 100g
                factor = quantity_grams / 100.0
                print(f"Factor for {food_name}: {factor}")
                
                for k in recommended.keys():
                    value = food_nutrition.get(k, 0) * factor
                    totals[k] += value
                    print(f"Added {value} {k} from {food_name}, total now {totals[k]}")

            print(f"Final totals: {totals}")

            def diff_message(k):
                diff = totals[k] - recommended[k]
                pct = (totals[k] / recommended[k]) * 100 if recommended[k] > 0 else 0
                if diff > 0:
                    return f"{k.capitalize()}: {diff:.1f} more than recommended ({pct:.0f}% of daily value)."
                elif diff < 0:
                    return f"{k.capitalize()}: {abs(diff):.1f} less than recommended ({pct:.0f}% of daily value)."
                else:
                    return f"{k.capitalize()}: Perfect intake!"

            # Format food items with quantities for display
            food_display = ", ".join([f"{name} ({qty})" for name, qty in zip(food_list_display, quantity_list)])
            
            msg = (
                f"Total Calories: {totals['calories']:.1f} kcal ({(totals['calories']/recommended['calories']*100):.0f}% of daily value)\n"
                f"Protein: {totals['protein']:.1f} g ({(totals['protein']/recommended['protein']*100):.0f}% of daily value)\n"
                f"Carbohydrates: {totals['carbohydrates']:.1f} g ({(totals['carbohydrates']/recommended['carbohydrates']*100):.0f}% of daily value)\n"
                f"Fat: {totals['fat']:.1f} g ({(totals['fat']/recommended['fat']*100):.0f}% of daily value)\n"
                f"Fiber: {totals['fiber']:.1f} g ({(totals['fiber']/recommended['fiber']*100):.0f}% of daily value)\n"
                f"Vitamins: {totals['vitamins']:.2f} g ({(totals['vitamins']/recommended['vitamins']*100):.0f}% of daily value)\n"
                f"Sugar: {totals['sugar']:.1f} g ({(totals['sugar']/recommended['sugar']*100):.0f}% of daily value)\n"
                f"Sodium: {totals['sodium']:.1f} g ({(totals['sodium']/recommended['sodium']*100):.0f}% of daily value)\n"
                f"Cholesterol: {totals['cholesterol']:.2f} g ({(totals['cholesterol']/recommended['cholesterol']*100):.0f}% of daily value)\n\n"
                "⚖️ Comparison with Recommended Intake:\n" +
                "\n".join([diff_message(k) for k in recommended.keys()])
            )

            
            # Show result
            result = ctk.CTkToplevel()
            result.title("Nutrition Summary")
            screen_width = result.winfo_screenwidth()
            screen_height = result.winfo_screenheight()
            result.geometry(f"{screen_width}x{screen_height}")

            
            # Create a scrollable frame for the content
            scroll_frame = ctk.CTkScrollableFrame(result, width=520, height=500)
            scroll_frame.pack(padx=10, pady=10, fill="both", expand=True)
            
            # Display nutrition summary
            ctk.CTkLabel(scroll_frame, text=msg, wraplength=500, justify="left", font=("Arial", 12)).pack(padx=10, pady=10)
            
            ctk.CTkButton(result, text="Close", command=result.destroy).pack(pady=10)
            
        except Exception as e:
            print(f"Error in calculate function: {e}")
            traceback.print_exc()
            messagebox.showerror("Calculation Error", f"An error occurred during calculation: {e}")
    
    # Clear all button
    def clear_all():
        selected_foods.clear()
        update_food_list()
    
    # Buttons frame
    buttons_frame = ctk.CTkFrame(win)
    buttons_frame.pack(fill="x", padx=20, pady=10)
    
    ctk.CTkButton(buttons_frame, text="Calculate & Save", command=calculate, width=150, height=40, 
                  font=("Arial", 14, "bold")).pack(side="left", padx=10)
    
    ctk.CTkButton(buttons_frame, text="Clear All", command=clear_all, width=100, height=40).pack(side="left", padx=10)
    
print(f"✅ Successfully loaded total {len(nutrition_data)} unique foods from all datasets.")
