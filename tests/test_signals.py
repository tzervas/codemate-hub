"""
Tests for Signal Emitter/Consumer System

Tests the pub-sub signal system for task orchestration including:
- Signal emission and consumption
- Subscriber management
- Signal filtering
- Thread safety
- Signal history
"""

import time
from datetime import datetime
from typing import List

import pytest

from src.signals import (
    SignalEmitter,
    SignalPayload,
    SignalType,
    TaskStatus,
    get_global_emitter,
    reset_global_emitter,
)


class TestSignalEmitter:
    """Test signal emitter functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.emitter = SignalEmitter()
        self.received_signals: List[SignalPayload] = []

    def callback(self, signal: SignalPayload):
        """Test callback that stores received signals."""
        self.received_signals.append(signal)

    def test_emit_and_receive_signal(self):
        """Test basic signal emission and reception."""
        # Subscribe to task completion signals
        self.emitter.subscribe(
            subscriber_id="test_sub",
            signal_types={SignalType.TASK_COMPLETED},
            callback=self.callback,
        )

        # Emit a signal
        signal = SignalPayload(
            signal_type=SignalType.TASK_COMPLETED,
            task_id="task1",
            agent_id="agent1",
            data={"result": "success"},
        )
        self.emitter.emit(signal)

        # Verify signal was received
        assert len(self.received_signals) == 1
        assert self.received_signals[0].task_id == "task1"
        assert self.received_signals[0].signal_type == SignalType.TASK_COMPLETED

    def test_multiple_subscribers(self):
        """Test multiple subscribers receiving the same signal."""
        received1: List[SignalPayload] = []
        received2: List[SignalPayload] = []

        self.emitter.subscribe(
            subscriber_id="sub1",
            signal_types={SignalType.TASK_STARTED},
            callback=lambda s: received1.append(s),
        )

        self.emitter.subscribe(
            subscriber_id="sub2",
            signal_types={SignalType.TASK_STARTED},
            callback=lambda s: received2.append(s),
        )

        # Emit signal
        signal = SignalPayload(
            signal_type=SignalType.TASK_STARTED,
            task_id="task1",
        )
        self.emitter.emit(signal)

        # Both should receive
        assert len(received1) == 1
        assert len(received2) == 1

    def test_signal_type_filtering(self):
        """Test that subscribers only receive matching signal types."""
        # Subscribe to COMPLETED only
        self.emitter.subscribe(
            subscriber_id="test_sub",
            signal_types={SignalType.TASK_COMPLETED},
            callback=self.callback,
        )

        # Emit different signal types
        self.emitter.emit(
            SignalPayload(signal_type=SignalType.TASK_STARTED, task_id="task1")
        )
        self.emitter.emit(
            SignalPayload(signal_type=SignalType.TASK_COMPLETED, task_id="task2")
        )
        self.emitter.emit(
            SignalPayload(signal_type=SignalType.TASK_FAILED, task_id="task3")
        )

        # Should only receive COMPLETED
        assert len(self.received_signals) == 1
        assert self.received_signals[0].signal_type == SignalType.TASK_COMPLETED

    def test_task_id_filtering(self):
        """Test filtering signals by task_id."""
        # Subscribe with task filter
        self.emitter.subscribe(
            subscriber_id="test_sub",
            signal_types={SignalType.TASK_COMPLETED},
            callback=self.callback,
            task_filter="task2",  # Only task2
        )

        # Emit signals for different tasks
        self.emitter.emit(
            SignalPayload(signal_type=SignalType.TASK_COMPLETED, task_id="task1")
        )
        self.emitter.emit(
            SignalPayload(signal_type=SignalType.TASK_COMPLETED, task_id="task2")
        )
        self.emitter.emit(
            SignalPayload(signal_type=SignalType.TASK_COMPLETED, task_id="task3")
        )

        # Should only receive task2
        assert len(self.received_signals) == 1
        assert self.received_signals[0].task_id == "task2"

    def test_unsubscribe(self):
        """Test unsubscribing from signals."""
        # Subscribe
        self.emitter.subscribe(
            subscriber_id="test_sub",
            signal_types={SignalType.TASK_COMPLETED},
            callback=self.callback,
        )

        # Emit signal - should receive
        self.emitter.emit(
            SignalPayload(signal_type=SignalType.TASK_COMPLETED, task_id="task1")
        )
        assert len(self.received_signals) == 1

        # Unsubscribe
        removed = self.emitter.unsubscribe("test_sub")
        assert removed is True

        # Emit another signal - should NOT receive
        self.emitter.emit(
            SignalPayload(signal_type=SignalType.TASK_COMPLETED, task_id="task2")
        )
        assert len(self.received_signals) == 1  # Still only 1

    def test_signal_history(self):
        """Test signal history tracking."""
        # Emit some signals
        for i in range(5):
            self.emitter.emit(
                SignalPayload(
                    signal_type=SignalType.TASK_COMPLETED,
                    task_id=f"task{i}",
                )
            )

        # Get history
        history = self.emitter.get_history()
        assert len(history) == 5

        # Most recent should be first
        assert history[0].task_id == "task4"

    def test_signal_history_filtering(self):
        """Test filtering signal history."""
        # Emit different signal types
        self.emitter.emit(
            SignalPayload(signal_type=SignalType.TASK_STARTED, task_id="task1")
        )
        self.emitter.emit(
            SignalPayload(signal_type=SignalType.TASK_COMPLETED, task_id="task1")
        )
        self.emitter.emit(
            SignalPayload(signal_type=SignalType.TASK_STARTED, task_id="task2")
        )

        # Filter by signal type
        started = self.emitter.get_history(signal_type=SignalType.TASK_STARTED)
        assert len(started) == 2

        # Filter by task_id
        task1 = self.emitter.get_history(task_id="task1")
        assert len(task1) == 2

    def test_signal_history_limit(self):
        """Test signal history size limit."""
        # Set small max history
        self.emitter._max_history = 10

        # Emit more signals than limit
        for i in range(20):
            self.emitter.emit(
                SignalPayload(
                    signal_type=SignalType.TASK_COMPLETED,
                    task_id=f"task{i}",
                )
            )

        # Should only keep last 10
        assert len(self.emitter._signal_history) == 10

        # Should be most recent
        history = self.emitter.get_history(limit=100)
        assert history[0].task_id == "task19"

    def test_clear_history(self):
        """Test clearing signal history."""
        # Emit signals
        for i in range(3):
            self.emitter.emit(
                SignalPayload(signal_type=SignalType.TASK_COMPLETED, task_id=f"task{i}")
            )

        assert len(self.emitter.get_history()) == 3

        # Clear
        self.emitter.clear_history()
        assert len(self.emitter.get_history()) == 0

    def test_callback_exception_handling(self):
        """Test that exceptions in callbacks don't break emitter."""

        def bad_callback(signal: SignalPayload):
            raise ValueError("Callback error")

        self.emitter.subscribe(
            subscriber_id="bad_sub",
            signal_types={SignalType.TASK_COMPLETED},
            callback=bad_callback,
        )

        self.emitter.subscribe(
            subscriber_id="good_sub",
            signal_types={SignalType.TASK_COMPLETED},
            callback=self.callback,
        )

        # Emit signal - should handle bad callback gracefully
        self.emitter.emit(
            SignalPayload(signal_type=SignalType.TASK_COMPLETED, task_id="task1")
        )

        # Good callback should still receive
        assert len(self.received_signals) == 1


class TestGlobalEmitter:
    """Test global emitter singleton."""

    def setup_method(self):
        """Reset global emitter before each test."""
        reset_global_emitter()

    def test_get_global_emitter(self):
        """Test getting global emitter instance."""
        emitter1 = get_global_emitter()
        emitter2 = get_global_emitter()

        # Should be same instance
        assert emitter1 is emitter2

    def test_reset_global_emitter(self):
        """Test resetting global emitter."""
        emitter1 = get_global_emitter()
        reset_global_emitter()
        emitter2 = get_global_emitter()

        # Should be different instances
        assert emitter1 is not emitter2


class TestSignalPayload:
    """Test signal payload structure."""

    def test_signal_payload_creation(self):
        """Test creating signal payload."""
        payload = SignalPayload(
            signal_type=SignalType.TASK_COMPLETED,
            task_id="task1",
            agent_id="agent1",
            data={"result": "success"},
        )

        assert payload.task_id == "task1"
        assert payload.agent_id == "agent1"
        assert payload.signal_type == SignalType.TASK_COMPLETED
        assert payload.data["result"] == "success"
        assert payload.signal_id is not None
        assert payload.timestamp is not None

    def test_signal_payload_defaults(self):
        """Test signal payload default values."""
        payload = SignalPayload(
            signal_type=SignalType.TASK_STARTED,
            task_id="task1",
        )

        assert payload.agent_id is None
        assert payload.error is None
        assert payload.data == {}

    def test_signal_payload_json_serialization(self):
        """Test that signal payload can be serialized."""
        payload = SignalPayload(
            signal_type=SignalType.TASK_COMPLETED,
            task_id="task1",
        )

        # Should be serializable via Pydantic
        json_str = payload.model_dump_json()
        assert "task1" in json_str
        assert "task_completed" in json_str
