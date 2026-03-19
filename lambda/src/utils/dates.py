from datetime import timedelta

def daterange(start, end):
    cur = start
    while cur < end:
        yield cur, min(cur + timedelta(days=1), end)
        cur += timedelta(days=1)
