import csv
import os
import re
from datetime import datetime

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

DAY_MAP = {
    "mon": "Monday", "monday": "Monday",
    "tue": "Tuesday", "tues": "Tuesday", "tuesday": "Tuesday",
    "wed": "Wednesday", "wednesday": "Wednesday",
    "thu": "Thursday", "thur": "Thursday", "thurs": "Thursday", "thursday": "Thursday",
    "fri": "Friday", "friday": "Friday",
    "sat": "Saturday", "saturday": "Saturday",
    "sun": "Sunday", "sunday": "Sunday",
}

SKIP_VALUES = {"", "lunch", "break", "free", "holiday", "-", "--", "n/a", "na", "nil", "none"}

TIME_FORMATS = ["%H:%M", "%I:%M %p", "%I:%M%p", "%H.%M", "%I %p"]


def _resolve_day(raw):
    return DAY_MAP.get(raw.strip().lower().rstrip("."), None)


def _parse_time(raw):
    raw = raw.strip()
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(raw, fmt).strftime("%H:%M")
        except ValueError:
            pass
    m = re.match(r"(\d{1,2})[:\.](\d{2})", raw)
    if m:
        return f"{int(m.group(1)):02d}:{m.group(2)}"
    return None


def _extract_time_from_slot(slot):
    slot = slot.strip()
    m = re.match(r"(\d{1,2}[:.]\d{2})\s*[-to]+\s*\d{1,2}[:.]\d{2}", slot, re.IGNORECASE)
    if m:
        return _parse_time(m.group(1))
    return _parse_time(slot)


def _guess_duration(slot):
    m = re.match(r"(\d{1,2})[.:](\d{2})\s*[-to]+\s*(\d{1,2})[.:](\d{2})", slot.strip(), re.IGNORECASE)
    if m:
        start = int(m.group(1)) * 60 + int(m.group(2))
        end   = int(m.group(3)) * 60 + int(m.group(4))
        diff  = end - start
        return diff if diff > 0 else 60
    return 60


def _is_horizontal(fieldnames):
    first = fieldnames[0].strip().lower().rstrip(".")
    if first not in ("day", "days", "day/time", "time/day"):
        return False
    return any(_extract_time_from_slot(f) is not None for f in fieldnames[1:])


def _is_vertical_time(fieldnames):
    cols = [c.strip().lower() for c in fieldnames]
    has_day     = any(c in ("day", "days") for c in cols)
    has_time    = any(c in ("time", "start", "start time", "period") for c in cols)
    has_subject = any(c in ("subject", "course", "class", "module", "paper") for c in cols)
    return has_day and has_time and has_subject


def _find_col(row_keys, candidates):
    for k in row_keys:
        if k.strip().lower() in candidates:
            return k
    return None


def _load_horizontal(reader, fieldnames):
    time_cols = {}
    for col in fieldnames[1:]:
        t = _extract_time_from_slot(col)
        if t:
            time_cols[col] = (t, _guess_duration(col))

    entries = []
    for row in reader:
        raw_day = row[fieldnames[0]].strip()
        day = _resolve_day(raw_day)
        if not day:
            continue
        for col, (time, duration) in time_cols.items():
            subject = row.get(col, "").strip()
            if subject.lower() in SKIP_VALUES:
                continue
            entries.append({
                "day":           day,
                "time":          time,
                "subject":       subject,
                "duration_mins": duration,
                "room":          "TBD",
                "type":          "Lecture",
            })
    return entries


def _load_vertical(reader, fieldnames):
    keys = [f.strip() for f in fieldnames]

    day_col     = _find_col(keys, {"day", "days"})
    time_col    = _find_col(keys, {"time", "start", "start time", "period", "slot"})
    subject_col = _find_col(keys, {"subject", "course", "class", "module", "paper", "name"})
    dur_col     = _find_col(keys, {"duration", "duration_mins", "duration (mins)", "mins", "minutes"})
    room_col    = _find_col(keys, {"room", "venue", "hall", "location", "lab"})
    type_col    = _find_col(keys, {"type", "class type", "session", "kind"})

    entries = []
    for i, row in enumerate(reader, 2):
        raw_day = row.get(day_col, "").strip()
        day = _resolve_day(raw_day)
        if not day:
            print(f"  [!] Row {i}: unrecognised day '{raw_day}' — skipped.")
            continue

        raw_time = row.get(time_col, "").strip()
        time = _extract_time_from_slot(raw_time)
        if not time:
            print(f"  [!] Row {i}: unrecognised time '{raw_time}' — skipped.")
            continue

        subject = row.get(subject_col, "").strip()
        if subject.lower() in SKIP_VALUES:
            continue

        duration = 60
        if dur_col:
            try:
                duration = int(row.get(dur_col, 60))
            except ValueError:
                duration = _guess_duration(raw_time) or 60
        else:
            duration = _guess_duration(raw_time) or 60

        entries.append({
            "day":           day,
            "time":          time,
            "subject":       subject,
            "duration_mins": duration,
            "room":          row.get(room_col, "TBD").strip() if room_col else "TBD",
            "type":          row.get(type_col, "Lecture").strip() if type_col else "Lecture",
        })
    return entries


def load_csv(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
    reader_data = None
    for enc in encodings:
        try:
            f = open(filepath, newline="", encoding=enc)
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            rows = list(reader)
            f.close()
            reader_data = (fieldnames, rows)
            break
        except (UnicodeDecodeError, Exception):
            f.close()
            continue

    if not reader_data:
        raise ValueError("Could not read the CSV file. Try saving it as UTF-8.")

    fieldnames, rows = reader_data
    if not fieldnames:
        raise ValueError("CSV appears to be empty or has no headers.")

    class FakeReader:
        def __init__(self, rows): self._rows = iter(rows)
        def __iter__(self): return self._rows

    if _is_horizontal(fieldnames):
        return _load_horizontal(FakeReader(rows), fieldnames)

    if _is_vertical_time(fieldnames):
        return _load_vertical(FakeReader(rows), fieldnames)

    raise ValueError(
        "Could not understand your CSV format.\n"
        "  Supported formats:\n"
        "  1. Horizontal: Day | 09:00-10:00 | 10:05-11:35 | ...\n"
        "  2. Vertical  : day, time, subject, room, type, duration_mins"
    )


def show_day(entries, day):
    day_entries = sorted(
        [e for e in entries if e["day"].lower() == day.lower()],
        key=lambda x: x["time"]
    )
    if not day_entries:
        print(f"  No classes on {day}.")
        return day_entries

    print(f"\n  {day}:")
    print(f"  {'Time':<8} {'Subject':<36} {'Dur':>5}  {'Room':<10} {'Type'}")
    print("  " + "-" * 68)
    for e in day_entries:
        print(f"  {e['time']:<8} {e['subject']:<36} {e['duration_mins']:>4}m  {e['room']:<10} {e['type']}")
    return day_entries


def show_all(entries):
    for day in DAYS:
        if any(e["day"] == day for e in entries):
            show_day(entries, day)
