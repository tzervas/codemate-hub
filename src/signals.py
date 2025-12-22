"""
Signal Emitter/Consumer System for Agent Task Orchestration

This module provides a lightweight publish-subscribe signal system for coordinating
agent task completion and triggering sequential or parallel operations.

Key Features:
- Event-based signal emission for task lifecycle (started, completed, failed)
- Subscriber pattern for loose coupling between agents and orchestrator
- Thread-safe signal handling for concurrent agent execution
- Type-safe signal payloads with Pydantic validation
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    """Signal types for task lifecycle events."""

    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    AGENT_READY = "agent_ready"
    AGENT_BUSY = "agent_busy"


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SignalPayload(BaseModel):
    """Base payload for all signals with common metadata."""

    signal_id: UUID = Field(default_factory=uuid4)
    signal_type: SignalType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    task_id: str
    agent_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }


@dataclass
class Subscription:
    """Represents a signal subscription."""

    subscriber_id: str
    signal_types: Set[SignalType]
    callback: Callable[[SignalPayload], None]
    task_filter: Optional[str] = None  # Only receive signals for specific task_id


class SignalEmitter:
    """
    Thread-safe signal emitter for publishing task lifecycle events.

    This class implements the publisher side of the pub-sub pattern,
    allowing agents and orchestrators to emit signals when task states change.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._subscribers: List[Subscription] = []
        self._signal_history: List[SignalPayload] = []
        self._max_history = 1000  # Limit history to prevent memory growth

    def emit(self, signal: SignalPayload) -> None:
        """
        Emit a signal to all matching subscribers.

        Args:
            signal: The signal payload to emit

        Thread-safe: Yes
        """
        with self._lock:
            # Store in history
            self._signal_history.append(signal)
            if len(self._signal_history) > self._max_history:
                self._signal_history = self._signal_history[-self._max_history :]

            # Find matching subscribers
            matching_subscribers = self._find_matching_subscribers(signal)

            logger.debug(
                f"Emitting signal {signal.signal_type} for task {signal.task_id} "
                f"to {len(matching_subscribers)} subscribers"
            )

        # Call subscribers outside the lock to prevent deadlocks
        for subscription in matching_subscribers:
            try:
                subscription.callback(signal)
            except Exception as e:
                logger.error(
                    f"Error in subscriber {subscription.subscriber_id} "
                    f"callback: {e}",
                    exc_info=True,
                )

    def _find_matching_subscribers(self, signal: SignalPayload) -> List[Subscription]:
        """Find subscribers that match the signal."""
        matching = []
        for sub in self._subscribers:
            # Check signal type
            if signal.signal_type not in sub.signal_types:
                continue

            # Check task filter
            if sub.task_filter and sub.task_filter != signal.task_id:
                continue

            matching.append(sub)

        return matching

    def subscribe(
        self,
        subscriber_id: str,
        signal_types: Set[SignalType],
        callback: Callable[[SignalPayload], None],
        task_filter: Optional[str] = None,
    ) -> str:
        """
        Subscribe to signals.

        Args:
            subscriber_id: Unique identifier for the subscriber
            signal_types: Set of signal types to subscribe to
            callback: Function to call when matching signal is emitted
            task_filter: Optional task_id to filter signals by

        Returns:
            subscription_id for later unsubscription

        Thread-safe: Yes
        """
        with self._lock:
            subscription = Subscription(
                subscriber_id=subscriber_id,
                signal_types=signal_types,
                callback=callback,
                task_filter=task_filter,
            )
            self._subscribers.append(subscription)

            logger.debug(
                f"Added subscription for {subscriber_id} "
                f"to signals {signal_types}"
            )

            return subscriber_id

    def unsubscribe(self, subscriber_id: str) -> bool:
        """
        Unsubscribe from all signals.

        Args:
            subscriber_id: The subscription ID returned from subscribe()

        Returns:
            True if subscription was found and removed

        Thread-safe: Yes
        """
        with self._lock:
            original_count = len(self._subscribers)
            self._subscribers = [
                sub for sub in self._subscribers if sub.subscriber_id != subscriber_id
            ]
            removed = len(self._subscribers) < original_count

            if removed:
                logger.debug(f"Removed subscription {subscriber_id}")

            return removed

    def get_history(
        self,
        signal_type: Optional[SignalType] = None,
        task_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[SignalPayload]:
        """
        Get signal history with optional filtering.

        Args:
            signal_type: Filter by signal type
            task_id: Filter by task ID
            limit: Maximum number of signals to return

        Returns:
            List of matching signals (most recent first)
        """
        with self._lock:
            history = self._signal_history.copy()

        # Apply filters
        if signal_type:
            history = [s for s in history if s.signal_type == signal_type]
        if task_id:
            history = [s for s in history if s.task_id == task_id]

        # Return most recent first
        return list(reversed(history[-limit:]))

    def clear_history(self) -> None:
        """Clear signal history. Thread-safe: Yes"""
        with self._lock:
            self._signal_history.clear()
            logger.debug("Cleared signal history")


# Global signal emitter instance (singleton pattern)
_global_emitter: Optional[SignalEmitter] = None
_global_emitter_lock = threading.Lock()


def get_global_emitter() -> SignalEmitter:
    """
    Get or create the global signal emitter instance.

    Returns:
        The singleton SignalEmitter instance

    Thread-safe: Yes
    """
    global _global_emitter

    if _global_emitter is None:
        with _global_emitter_lock:
            if _global_emitter is None:
                _global_emitter = SignalEmitter()
                logger.info("Initialized global signal emitter")

    return _global_emitter


def reset_global_emitter() -> None:
    """
    Reset the global emitter (primarily for testing).

    Thread-safe: Yes
    """
    global _global_emitter

    with _global_emitter_lock:
        _global_emitter = None
        logger.debug("Reset global signal emitter")
