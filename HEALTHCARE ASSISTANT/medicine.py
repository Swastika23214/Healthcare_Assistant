import sqlite3
import customtkinter as ctk
from tkinter import messagebox


def init_medicine_table():
    """Initialize the medicine table in the database."""
    conn = sqlite3.connect("health_tracker.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS medicine (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            days TEXT NOT NULL,
            time TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


def add_medicine(user_id, parent_win=None):
    """Window for adding new medicine."""
    add_win = ctk.CTkToplevel()
    add_win.title("Add Medicine")
    add_win.geometry("400x450")

    ctk.CTkLabel(add_win, text="Medicine Name").pack(pady=5)
    name_entry = ctk.CTkEntry(add_win, width=300)
    name_entry.pack()

    ctk.CTkLabel(add_win, text="Days (e.g., Mon, Tue, Wed)").pack(pady=5)
    days_entry = ctk.CTkEntry(add_win, width=300)
    days_entry.pack()

    ctk.CTkLabel(add_win, text="Time (HH:MM 24hr)").pack(pady=5)
    time_entry = ctk.CTkEntry(add_win, width=300)
    time_entry.pack()

    ctk.CTkLabel(add_win, text="Notes (optional)").pack(pady=5)
    notes_entry = ctk.CTkTextbox(add_win, width=300, height=80)
    notes_entry.pack()

    def save_medicine():
        """Save the new medicine to the database."""
        name = name_entry.get().strip()
        days = days_entry.get().strip()
        time = time_entry.get().strip()
        notes = notes_entry.get("1.0", "end-1c").strip()  

        if not name or not days or not time:
            messagebox.showerror("Error", "Please fill all required fields.")
            return

        try:
            conn = sqlite3.connect("health_tracker.db")
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO medicine (user_id, name, days, time, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, name, days, time, notes))
            conn.commit()
            conn.close()

            messagebox.showinfo("Success", f"Medicine '{name}' added successfully.")
            add_win.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add medicine: {e}")

    ctk.CTkButton(add_win, text="Save Medicine", command=save_medicine).pack(pady=10)


def view_medicines(user_id):
    """Show all medicines for the logged-in user with edit/delete options."""
    view_win = ctk.CTkToplevel()
    view_win.title("View Medicines")
    view_win.geometry("600x500")

    list_frame = ctk.CTkScrollableFrame(view_win, width=550, height=400)
    list_frame.pack(pady=10)

    try:
        conn = sqlite3.connect("health_tracker.db")
        cur = conn.cursor()
        cur.execute("SELECT id, name, days, time, notes FROM medicine WHERE user_id=?", (user_id,))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            ctk.CTkLabel(list_frame, text="No medicines added yet.").pack(pady=10)
            return

        for med_id, name, days, time, notes in rows:
            frame = ctk.CTkFrame(list_frame)
            frame.pack(pady=5, padx=10, fill="x")

            text = f" {name}\nDays: {days}\nTime: {time}"
            if notes:
                text += f"\nNotes: {notes}"

            ctk.CTkLabel(frame, text=text, justify="left").pack(side="left", padx=10, pady=5)
            ctk.CTkButton(frame, text="Edit", width=60, command=lambda i=med_id: edit_medicine(user_id, i, view_win)).pack(side="right", padx=5)
            ctk.CTkButton(frame, text="Delete", width=60, fg_color="red", command=lambda i=med_id: delete_medicine(user_id, i, view_win)).pack(side="right", padx=5)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to retrieve medicines: {e}")


def delete_medicine(user_id, med_id, parent_win):
    """Delete a medicine entry."""
    if messagebox.askyesno("Confirm", "Delete this medicine?"):
        try:
            conn = sqlite3.connect("health_tracker.db")
            cur = conn.cursor()
            cur.execute("DELETE FROM medicine WHERE id=? AND user_id=?", (med_id, user_id))
            conn.commit()
            conn.close()
            messagebox.showinfo("Deleted", "Medicine deleted successfully.")
            parent_win.destroy()
            view_medicines(user_id)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete medicine: {e}")


def edit_medicine(user_id, med_id, parent_win):
    """Edit selected medicine."""
    try:
        conn = sqlite3.connect("health_tracker.db")
        cur = conn.cursor()
        cur.execute("SELECT name, days, time, notes FROM medicine WHERE id=? AND user_id=?", (med_id, user_id))
        data = cur.fetchone()
        conn.close()

        if not data:
            messagebox.showerror("Error", "Medicine not found.")
            return

        name, days, time, notes = data

        edit_win = ctk.CTkToplevel()
        edit_win.title("Edit Medicine")
        edit_win.geometry("400x450")

        ctk.CTkLabel(edit_win, text="Medicine Name").pack(pady=5)
        e_name = ctk.CTkEntry(edit_win, width=300)
        e_name.insert(0, name)
        e_name.pack()

        ctk.CTkLabel(edit_win, text="Days").pack(pady=5)
        e_days = ctk.CTkEntry(edit_win, width=300)
        e_days.insert(0, days)
        e_days.pack()

        ctk.CTkLabel(edit_win, text="Time (HH:MM 24hr)").pack(pady=5)
        e_time = ctk.CTkEntry(edit_win, width=300)
        e_time.insert(0, time)
        e_time.pack()

        ctk.CTkLabel(edit_win, text="Notes").pack(pady=5)
        e_notes = ctk.CTkTextbox(edit_win, width=300, height=80)
        if notes:  
            e_notes.insert("1.0", notes)
        e_notes.pack()

        def save_changes():
            """Save changes to the medicine."""
            new_name = e_name.get().strip()
            new_days = e_days.get().strip()
            new_time = e_time.get().strip()
            new_notes = e_notes.get("1.0", "end-1c").strip() 

            if not new_name or not new_days or not new_time:
                messagebox.showerror("Error", "Please fill all required fields.")
                return

            try:
                conn = sqlite3.connect("health_tracker.db")
                cur = conn.cursor()
                cur.execute("""
                    UPDATE medicine
                    SET name=?, days=?, time=?, notes=?
                    WHERE id=? AND user_id=?
                """, (new_name, new_days, new_time, new_notes, med_id, user_id))
                conn.commit()
                conn.close()

                messagebox.showinfo("Updated", "Medicine updated successfully.")
                edit_win.destroy()
                parent_win.destroy()
                view_medicines(user_id)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update medicine: {e}")

        ctk.CTkButton(edit_win, text="Save Changes", command=save_changes).pack(pady=10)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load medicine: {e}")


def medicine_gui(user_id):
    """Main GUI for medicine scheduler with menu options."""
    init_medicine_table()

    med_win = ctk.CTkToplevel()
    med_win.title("Medicine Scheduler")
    med_win.geometry("400x400")

    ctk.CTkLabel(med_win, text=" Medicine Scheduler", font=("Arial", 20, "bold")).pack(pady=20)

    ctk.CTkButton(med_win, text=" Add Medicine", width=250, command=lambda: add_medicine(user_id, med_win)).pack(pady=10)
    ctk.CTkButton(med_win, text=" View / Edit / Delete Medicines", width=250, command=lambda: view_medicines(user_id)).pack(pady=10)
    ctk.CTkButton(med_win, text=" Close", width=250, fg_color="gray", command=med_win.destroy).pack(pady=20)
