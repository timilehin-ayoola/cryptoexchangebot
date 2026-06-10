"""
Rate limiting and anti-spam middleware for the P2P Crypto Exchange Bot.

Tracks per-user request timestamps and enforces configurable limits.
All state is in-memory (resets on restart — acceptable for rate limiting).
"""

from __future__ import annotations

import time
import logging
from collections import defaultdict
from typing import Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Sliding-window rate limiter keyed by user_id.

    Args:
        max_requests:  number of allowed requests within the window.
        window_seconds: sliding window duration in seconds.
        block_seconds: how long to block a user who exceeds the limit.
    """

    def __init__(
        self,
        max_requests: int = 5,
        window_seconds: int = 30,
        block_seconds: int = 60,
    ):
        self._max_requests = max_requests
        self._window = window_seconds
        self._block_duration = block_seconds
        self._timestamps: dict[int, list[float]] = defaultdict(list)
        self._blocked_until: dict[int, float] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_allowed(self, user_id: int) -> bool:
        """
        Returns True if the user is allowed to make a request right now.
        Records the request timestamp automatically on success.
        """
        now = time.time()

        # Check if user is currently blocked
        if user_id in self._blocked_until:
            if now < self._blocked_until[user_id]:
                remaining = int(self._blocked_until[user_id] - now)
                logger.warning(
                    f"Rate limit: user {user_id} blocked for {remaining}s more"
                )
                return False
            else:
                # Block expired — reset
                del self._blocked_until[user_id]
                self._timestamps.pop(user_id, None)

        # Prune old timestamps outside the window
        ts_list = self._timestamps[user_id]
        cutoff = now - self._window
        ts_list[:] = [t for t in ts_list if t > cutoff]

        # Check limit
        if len(ts_list) >= self._max_requests:
            self._blocked_until[user_id] = now + self._block_duration
            logger.warning(
                f"Rate limit exceeded: user {user_id} blocked for {self._block_duration}s"
            )
            return False

        # Record this request
        ts_list.append(now)
        return True

    def pending_count(self, user_id: int) -> int:
        """Return how many requests the user has made in the current window."""
        ts_list = self._timestamps.get(user_id, [])
        cutoff = time.time() - self._window
        return len([t for t in ts_list if t > cutoff])

    def reset(self, user_id: int) -> None:
        """Manually clear all rate-limit state for a user."""
        self._timestamps.pop(user_id, None)
        self._blocked_until.pop(user_id, None)

    def reset_all(self) -> None:
        """Clear all state."""
        self._timestamps.clear()
        self._blocked_until.clear()
