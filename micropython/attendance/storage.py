import ujson
from time_utils import get_datetime

FILE = "attendance.json"

def load_attendance():
    try:
        with open(FILE, "r") as f:
            return ujson.load(f)
    except:
        return []

def save_attendance(data):
    with open(FILE, "w") as f:
        ujson.dump(data, f)

def roll_exists(roll):
    for r in load_attendance():
        if r["roll"] == roll:
            return True
    return False

def add_record(name, roll):
    if roll_exists(roll):
        return False

    date, clock = get_datetime()
    data = load_attendance()
    data.append({
        "name": name,
        "roll": roll,
        "date": date,
        "time": clock
    })
    save_attendance(data)
    return True
