from datetime import datetime, timedelta
from collections import Counter

ORDERED_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

HIGH_PRIORITY = ["math", "calculus", "algebra", "statistics", "physics", "chemistry",
                 "programming", "data", "database", "algorithms", "networks", "ai",
                 "machine learning", "signals", "transform", "differential", "equations"]
LOW_PRIORITY  = ["english", "history", "geography", "writing", "arts", "communication",
                 "values", "ethics", "humanities"]

ENERGY = {
    "peak":     (6,  10),
    "moderate": (10, 13),
    "low":      (13, 15),
    "second":   (15, 18),
    "wind":     (18, 21),
}


def _parse(t):
    return datetime.strptime(t, "%H:%M")

def _fmt(dt):
    return dt.strftime("%H:%M")

def _priority(subject):
    s = subject.lower()
    if any(k in s for k in HIGH_PRIORITY): return 3
    if any(k in s for k in LOW_PRIORITY):  return 1
    return 2

def _energy_label(hour):
    if ENERGY["peak"][0]     <= hour < ENERGY["peak"][1]:     return "Peak energy"
    if ENERGY["moderate"][0] <= hour < ENERGY["moderate"][1]: return "Moderate energy"
    if ENERGY["low"][0]      <= hour < ENERGY["low"][1]:      return "Post-lunch dip"
    if ENERGY["second"][0]   <= hour < ENERGY["second"][1]:   return "Second wind"
    if ENERGY["wind"][0]     <= hour < ENERGY["wind"][1]:     return "Wind-down"
    return ""

def _gap_suggestion(gap_mins, before, after):
    if gap_mins <= 10:
        return "Quick walk to next class."
    if gap_mins <= 20:
        return f"Glance at {after} notes — 10 min, then head over."
    if gap_mins <= 45:
        return f"Review {before} key points (15 min) + skim {after} intro (10 min)."
    if gap_mins <= 90:
        return f"Consolidate {before} (20 min), prep {after} (20 min), eat/rest remaining."
    return f"Deep gap: revise {before} (30 min), break (15 min), pre-read {after} (25 min), rest."

def _study_action(subject, priority):
    if priority == 3:
        return "solve practice problems + review formulas"
    if priority == 2:
        return "summarize notes + attempt past questions"
    return "read & highlight key concepts"

def _divider():
    print("  " + "─" * 60)

def _by_day(entries):
    d = {}
    for e in entries:
        d.setdefault(e["day"], []).append(e)
    return d

def _day_load(by_day):
    return {day: sum(e["duration_mins"] for e in es) for day, es in by_day.items()}


def plan_day(day, entries):
    if not entries:
        print(f"\n  No classes on {day}.")
        print("  Since you're free, use the morning for your hardest subject,")
        print("  afternoon for any assignments, and keep the evening light.")
        return

    entries = sorted(entries, key=lambda x: x["time"])
    first_start = _parse(entries[0]["time"])
    last_end    = _parse(entries[-1]["time"]) + timedelta(minutes=entries[-1]["duration_mins"])
    wake        = first_start - timedelta(minutes=80)

    print()
    _divider()
    print(f"    Day Plan  —  {day}")
    _divider()

    # Morning block
    print(f"\n  {_fmt(wake)}   Wake up + morning routine")
    print(f"  {_fmt(wake + timedelta(minutes=30))}   Breakfast")
    energy = _energy_label(first_start.hour)
    print(f"  {_fmt(wake + timedelta(minutes=50))}   Pre-read: {entries[0]['subject']} (20 min)  [{energy}]")
    print(f"  {_fmt(first_start - timedelta(minutes=10))}   Head to {entries[0]['room']}")

    # Class blocks + gaps
    for i, e in enumerate(entries):
        start  = _parse(e["time"])
        end    = start + timedelta(minutes=e["duration_mins"])
        energy = _energy_label(start.hour)
        label  = f"[{energy}]" if energy else ""
        print(f"\n  {e['time']} → {_fmt(end)}   {e['type'].upper()}: {e['subject']}  |  Room {e['room']}  {label}")

        if i + 1 < len(entries):
            nxt = entries[i + 1]
            gap = int((_parse(nxt["time"]) - end).total_seconds() / 60)
            if gap > 0:
                suggestion = _gap_suggestion(gap, e["subject"], nxt["subject"])
                print(f"  {_fmt(end)} → {_fmt(_parse(nxt['time']))}   Gap {gap} min — {suggestion}")

    # Post-class
    print(f"\n  {_fmt(last_end)}   Classes done.")
    rest_end = last_end + timedelta(minutes=30)
    print(f"  {_fmt(last_end)} → {_fmt(rest_end)}   Rest + snack")

    # Evening study blocks
    print(f"\n  Evening:")
    t    = rest_end
    seen = set()
    for e in sorted(entries, key=lambda x: -_priority(x["subject"])):
        if e["subject"] in seen:
            continue
        seen.add(e["subject"])
        p        = _priority(e["subject"])
        duration = {3: 45, 2: 30, 1: 20}[p]
        end_slot = t + timedelta(minutes=duration)
        action   = _study_action(e["subject"], p)
        energy   = _energy_label(t.hour)
        label    = f"[{energy}]" if energy else ""
        print(f"  {_fmt(t)} → {_fmt(end_slot)}   {e['subject']} — {action} ({duration} min)  {label}")
        t = end_slot + timedelta(minutes=10)

    dinner_end = t + timedelta(minutes=45)
    print(f"\n  {_fmt(t)} → {_fmt(dinner_end)}   Dinner + break")
    t = dinner_end
    print(f"  {_fmt(t)} → {_fmt(t + timedelta(minutes=20))}   Light re-read: today's notes only")
    print(f"  {_fmt(t + timedelta(minutes=20))}   Prep for tomorrow → sleep")
    print(); _divider()


def suggest_week_plan(entries):
    bd = _by_day(entries)
    dl = _day_load(bd)
    sc = Counter(e["subject"] for e in entries)

    print()
    _divider()
    print("    Weekly Strategy")
    _divider()

    # Workload bar chart
    print("\n  Workload by Day:")
    max_load = max(dl.values()) if dl else 1
    for day in ORDERED_DAYS:
        if day not in dl:
            continue
        load    = dl[day]
        classes = len(bd[day])
        level   = "Heavy" if load > 180 else "Moderate" if load > 90 else "Light"
        bar     = "█" * (load * 20 // max_load)
        print(f"  {day:<12} {load:>3} min  {classes} class(es)  {level:<8}  {bar}")

    heaviest = max(dl, key=dl.get)
    lightest = min(dl, key=dl.get)
    free_days = [d for d in ORDERED_DAYS if d not in dl]

    print(f"\n  Heaviest day : {heaviest} ({dl[heaviest]} min) — go easy on self-study that day")
    print(f"  Lightest day : {lightest} ({dl[lightest]} min) — good day for assignments or catching up")
    if free_days:
        print(f"  Free days    : {', '.join(free_days)} — use for revision or rest")

    # Per-subject weekly study schedule
    print("\n  Per subject:")
    print(f"  {'Subject':<36} {'Classes/wk':<12} {'Priority':<10} {'Suggested study'}")
    print("  " + "─" * 75)
    for subject, count in sc.most_common():
        p         = _priority(subject)
        label     = ["Low", "Medium", "High"][p - 1]
        weekly    = {3: "5x × 30 min", 2: "3x × 25 min", 1: "2x × 20 min"}[p]
        strategy  = _study_action(subject, p)
        print(f"  {subject:<36} {count}x/wk      {label:<10} {weekly}")

    # Best days to study each subject
    print("\n  Good days to study each subject:")
    sorted_days = sorted(dl, key=dl.get)
    light_days  = sorted_days[:2]
    for subject in sc:
        p    = _priority(subject)
        days = light_days if p == 3 else sorted_days[:3]
        print(f"  {subject:<36} → {', '.join(days)}")

    print("\n  A few things worth keeping in mind:")
    print("  — Don't cram, spread revision across the week")
    print("  — Harder subjects are better tackled in the morning")
    print("  — Sunday evening is a good time to go over the whole week")
    print("  — 7–8 hours of sleep makes a real difference")
    print(); _divider()


def ask_ai(timetable, question):
    q  = question.lower().strip()
    bd = _by_day(timetable)
    dl = _day_load(bd)
    sc = Counter(e["subject"] for e in timetable)

    print()

    if any(w in q for w in ["hardest", "difficult", "tough", "busiest", "heavy"]):
        day = max(dl, key=dl.get)
        print(f"  {day} has the most classes ({dl[day]} min). Keep extra study light that day.")

    elif any(w in q for w in ["free", "lightest", "easiest", "least busy", "light day"]):
        day = min(dl, key=dl.get)
        if free:
            print(f"  Days with no classes: {', '.join(free)}.")
        print(f"  {day} has the least classes ({dl[day]} min) — good for assignments or extra study.")

    elif any(w in q for w in ["assignment", "project", "homework", "task"]):
        day = min(dl, key=dl.get)
        print(f"  {day} is your lightest day, probably the best time for assignments.")
        print("  Break it into chunks — 45 min on, short break, repeat.")
        print("  Starting early helps, even if it's just 30 minutes.")

    elif any(w in q for w in ["study", "revise", "revision", "prepare", "practice"]):
        matched = [s for s in sc if s.lower() in q or any(w in s.lower() for w in q.split())]
        if matched:
            subj   = matched[0]
            p      = _priority(subj)
            label  = ["Low", "Medium", "High"][p - 1]
            weekly = {3: "5x × 30 min", 2: "3x × 25 min", 1: "2x × 20 min"}[p]
            action = _study_action(subj, p)
            print(f"  {subj} shows up {sc[subj]}x a week — {label.lower()} priority.")
            print(f"  Around {weekly} works well — {action}.")
            print(f"  Morning is usually the better time for this one.")
        else:
            high = [s for s in sc if _priority(s) == 3]
            med  = [s for s in sc if _priority(s) == 2]
            print(f"  High priority subjects: {', '.join(high) if high else 'none flagged'}")
            print(f"  Medium priority: {', '.join(med) if med else 'none'}")
            print("  Generally, do the harder ones first while you still have energy.")

    elif any(w in q for w in ["break", "rest", "relax", "pause"]):
        print("  45-50 min of work then a 10-15 min break is a solid rhythm.")
        print("  If you've been at it for 2+ hours, take a proper break — go outside or eat.")
        print("  Phones off the desk helps more than most people expect.")

    elif any(w in q for w in ["sleep", "tired", "energy", "fatigue", "exhausted"]):
        print("  7-8 hours is the target.")
        print("  Morning (06:00-10:00) is usually when focus is sharpest.")
        print("  After lunch (13:00-15:00) is rough for most people — keep it light.")
        print("  Late night studying past midnight rarely pays off.")

    elif "tomorrow" in q or "next day" in q:
        tomorrow = ORDERED_DAYS[(datetime.now().weekday() + 1) % 7]
        entries  = sorted(bd.get(tomorrow, []), key=lambda x: x["time"])
        if entries:
            print(f"  Tomorrow is {tomorrow}, {len(entries)} class(es).")
            for e in entries:
                print(f"    {e['time']}  {e['subject']}  ({e['type']}, Room {e['room']})")
            print(f"\n  Worth glancing at {entries[0]['subject']} tonight before you sleep.")
        else:
            print(f"  Nothing on tomorrow ({tomorrow}).")

    elif "today" in q:
        today   = datetime.now().strftime("%A")
        entries = sorted(bd.get(today, []), key=lambda x: x["time"])
        if entries:
            print(f"  Today is {today}, {len(entries)} class(es).")
            for e in entries:
                energy = _energy_label(_parse(e["time"]).hour)
                print(f"    {e['time']}  {e['subject']}  ({e['type']}, Room {e['room']})  [{energy}]")
        else:
            print(f"  No classes today ({today}).")

    elif any(d.lower() in q for d in ORDERED_DAYS):
        day     = next(d for d in ORDERED_DAYS if d.lower() in q)
        entries = sorted(bd.get(day, []), key=lambda x: x["time"])
        if entries:
            print(f"  {day}: {len(entries)} class(es), {dl.get(day, 0)} min")
            for e in entries:
                print(f"    {e['time']}  {e['subject']}  ({e['type']}, Room {e['room']})")
        else:
            print(f"  No classes on {day}.")

    elif any(w in q for w in ["week", "weekly", "overview", "schedule", "plan"]):
        suggest_week_plan(timetable)

    elif any(w in q for w in ["exam", "test", "quiz", "exams"]):
        high = [s for s in sc if _priority(s) == 3]
        print("  For exams, starting early is the main thing.")
        print(f"  Prioritise {', '.join(high) if high else 'your harder subjects'} first.")
        print("  Past papers in the last few days, timed if possible.")
        print("  The night before — just a light read, then sleep early.")

    elif any(w in q for w in ["motivat", "procrastinat", "focus", "distract", "lazy"]):
        print("  Starting is usually the hardest part — just open the book.")
        print("  Phone off the desk makes a bigger difference than it sounds.")
        print("  Having a specific goal helps more than a time target.")
        print("  Take a proper break when you're done, not before.")

    else:
        today   = datetime.now().strftime("%A")
        entries = bd.get(today, [])
        print(f"  {len(timetable)} classes across {len(bd)} days.")
        if entries:
            print(f"  Today ({today}): {', '.join(e['subject'] for e in entries)}")
        print(f"  Busiest: {max(dl, key=dl.get)}  |  Lightest: {min(dl, key=dl.get)}")
        print()
        print("  You can ask things like:")
        print("  what do I have on monday / what's my busiest day / how do I study for calculus")
