import json
import os
from datetime import datetime, date

TASKS_FILE = os.path.join(os.path.dirname(__file__), "one_day_tasks.json")


def _today():
    return date.today().isoformat()


def _load():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)


def _parse_date(raw):
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y"):
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            pass
    return None


def add_task():
    raw = input("\n  Date (dd/mm/yyyy): ").strip()
    d = _parse_date(raw)
    if not d:
        print("  [!] Invalid date format. Use dd/mm/yyyy.")
        return
    if d < date.today():
        print("  [!] That date has already passed.")
        return
    task = input("  Task description: ").strip()
    time = input("  Time (HH:MM or leave blank): ").strip()
    if not task:
        print("  [!] Task cannot be empty.")
        return
    tasks = _load()
    tasks.append({
        "date": d.isoformat(),
        "day":  d.strftime("%A"),
        "task": task,
        "time": time or "—",
    })
    _save(tasks)
    print(f"  [+] Task added for {d.strftime('%A, %d %b %Y')}.")


def view_tasks(filter_date=None):
    tasks = _load()
    if filter_date:
        tasks = [t for t in tasks if t["date"] == filter_date]
        label = date.fromisoformat(filter_date).strftime("%A, %d %b %Y")
    else:
        tasks = sorted(tasks, key=lambda t: t["date"])
        label = "all upcoming days"

    if not tasks:
        print(f"\n  No extra tasks for {label}.")
        return
    print(f"\n  Extra tasks — {label}:")
    for i, t in enumerate(tasks, 1):
        prefix = f"{t['day']}, {date.fromisoformat(t['date']).strftime('%d %b %Y')}" if not filter_date else ""
        suffix = f"  ({prefix})" if prefix else ""
        print(f"    {i}. [{t['time']}]  {t['task']}{suffix}")


def view_today():
    view_tasks(_today())


def remove_task():
    tasks = sorted(_load(), key=lambda t: t["date"])
    if not tasks:
        print("  No tasks to remove.")
        return
    print("\n  All extra tasks:")
    for i, t in enumerate(tasks, 1):
        print(f"    {i}. [{t['date']} {t['day']}]  [{t['time']}]  {t['task']}")
    try:
        n = int(input("\n  Remove task #: ").strip())
        if 1 <= n <= len(tasks):
            removed = tasks.pop(n - 1)
            _save(tasks)
            print(f"  [-] Removed: {removed['task']} ({removed['date']})")
        else:
            print("  [!] Invalid number.")
    except ValueError:
        print("  [!] Enter a valid number.")


def purge_old_tasks():
    today = _today()
    tasks = _load()
    cleaned = [t for t in tasks if t["date"] >= today]
    if len(cleaned) != len(tasks):
        _save(cleaned)
