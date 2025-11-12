import sqlite3
import customtkinter as ctk
from tkinter import messagebox

def init_medicine_table():
    conn = sqlite3.connect("health_tracker.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS medicine (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            time TEXT,
            paused INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_medicine():
    global name_entry, time_entry
    name = name_entry.get().strip()
    time = time_entry.get().strip()

    if not name or not time:
        messagebox.showerror("Error", "Please fill all fields.")
        return

    conn = sqlite3.connect("health_tracker.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO medicine (name, time, paused) VALUES (?, ?, 0)", (name, time))
    conn.commit()
    conn.close()

    messagebox.showinfo("Success", f"Medicine '{name}' added for {time}.")
    name_entry.delete(0, 'end')
    time_entry.delete(0, 'end')
    view_medicines()

def view_medicines():
    global list_frame
    for widget in list_frame.winfo_children():
        widget.destroy()

    conn = sqlite3.connect("health_tracker.db")
    cur = conn.cursor()
    cur.execute("SELECT id, name, time, paused FROM medicine")
    rows = cur.fetchall()
    conn.close()

    for rid, (med_id, name, time, paused) in enumerate(rows):
        ctk.CTkLabel(list_frame, text=f"{name} at {time}").grid(row=rid, column=0, padx=10, pady=5)

        # Button to delete
        ctk.CTkButton(list_frame, text="Delete", width=80, command=lambda i=med_id: delete_medicine(i)).grid(row=rid, column=1, padx=5)

        # Button to pause/resume
        if paused == 0:
            ctk.CTkButton(list_frame, text="Pause", width=80, fg_color="orange",
                          command=lambda i=med_id: toggle_pause(i, True)).grid(row=rid, column=2, padx=5)
        else:
            ctk.CTkButton(list_frame, text="Resume", width=80, fg_color="green",
                          command=lambda i=med_id: toggle_pause(i, False)).grid(row=rid, column=2, padx=5)

def delete_medicine(med_id):
    conn = sqlite3.connect("health_tracker.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM medicine WHERE id=?", (med_id,))
    conn.commit()
    conn.close()
    view_medicines()

def toggle_pause(med_id, pause=True):
    conn = sqlite3.connect("health_tracker.db")
    cur = conn.cursor()
    cur.execute("UPDATE medicine SET paused=? WHERE id=?", (1 if pause else 0, med_id))
    conn.commit()
    conn.close()
    view_medicines()

def medicine_gui():
    global name_entry, time_entry, list_frame
    init_medicine_table()

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

    ctk.CTkButton(med_win, text="Add Medicine", command=add_medicine).pack(pady=10)

    list_frame = ctk.CTkScrollableFrame(med_win, width=450, height=200)
    list_frame.pack(pady=10)
    view_medicines()


   
      
