from datetime import datetime
from zoneinfo import ZoneInfo

def get_day_suffix(day):
    if 11 <= day <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

now = datetime.now()
day = now.day
year = now.year
month = now.month

def is_after_school_hours() -> bool:
    if now.hour > 8 and now.hour < 15:
        return False
    return True

def cleanDate() -> str:
    now = datetime.now()
    day = now.day
    formatted_date = now.strftime(f"%A, %B {day}{get_day_suffix(day)}")
    return formatted_date

if __name__ == "__main__":
    print(cleanDate())
