import os
import sys
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from csv_loader import load_csv, show_day, show_all
from ai_planner import plan_day, ask_ai, suggest_week_plan
from reminders  import start_reminder_thread, add_reminder, list_reminders, remove_reminder
from one_day_tasks import add_task, view_tasks, view_today, remove_task, purge_old_tasks
from qa import chat_mode

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.txt")


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return ""
    with open(CONFIG_FILE, encoding="utf-8") as f:
        lines = dict(line.strip().split("=", 1) for line in f if "=" in line)
    return lines.get("csv_path", "")


def save_config(csv_path):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(f"csv_path={csv_path}\n")


def load_timetable(csv_path):
    try:
        entries = load_csv(csv_path)
        print(f"  [+] {len(entries)} classes loaded from {os.path.basename(csv_path)}")
        return entries
    except Exception as e:
        print(f"  [!] {e}")
        return []


def reminder_menu(data):
    while True:
        print("\n  REMINDERS")
        print("  1. List   2. Add   3. Remove   0. Back")
        c = input("\n  Choice: ").strip()
        if   c == "1": list_reminders(data)
        elif c == "2": add_reminder(data)
        elif c == "3": remove_reminder(data)
        elif c == "0": break


def main():
    print("\n" + "=" * 55)
    print("   Student Timetable Assistant")
    print(f"   {datetime.now().strftime('%A, %d %b %Y  %H:%M')}")
    print("=" * 55)

    csv_path = load_config()
    if not csv_path:
        sample = os.path.join(os.path.dirname(__file__), "sample_timetable.csv")
        print("\n  No timetable loaded. Sample available: sample_timetable.csv")
        path     = input("  CSV path [Enter for sample]: ").strip()
        csv_path = path if path else sample
        save_config(csv_path)

    timetable = load_timetable(csv_path)
    reminder_data = {"timetable": timetable, "reminders": []}
    start_reminder_thread(reminder_data)
    purge_old_tasks()

    while True:
        print("\n  MENU")
        print("  1. View timetable")
        print("  2. Plan today")
        print("  3. Plan a day")
        print("  4. Weekly strategy")
        print("  5. Ask a question")
        print("  6. Reminders")
        print("  7. Load different CSV")
        print("  8. Extra tasks")
        print("  9. Chat assistant")
        print("  0. Exit")
        c = input("\n  Choice: ").strip()

        if c == "1":
            print("  1. All   2. Today   3. By day")
            s = input("  Choice: ").strip()
            if   s == "1": show_all(timetable)
            elif s == "2": show_day(timetable, datetime.now().strftime("%A"))
            elif s == "3": show_day(timetable, input("  Day: ").strip().capitalize())

        elif c == "2":
            today   = datetime.now().strftime("%A")
            entries = [e for e in timetable if e["day"] == today]
            show_day(timetable, today)
            plan_day(today, entries)

        elif c == "3":
            day     = input("  Day: ").strip().capitalize()
            entries = [e for e in timetable if e["day"] == day]
            show_day(timetable, day)
            plan_day(day, entries)

        elif c == "4":
            suggest_week_plan(timetable)

        elif c == "5":
            ask_ai(timetable, input("\n  Question: ").strip())

        elif c == "6":
            reminder_menu(reminder_data)

        elif c == "7":
            path = input("  CSV path: ").strip()
            if path:
                csv_path  = path
                save_config(csv_path)
                timetable = load_timetable(csv_path)

        elif c == "8":
            while True:
                print("\n  EXTRA TASKS")
                print("  1. Today   2. All upcoming   3. Add   4. Remove   0. Back")
                t = input("\n  Choice: ").strip()
                if   t == "1": view_today()
                elif t == "2": view_tasks()
                elif t == "3": add_task()
                elif t == "4": remove_task()
                elif t == "0": break

        elif c == "9":
            if "qa_store" not in reminder_data:
                reminder_data["qa_store"] = {}
            chat_mode({"timetable": timetable, "qa": reminder_data["qa_store"]})

        elif c == "0":
            print("\n  Goodbye!\n")
            raise SystemExit(0)


if __name__ == "__main__":
    main()
