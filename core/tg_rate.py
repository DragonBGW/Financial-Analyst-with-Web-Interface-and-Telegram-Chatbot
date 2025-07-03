import time
from collections import defaultdict

MAX_CALLS = 10          # per minute
WINDOW    = 60          # seconds

_user_hits = defaultdict(list)

def too_many_calls(user_id: int) -> bool:
    now = time.time()
    hits = [t for t in _user_hits[user_id] if now - t < WINDOW]
    _user_hits[user_id] = hits
    if len(hits) >= MAX_CALLS:
        return True
    hits.append(now)
    return False
