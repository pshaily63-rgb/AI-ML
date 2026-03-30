import threading
import time
from datetime import datetime

_started = False


def _loop(data):
    notified = set()
    while True:
        now          = datetime.now()
        current_time = now.strftime("%H:%M")
        current_day  = now.strftime("%A")
        now_minutes  = now.hour * 60 + now.minute

        for entry in data.get("timetable", []):
            if entry["day"] != current_day:
                continue
            h, m          = map(int, entry["time"].split(":"))
            class_minutes = h * 60 + m
            key           = f"class_{entry['day']}_{entry['time']}_{entry['subject']}"
            if class_minutes - now_minutes == 10 and key not in notified:
                print(f"\n  [REMINDER] {entry['subject']} in 10 minutes — Room {entry['room']}")
                notified.add(key)

        for r in data.get("reminders", []):
            key = f"custom_{r['time']}_{r['message']}"
            if r["time"] == current_time and key not in notified:
                print(f"\n  [REMINDER] {r['message']}")
                notified.add(key)

        if current_time == "00:00":
            notified.clear()

        time.sleep(30)


def start_reminder_thread(data):
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_loop, args=(data,), daemon=True).start()
    print("  [+] Reminder service active.")


def add_reminder(data):
    time_str = input("  Time (HH:MM): ").strip()
    message  = input("  Message: ").strip()
    data["reminders"].append({"time": time_str, "message": message})
    print(f"  [+] Reminder set — {time_str}: {message}")


def list_reminders(data):
    reminders = data.get("reminders", [])
    if not reminders:
        print("  No reminders set.")
        return
    print("\n  Reminders:")
    for i, r in enumerate(reminders, 1):
        print(f"  {i}. {r['time']}  {r['message']}")


def remove_reminder(data):
    list_reminders(data)
    try:
        idx = int(input("\n  Remove number: ")) - 1
        removed = data["reminders"].pop(idx)
        print(f"  [+] Removed: {removed['message']}")
    except (ValueError, IndexError):
        print("  [!] Invalid selection.")
