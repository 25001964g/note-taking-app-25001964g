from src.main_flask import infer_event_datetime

if __name__ == "__main__":
    samples = [
        "There is a meeting scheduled with John today at 18:00.",
        "Dinner tomorrow at 6pm",
        "Call on next Monday evening",
        "Standup 09:30",
    ]
    for s in samples:
        d, t = infer_event_datetime(s)
        print(f"text={s!r} -> date={d}, time={t}")
