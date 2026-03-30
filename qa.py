import difflib
from datetime import datetime
from ai_planner import ask_ai, plan_day, suggest_week_plan, _by_day, ORDERED_DAYS

TIMETABLE_TRIGGERS = [
    "today", "tomorrow", "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday", "week", "schedule", "class", "classes",
    "hardest", "lightest", "busiest", "free day", "assignment", "project",
    "study", "revise", "revision", "exam", "test", "break", "sleep",
    "energy", "tired", "plan", "prepare", "focus", "motivat", "procrastinat",
]


def _normalize(text):
    return text.lower().strip().rstrip("?").strip()


def _is_timetable_question(q):
    ql = q.lower()
    return any(t in ql for t in TIMETABLE_TRIGGERS)


def _qa_answer(data, normalized):
    qa = data.get("qa", {})
    if not qa:
        return False

    if normalized in qa:
        print(f"\n  {qa[normalized]}")
        return True

    matches = difflib.get_close_matches(normalized, qa.keys(), n=1, cutoff=0.5)
    if matches:
        best = matches[0]
        print(f"\n  {qa[best]}")
        return True

    words = set(normalized.split())
    scored = [(len(words & set(k.split())), k, v) for k, v in qa.items() if len(words & set(k.split())) > 0]
    if scored:
        scored.sort(reverse=True)
        _, best_key, best_val = scored[0]
        print(f"\n  {best_val}")
        return True

    return False


def answer_question(data, question=None):
    if not question:
        question = input("\n  Ask a question: ").strip()

    normalized = _normalize(question)
    timetable  = data.get("timetable", [])

    if timetable and _is_timetable_question(normalized):
        ask_ai(timetable, normalized)
        return

    # Try Q&A knowledge base
    if _qa_answer(data, normalized):
        return

    # Unknown — offer to teach
    print("  I don't know that one.")
    teach = input("  Want to teach me? (y/n): ").strip().lower()
    if teach == "y":
        answer = input("  Enter the answer: ").strip()
        if answer:
            data.setdefault("qa", {})[normalized] = answer
            print("  [+] Saved.")


def list_topics(data):
    qa = data.get("qa", {})
    if not qa:
        print("  Nothing saved yet.")
        return
    print("\n  Saved topics:")
    for i, key in enumerate(qa.keys(), 1):
        print(f"  {i:>2}. {key.capitalize()}")


def _show_help():
    print("\n  plan <day>  — e.g. 'plan Monday'")
    print("  week        — workload + study breakdown")
    print("  topics      — list saved answers")
    print("  exit        — go back")
    print("\n  Or just ask something like:")
    print("  what do I have today / tomorrow / on Wednesday")
    print("  which day is the busiest")
    print("  how do I study for calculus")
    print("  how do I prepare for exams")
    print("  how much sleep do I need")


def chat_mode(data):
    timetable = data.get("timetable", [])
    bd        = _by_day(timetable) if timetable else {}
    today     = datetime.now().strftime("%A")

    print("\n  " + "─" * 50)
    print("    Chat")
    print("  " + "─" * 50)
    if timetable:
        entries = bd.get(today, [])
        if entries:
            print(f"\n  Today ({today}): {len(entries)} class(es) — {', '.join(e['subject'] for e in entries)}")
        else:
            print(f"\n  No classes today ({today}).")
    print("  Type 'help' for a list of commands.\n")

    while True:
        try:
            q = input("  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not q:
            continue

        ql = q.lower().strip()

        if ql == "exit":
            break

        if ql == "help":
            _show_help()
            continue

        if ql == "topics":
            list_topics(data)
            continue

        if ql in ("week", "weekly", "weekly strategy", "week plan"):
            if timetable:
                suggest_week_plan(timetable)
            else:
                print("  No timetable loaded.")
            continue

        # 'plan monday' / 'plan my tuesday' etc.
        if ql.startswith("plan"):
            matched_day = next((d for d in ORDERED_DAYS if d.lower() in ql), None)
            if matched_day and timetable:
                entries = sorted(bd.get(matched_day, []), key=lambda x: x["time"])
                plan_day(matched_day, entries)
            elif not matched_day:
                print("  Which day? e.g. 'plan Monday'")
            else:
                print("  No timetable loaded.")
            continue

        answer_question(data, q)
