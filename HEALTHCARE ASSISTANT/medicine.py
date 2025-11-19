import sqlite3
import customtkinter as ctk
from tkinter import messagebox

def add_medicine(user_id):
    global name_entry, time_entry
    name = name_entry.get().strip()
    time = time_entry.get().strip()

    if not name or not time:
        messagebox.showerror("Error", "Please fill all fields.")
        return

    conn = sqlite3.connect("health_tracker.db")
    cur = conn.cursor()
    # Use the columns from database.py schema
    cur.execute("""
        INSERT INTO medicine (user_id, name, time, paused) 
        VALUES (?, ?, ?, 0)
    """, (user_id, name, time))
    conn.commit()
    conn.close()

    messagebox.showinfo("Success", f"Medicine '{name}' added for {time}.")
    name_entry.delete(0, 'end')
    time_entry.delete(0, 'end')
    view_medicines(user_id)

def view_medicines(user_id):
    global list_frame
    for widget in list_frame.winfo_children():
        widget.destroy()

    conn = sqlite3.connect("health_tracker.db")
    cur = conn.cursor()
    cur.execute("SELECT id, name, time, paused FROM medicine WHERE user_id=?", (user_id,))
    rows = cur.fetchall()
    conn.close()

    for rid, (med_id, name, time, paused) in enumerate(rows):
        ctk.CTkLabel(list_frame, text=f"{name} at {time}").grid(row=rid, column=0, padx=10, pady=5)

        ctk.CTkButton(list_frame, text="Delete", width=80, 
                      command=lambda i=med_id: delete_medicine(i, user_id)).grid(row=rid, column=1, padx=5)

        if paused == 0:
            ctk.CTkButton(list_frame, text="Pause", width=80, fg_color="orange",
                          command=lambda i=med_id: toggle_pause(i, True, user_id)).grid(row=rid, column=2, padx=5)
        else:
            ctk.CTkButton(list_frame, text="Resume", width=80, fg_color="green",
                          command=lambda i=med_id: toggle_pause(i, False, user_id)).grid(row=rid, column=2, padx=5)

def delete_medicine(med_id, user_id):
    conn = sqlite3.connect("health_tracker.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM medicine WHERE id=?", (med_id,))
    conn.commit()
    conn.close()
    view_medicines(user_id)

def toggle_pause(med_id, pause, user_id):
    conn = sqlite3.connect("health_tracker.db")
    cur = conn.cursor()
    cur.execute("UPDATE medicine SET paused=? WHERE id=?", (1 if pause else 0, med_id))
    conn.commit()
    conn.close()
    view_medicines(user_id)

def medicine_gui(user_id):
    global name_entry, time_entry, list_frame
    # REMOVED init_medicine_table() - table is created in database.py

    med_win = ctk.CTkToplevel()
    med_win.title("Medicine Scheduler")
    screen_width = med_win.winfo_screenwidth()
    screen_height = med_win.winfo_screenheight()
    med_win.geometry(f"{screen_width}x{screen_height}")

    ctk.CTkLabel(med_win, text="Medicine Name").pack(pady=5)
    name_entry = ctk.CTkEntry(med_win, width=300)
    name_entry.pack()

    ctk.CTkLabel(med_win, text="Time (HH:MM 24hr)").pack(pady=5)
    time_entry = ctk.CTkEntry(med_win, width=300)
    time_entry.pack()

    ctk.CTkButton(med_win, text="Add Medicine", command=lambda: add_medicine(user_id)).pack(pady=10)

    list_frame = ctk.CTkScrollableFrame(med_win, width=450, height=200)
    list_frame.pack(pady=10)
    view_medicines(user_id)
