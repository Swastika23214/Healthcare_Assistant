import sqlite3
from plyer import notification
from datetime import datetime

conn = sqlite3.connect("health_tracker.db")
cur = conn.cursor()

now = datetime.now().strftime("%H:%M")

# Only remind if not paused
cur.execute("SELECT name FROM medicine WHERE time=? AND paused=0", (now,))
meds = cur.fetchall()

for med in meds:
    notification.notify(
        title="Medicine Reminder",
        message=f"Time to take {med[0]} 💊",
        message=f"Time to take {med[0]}",
        timeout=10
    )

conn.close()


