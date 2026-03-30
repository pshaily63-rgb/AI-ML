# Student Timetable Assistant

A terminal-based tool for managing your university timetable, planning your day, tracking tasks, and asking questions about your schedule — all from the command line.

---

## What it does

- Loads your timetable from a CSV file
- Shows your schedule for today, a specific day, or the whole week
- Generates a hour-by-hour day plan based on your classes
- Gives a weekly workload breakdown with study suggestions per subject
- Lets you ask questions about your schedule in plain text
- Sends reminders 10 minutes before each class (runs in the background)
- Lets you add custom reminders at any time
- Tracks one-off tasks tied to specific dates — they disappear once the date passes
- Has a chat mode where you can ask anything about your schedule or study habits

---

## Requirements

- Python 3.8 or higher
- No external libraries — uses only the Python standard library

---

## Setup

1. Clone or download the repository

```
git clone https://github.com/yourusername/student_assistant.git
cd student_assistant
```

2. Prepare your timetable as a CSV file. Two formats are supported:

**Horizontal** (one row per day, time slots as columns):
```
Day,08:30-10:00,10:05-11:35,13:15-14:45
Monday,,Calculus,Physics
Tuesday,Chemistry,,
```

**Vertical** (one row per class):
```
day,time,subject,room,type,duration_mins
Monday,08:30,Calculus,B12,Lecture,90
Tuesday,10:05,Chemistry,Lab3,Lab,90
```

A sample file `timetable2.csv` is included in the repo.

3. Run the program:

```
python main.py
```

On first run it will ask for the path to your CSV file. After that it remembers it in `config.txt`.

---

## Usage

When you run `main.py` you get a numbered menu:

```
  MENU
  1. View timetable
  2. Plan today
  3. Plan a day
  4. Weekly strategy
  5. Ask a question
  6. Reminders
  7. Load different CSV
  8. Extra tasks
  9. Chat
  0. Exit
```

### 1 — View timetable
Shows your full schedule, today only, or a specific day.

### 2 — Plan today
Generates a full day plan for today — wake time, pre-reads, class blocks with gap suggestions, and an evening study schedule ordered by subject priority.

### 3 — Plan a day
Same as above but you pick the day.

### 4 — Weekly strategy
Shows a workload bar chart by day, a per-subject study breakdown, and which days are best for each subject.

### 5 — Ask a question
Type a question about your schedule. Examples:
- `what do I have on Wednesday`
- `which is my busiest day`
- `how do I study for calculus`
- `how do I prepare for exams`
- `how much sleep do I need`

### 6 — Reminders
Set custom reminders at a specific time. Class reminders (10 min before) fire automatically in the background.

### 7 — Load different CSV
Switch to a different timetable file without restarting.

### 8 — Extra tasks
Add one-off tasks tied to a specific date. Tasks show up under the right day and are automatically removed once the date passes.

```
  EXTRA TASKS
  1. Today   2. All upcoming   3. Add   4. Remove   0. Back
```

When adding a task, enter the date as `dd/mm/yyyy`. The day name is resolved automatically from the calendar.

### 9 — Chat
A conversational interface. You can type questions naturally instead of navigating menus.

Commands inside chat:
- `plan Monday` — full day plan for that day
- `week` — weekly strategy
- `topics` — list anything you've taught it
- `exit` — go back to the main menu

If you ask something it doesn't know, it will ask if you want to save the answer for next time.

---

## File structure

```
student_assistant/
├── main.py            — entry point, menu loop
├── csv_loader.py      — parses horizontal and vertical CSV formats
├── ai_planner.py      — day planner, weekly strategy, question answering
├── qa.py              — chat mode, Q&A matching, routing
├── reminders.py       — background reminder thread
├── one_day_tasks.py   — date-based task tracking
├── timetable.py       — timetable display utilities
├── timetable2.csv     — sample timetable
├── config.txt         — stores the last used CSV path (auto-generated)
└── one_day_tasks.json — saved tasks (auto-generated)
```

---

## Notes

- `config.txt` and `one_day_tasks.json` are created automatically on first use
- Reminders only fire while the program is running
- The chat Q&A store is in memory only — it resets when you exit. To make it persistent, save the `qa_store` dict to a JSON file (not implemented by default)
- Windows users: the program sets stdout to UTF-8 automatically to handle special characters in the terminal
