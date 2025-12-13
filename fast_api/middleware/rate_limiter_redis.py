import os
import time
from datetime import datetime, timedelta
from typing import Optional

import redis
from fastapi import Request, HTTPException

DEFAULT_LIMIT = int(os.getenv("RATE_LIMIT_ANONYMOUS", "5"))
CHAR_MAX = int(os.getenv("RATE_LIMIT_CHAR_MAX", "1000"))
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class RedisRateLimiter:
    """
    Redis-backed rate limiter.
    - Uses IP+UA as anonymous session ID
    - Stores per-session counters with expiration (24h)
    Keys:
      rl:{session_id}:count
      rl:{session_id}:reset
    """
    def __init__(self):
        self.r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        self.window_seconds = 24 * 60 * 60

    def get_session_id(self, request: Request) -> str:
        ip = request.client.host
        ua = request.headers.get("user-agent", "")
        return f"{ip}:{ua}"  # readable key; hashing optional

    def _keys(self, session_id: str):
        base = f"rl:{session_id}"
        return {
            "count": f"{base}:count",
            "reset": f"{base}:reset"
        }

    def check(self, session_id: str, text_len: int):
        if text_len > CHAR_MAX:
            raise HTTPException(
                status_code=400,
                detail=f"Text exceeds {CHAR_MAX} character limit. Please login for extended usage."
            )

        keys = self._keys(session_id)
        now_ts = int(time.time())
        pipe = self.r.pipeline()

        # Initialize if missing
        if not self.r.exists(keys["count"]):
            reset_ts = now_ts + self.window_seconds
            pipe.set(keys["count"], 0, ex=self.window_seconds)
            pipe.set(keys["reset"], reset_ts, ex=self.window_seconds)
            pipe.execute()

        # Increment count atomically
        remaining = None
        try:
            pipe = self.r.pipeline()
            pipe.incr(keys["count"])  # returns new count
            pipe.get(keys["reset"])   # reset timestamp
            count, reset_ts = pipe.execute()
        except redis.RedisError:
            raise HTTPException(status_code=500, detail="Rate limiter backend error")

        if int(count) > DEFAULT_LIMIT:
            reset_iso = datetime.utcfromtimestamp(int(reset_ts)).isoformat() + "Z"
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded ({DEFAULT_LIMIT} requests per session). Please login for unlimited access.",
                headers={
                    "X-RateLimit-Limit": str(DEFAULT_LIMIT),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": reset_iso
                }
            )

        remaining = max(0, DEFAULT_LIMIT - int(count))
        reset_iso = datetime.utcfromtimestamp(int(reset_ts)).isoformat() + "Z"
        return {"remaining": remaining, "reset_iso": reset_iso}
