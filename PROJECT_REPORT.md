# Project Report — Student Timetable Assistant

---

## 1. The Problem

University students deal with a lot of moving parts  classes spread across the week, subjects with different difficulty levels, assignments with deadlines, and the general pressure of managing time well. Most students either rely on a paper timetable or a calendar app, but neither of those tells you what to actually do with your time. They show you what's scheduled, not how to prepare for it or how to distribute your study load.

The specific problems I wanted to address:

- Students often don't know which days are their heaviest or lightest until they're already in the middle of a bad week
- There's no easy way to get a study plan that's based on your actual schedule rather than generic advice
- Reminders for classes are usually set manually, one by one
- Last-minute tasks (a surprise quiz, a submission moved forward) have no good place to live — they either get added to a calendar and forgotten, or written on paper and lost
- Looking up "what do I have on Wednesday" requires opening an app, navigating to the right view, and scrolling — more friction than it should be

---

## 2. Why it matters

Time management is one of the most common reasons students underperform, not lack of ability. A tool that sits close to where students already work (the terminal, for CS students especially) and gives useful, schedule aware answers without requiring a phone or a browser felt worth building.

The goal wasn't to build something flashy. It was to build something that a student could actually open every morning and get something useful out of in under a minute.

---

## 3. Approach

The project is a command line Python application with no external dependencies. Everything runs on the standard library.

The core idea was to keep the data model simple a timetable is just a list of dicts, each with a day, time, subject, room, type, and duration. Everything else (planning, strategy, reminders, tasks) operates on that same list.

### Modules

**csv_loader.py**
The first real challenge was that timetables come in different formats. Some are horizontal (days as rows, time slots as columns), some are vertical (one row per class). The loader detects the format automatically by inspecting the headers and routes to the right parser. It also handles multiple encodings, fuzzy day name matching (mon, MON, Monday all work), and time range parsing (08:30-10:00 extracts both the start time and duration).

**ai_planner.py**
This is the main logic module. It does three things:

- `plan_day` — takes a day's classes, sorts them by time, and builds a full schedule from wake-up to sleep. Gaps between classes get suggestions based on their length. Evening study blocks are ordered by subject priority (harder subjects first) with durations scaled to priority level. Each time slot is tagged with an energy label (peak, moderate, post-lunch dip, second wind, wind-down) based on the hour.

- `suggest_week_plan` — aggregates the whole timetable into a workload summary. Shows a bar chart of minutes per day, identifies the heaviest and lightest days, and produces a per-subject breakdown with suggested weekly study frequency and which days to use for each subject.

- `ask_ai` — handles plain-text questions about the schedule. Uses keyword matching to route questions to the right response. Covers schedule queries (today, tomorrow, specific days), study advice, sleep and energy, exam prep, and focus/motivation questions.

**qa.py**
Wraps the planner with a chat interface. Incoming questions are first checked against a keyword list to decide if they're timetable related, if yes, they go to `ask_ai`. If not, they go through a fuzzy Q&A lookup using `difflib`. If nothing matches, the user is offered the option to save the answer for next time.

**reminders.py**
Runs a background thread that checks the current time every 30 seconds. If a class is 10 minutes away, it prints a reminder to the terminal. Custom reminders work the same way — stored as time + message pairs, fired when the clock matches.

**one_day_tasks.py**
Stores tasks as a JSON list, each with a date (ISO format), day name, description, and optional time. The day name is derived from the date using the calendar, so there's no manual input required. On startup, any task whose date is in the past is automatically removed.

---

## 4. Key decisions

**No external libraries**
Keeping it stdlib only means there's nothing to install. A student can clone the repo and run it immediately. It also forced cleaner solutions the CSV parser, fuzzy matching, and background threading all had to be done from scratch or with what's available.

**CSV as the data source**
Most university timetable systems let you export to CSV. Using CSV as the input format means the tool works with real data without any manual entry. The auto detection of horizontal vs vertical format was important here, students shouldn't have to reformat their export to use the tool.

**Keyword routing over a real NLP model**
Using a language model for the chat would have added a dependency and required an API key or local model. Keyword matching is fast, predictable, and works offline. The tradeoff is that it can miss questions phrased in unexpected ways, but for a fixed domain (one student's timetable), the coverage is good enough.

**Date-based tasks instead of day-based**
The first version of the task system used day names as keys (Monday, Tuesday, etc.), which meant tasks had no expiry, a task added for "Monday" would show up every Monday. Switching to ISO dates (2025-07-21) tied each task to a specific calendar date, so they expire naturally and the day name is just derived metadata.

**Persistent Q&A store per session**
The chat Q&A store lives in memory during a session. This was a deliberate choice to keep the scope manageable, persisting it to JSON would be a small addition but wasn't necessary for the core functionality.

**Subject priority classification**
Rather than asking the user to rate each subject, priority is inferred from the subject name using keyword lists. Math, calculus, physics, programming, etc. are high priority. English, history, communication subjects are low. Everything else is medium. This is a heuristic and won't always be right, but it's a reasonable default that works without any setup.

---

## 5. Challenges

**CSV format detection**
The hardest part of the CSV loader was making it robust. Real timetable exports have inconsistent headers, mixed case, extra whitespace, BOM characters, and different encodings. The loader tries four encodings, strips and lowercases headers for comparison, and uses regex to extract time ranges from column names. Getting this right took several iterations.

**Gap suggestions that don't feel generic**
The first version of gap suggestions was just a fixed message based on gap length. It felt useless. The improved version uses the actual subject names before and after the gap, so the suggestion says "review Calculus key points, then skim Physics intro" instead of "use this time to review". Small change, much more useful output.

**Energy labels and evening scheduling**
The energy curve (peak in the morning, dip after lunch, second wind in the afternoon) is a rough model. The tricky part was that evening study blocks could run past 21:00 if a student had many classes, at which point the energy labels stop applying. The current implementation just omits the label if the hour falls outside the defined ranges, which is cleaner than showing a wrong label.

**Keeping responses from sounding generated**
A lot of the output in the planner and chat initially read like it came from a productivity app — bullet points, bold claims, prescriptive language. Rewriting it to sound like a person talking took more passes than expected. The main changes were removing section headers, dropping phrases like "non-negotiable" and "retention drops sharply", and making suggestions feel like observations rather than instructions.

**Module-level constants that go stale**
The task module originally set `TODAY = date.today().isoformat()` at import time. If the program ran past midnight, `TODAY` would be wrong for the rest of the session. Replacing it with a `_today()` function that's called at runtime fixed this cleanly.

---

## 6. What I learned

**Parsing is harder than logic**
The planning and strategy logic was straightforward to write. The CSV parser took much longer and had more edge cases. Real world data is messy in ways that are hard to anticipate until you actually test with real files.

**Heuristics are underrated**
Subject priority by keyword, energy levels by hour, study duration by priority level none of these are scientifically precise, but they produce useful output without any user configuration. For a tool like this, a good heuristic that works immediately is more valuable than a precise model that requires setup.

**Output design matters as much as logic**
The same information presented differently can feel helpful or useless. The gap suggestions, the workload bar chart, the evening study blocks these all went through multiple rewrites not because the logic was wrong but because the output wasn't readable or useful enough. Spending time on how things are displayed is not wasted time.

**Separation of concerns pays off**
Keeping the CSV loader, planner, chat, reminders, and tasks in separate modules made it easy to change one without breaking others. When the task system was redesigned from day based to date-based, nothing else needed to change. When the chat routing was added to `qa.py`, the planner didn't need to know about it.

**Scope creep is real**
The project started as a timetable viewer. It grew into a planner, then added a strategist, then a chat interface, then tasks. Each addition was small on its own but the cumulative scope was much larger than the original plan. Managing that required being deliberate about what each module was responsible for and not letting features bleed into each other.

---

## 7. What could be improved

- The Q&A store could be persisted to a JSON file so answers survive between sessions
- The subject priority classification could be user configurable a student might want to mark a specific subject as high priority regardless of its name
- The reminder system only works while the terminal is open a proper notification system (OS-level toast notifications) would be more reliable
- The chat routing is keyword-based and will miss questions phrased in unexpected ways a small embedding-based similarity model could improve this without adding heavy dependencies
- The day planner assumes a fixed wake time relative to the first class letting the user set a preferred wake time would make the output more accurate
