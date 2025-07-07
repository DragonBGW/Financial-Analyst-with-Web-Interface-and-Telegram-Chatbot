# core/tg_rate.py
import time
from django.core.cache import cache

MAX_CALLS = 10  # per minute
WINDOW = 60     # seconds

def too_many_calls(user_id: int) -> bool:
    cache_key = f"rate_limit:{user_id}"
    now = time.time()
    
    # Get existing hits or initialize
    hits = cache.get(cache_key, [])
    
    # Filter hits within time window
    hits = [t for t in hits if now - t < WINDOW]
    
    if len(hits) >= MAX_CALLS:
        return True
        
    hits.append(now)
    cache.set(cache_key, hits, timeout=WINDOW)
    return False