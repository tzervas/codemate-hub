"""
Tests for Task Orchestrator

Tests the task orchestration system including:
- Task creation and execution
- Parallel and sequential execution
- Dependency resolution
- Signal integration
- Error handling
"""

import time
from typing import List

import pytest

from src.orchestrator import TaskExecutor, TaskOrchestrator
from src.signals import SignalPayload, SignalType, reset_global_emitter
from src.task_manager import TaskExecutionMode, TaskPriority


class TestTaskOrchestrator:
    """Test task orchestrator functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        reset_global_emitter()
        self.orchestrator = TaskOrchestrator(max_parallel_tasks=4)
        self.execution_order: List[str] = []

    def teardown_method(self):
        """Cleanup after tests."""
        self.orchestrator.shutdown()

    def make_task_func(self, task_name: str, delay: float = 0.0):
        """Create a test task function."""

        def task_func():
            self.execution_order.append(task_name)
            if delay:
                time.sleep(delay)
            return f"result_{task_name}"

        return task_func

    def test_create_task(self):
        """Test creating a task."""
        task_id = self.orchestrator.create_task(
            name="test_task",
            task_func=lambda: "result",
            description="Test task",
        )

        assert task_id is not None

        # Verify task was created
        task = self.orchestrator._task_manager.get_task(task_id)
        assert task is not None
        assert task.name == "test_task"

    def test_execute_single_task(self):
        """Test executing a single task."""
        task_id = self.orchestrator.create_task(
            name="task1",
            task_func=self.make_task_func("task1"),
        )

        result = self.orchestrator.execute_task(task_id)

        assert result == "result_task1"
        assert "task1" in self.execution_order

        # Verify task status
        status = self.orchestrator.get_task_status(task_id)
        from src.signals import TaskStatus

        assert status == TaskStatus.COMPLETED

    def test_execute_tasks_sequential(self):
        """Test executing tasks sequentially."""
        task_ids = []
        for i in range(3):
            task_id = self.orchestrator.create_task(
                name=f"task{i}",
                task_func=self.make_task_func(f"task{i}", delay=0.01),
            )
            task_ids.append(task_id)

        results = self.orchestrator.execute_tasks_sequential(task_ids)

        # All should complete
        assert len(results) == 3

        # Should execute in order
        assert self.execution_order == ["task0", "task1", "task2"]

    def test_execute_tasks_parallel(self):
        """Test executing tasks in parallel."""
        task_ids = []
        for i in range(3):
            task_id = self.orchestrator.create_task(
                name=f"task{i}",
                task_func=self.make_task_func(f"task{i}", delay=0.05),
            )
            task_ids.append(task_id)

        start_time = time.time()
        results = self.orchestrator.execute_tasks_parallel(task_ids)
        duration = time.time() - start_time

        # All should complete
        assert len(results) == 3

        # Should complete faster than sequential (3 * 0.05 = 0.15s)
        # Parallel should be closer to 0.05s
        assert duration < 0.12  # Some overhead, but much faster than 0.15

        # All tasks should have executed (order may vary)
        assert set(self.execution_order) == {"task0", "task1", "task2"}

    def test_task_with_dependencies(self):
        """Test task dependency resolution."""
        # Create tasks with dependencies
        task1_id = self.orchestrator.create_task(
            name="task1",
            task_func=self.make_task_func("task1"),
        )

        task2_id = self.orchestrator.create_task(
            name="task2",
            task_func=self.make_task_func("task2"),
            dependencies={task1_id},  # task2 depends on task1
        )

        # task2 should not be ready yet
        ready_tasks = self.orchestrator._task_manager.get_ready_tasks()
        ready_ids = [t.task_id for t in ready_tasks]
        assert task1_id in ready_ids
        assert task2_id not in ready_ids

        # Execute task1
        self.orchestrator.execute_task(task1_id)

        # Now task2 should be ready
        ready_tasks = self.orchestrator._task_manager.get_ready_tasks()
        ready_ids = [t.task_id for t in ready_tasks]
        assert task2_id in ready_ids

        # Execute task2
        self.orchestrator.execute_task(task2_id)

        # Check execution order
        assert self.execution_order == ["task1", "task2"]

    def test_task_with_args_and_kwargs(self):
        """Test task execution with arguments."""

        def task_with_args(x, y, z=0):
            return x + y + z

        task_id = self.orchestrator.create_task(
            name="task_args",
            task_func=task_with_args,
            args=(10, 20),
            kwargs={"z": 5},
        )

        result = self.orchestrator.execute_task(task_id)
        assert result == 35

    def test_task_priority_ordering(self):
        """Test that tasks are ordered by priority."""
        # Create tasks with different priorities
        low_id = self.orchestrator.create_task(
            name="low",
            task_func=lambda: "low",
            priority=TaskPriority.LOW,
        )

        high_id = self.orchestrator.create_task(
            name="high",
            task_func=lambda: "high",
            priority=TaskPriority.HIGH,
        )

        normal_id = self.orchestrator.create_task(
            name="normal",
            task_func=lambda: "normal",
            priority=TaskPriority.NORMAL,
        )

        # Get ready tasks - should be ordered by priority
        ready_tasks = self.orchestrator._task_manager.get_ready_tasks()
        ready_ids = [t.task_id for t in ready_tasks]

        # High should be first
        assert ready_ids[0] == high_id
        assert ready_ids[2] == low_id

    def test_task_failure_handling(self):
        """Test handling task failures."""

        def failing_task():
            raise ValueError("Task failed!")

        task_id = self.orchestrator.create_task(
            name="failing_task",
            task_func=failing_task,
        )

        # Should raise exception
        with pytest.raises(ValueError, match="Task failed!"):
            self.orchestrator.execute_task(task_id)

        # Task should be marked as failed
        from src.signals import TaskStatus

        status = self.orchestrator.get_task_status(task_id)
        assert status == TaskStatus.FAILED

    def test_sequential_stops_on_failure(self):
        """Test that sequential execution stops on first failure."""

        def failing_task():
            raise ValueError("Failed")

        task1_id = self.orchestrator.create_task(
            name="task1",
            task_func=self.make_task_func("task1"),
        )

        task2_id = self.orchestrator.create_task(
            name="task2",
            task_func=failing_task,
        )

        task3_id = self.orchestrator.create_task(
            name="task3",
            task_func=self.make_task_func("task3"),
        )

        results = self.orchestrator.execute_tasks_sequential(
            [task1_id, task2_id, task3_id]
        )

        # Only task1 should have completed
        assert "task1" in self.execution_order
        assert "task3" not in self.execution_order

    def test_parent_child_tasks(self):
        """Test parent-child task relationships."""
        # Create parent task
        parent_id = self.orchestrator.create_task(
            name="parent",
            task_func=lambda: "parent_result",
        )

        # Create child tasks
        child1_id = self.orchestrator.create_task(
            name="child1",
            task_func=self.make_task_func("child1"),
            parent_task_id=parent_id,
        )

        child2_id = self.orchestrator.create_task(
            name="child2",
            task_func=self.make_task_func("child2"),
            parent_task_id=parent_id,
        )

        # Execute task group
        results = self.orchestrator.execute_task_group(
            parent_id, mode=TaskExecutionMode.SEQUENTIAL
        )

        assert len(results) == 2
        assert "child1" in self.execution_order
        assert "child2" in self.execution_order

    def test_signal_emission_on_task_completion(self):
        """Test that signals are emitted when tasks complete."""
        received_signals: List[SignalPayload] = []

        def signal_callback(signal: SignalPayload):
            received_signals.append(signal)

        # Subscribe to task signals
        from src.signals import get_global_emitter

        emitter = get_global_emitter()
        emitter.subscribe(
            subscriber_id="test_observer",
            signal_types={SignalType.TASK_STARTED, SignalType.TASK_COMPLETED},
            callback=signal_callback,
        )

        # Execute a task
        task_id = self.orchestrator.create_task(
            name="test_task",
            task_func=lambda: "result",
        )
        self.orchestrator.execute_task(task_id)

        # Should receive STARTED and COMPLETED signals
        assert len(received_signals) >= 2

        signal_types = [s.signal_type for s in received_signals]
        assert SignalType.TASK_STARTED in signal_types
        assert SignalType.TASK_COMPLETED in signal_types

    def test_get_all_tasks(self):
        """Test getting all tasks."""
        # Create some tasks
        for i in range(3):
            self.orchestrator.create_task(
                name=f"task{i}",
                task_func=lambda: "result",
            )

        all_tasks = self.orchestrator.get_all_tasks()
        assert len(all_tasks) == 3


class TestTaskExecutor:
    """Test task executor functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        from src.task_manager import TaskManager

        reset_global_emitter()
        self.task_manager = TaskManager()
        self.executor = TaskExecutor(self.task_manager)

    def test_execute_task_lifecycle(self):
        """Test complete task execution lifecycle."""
        # Create a task
        task_id = self.task_manager.create_task(
            name="test_task",
            description="Test task",
        )

        def task_func():
            return "success"

        # Execute
        result = self.executor.execute_task(task_id, task_func)

        assert result == "success"

        # Check task was started and completed
        task = self.task_manager.get_task(task_id)
        from src.signals import TaskStatus

        assert task.status == TaskStatus.COMPLETED
        assert task.started_at is not None
        assert task.completed_at is not None

    def test_execute_task_failure(self):
        """Test task execution failure handling."""
        task_id = self.task_manager.create_task(name="failing_task")

        def failing_func():
            raise RuntimeError("Execution failed")

        with pytest.raises(RuntimeError):
            self.executor.execute_task(task_id, failing_func)

        # Task should be marked as failed
        task = self.task_manager.get_task(task_id)
        from src.signals import TaskStatus

        assert task.status == TaskStatus.FAILED
        assert task.error is not None
