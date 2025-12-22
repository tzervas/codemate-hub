"""
Task Management System for Agent Orchestration

This module provides task queue management, state tracking, and dependency
resolution for coordinating multiple agent tasks.

Key Features:
- Task state management with thread-safe updates
- Dependency tracking for sequential task execution
- Support for parallel and sequential task groups
- Task priority and scheduling
- Integration with signal system for event-driven orchestration
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from src.signals import SignalPayload, SignalType, TaskStatus, get_global_emitter


logger = logging.getLogger(__name__)


class TaskPriority(int, Enum):
    """Task execution priority levels."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskExecutionMode(str, Enum):
    """Task execution mode."""

    SEQUENTIAL = "sequential"  # Tasks execute one after another
    PARALLEL = "parallel"  # Tasks execute concurrently


@dataclass
class TaskMetadata:
    """Metadata about a task."""

    task_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    agent_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    dependencies: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Any] = None
    execution_mode: TaskExecutionMode = TaskExecutionMode.SEQUENTIAL
    metadata: Dict[str, Any] = field(default_factory=dict)

    def duration_seconds(self) -> Optional[float]:
        """Calculate task duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def is_ready(self, completed_tasks: Set[str]) -> bool:
        """Check if task is ready to execute (all dependencies met)."""
        if self.status != TaskStatus.PENDING:
            return False
        return self.dependencies.issubset(completed_tasks)


class TaskManager:
    """
    Thread-safe task manager for orchestrating agent tasks.

    This class manages task lifecycle, dependencies, and state transitions,
    integrating with the signal system to emit events.
    """

    def __init__(self, emitter=None):
        """
        Initialize task manager.

        Args:
            emitter: Optional SignalEmitter instance (uses global if not provided)
        """
        self._lock = threading.RLock()
        self._tasks: Dict[str, TaskMetadata] = {}
        self._emitter = emitter or get_global_emitter()

        # Track task relationships
        self._parent_to_children: Dict[str, List[str]] = {}
        self._dependencies_graph: Dict[str, Set[str]] = {}

    def create_task(
        self,
        name: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        agent_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        dependencies: Optional[Set[str]] = None,
        execution_mode: TaskExecutionMode = TaskExecutionMode.SEQUENTIAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new task.

        Args:
            name: Task name
            description: Task description
            priority: Task priority level
            agent_id: ID of agent assigned to this task
            parent_task_id: ID of parent task (for subtasks)
            dependencies: Set of task IDs that must complete before this task
            execution_mode: Sequential or parallel execution
            metadata: Additional task metadata

        Returns:
            task_id: The created task's unique identifier
        """
        with self._lock:
            task = TaskMetadata(
                name=name,
                description=description,
                priority=priority,
                agent_id=agent_id,
                parent_task_id=parent_task_id,
                dependencies=dependencies or set(),
                execution_mode=execution_mode,
                metadata=metadata or {},
            )

            self._tasks[task.task_id] = task

            # Track parent-child relationship
            if parent_task_id:
                if parent_task_id not in self._parent_to_children:
                    self._parent_to_children[parent_task_id] = []
                self._parent_to_children[parent_task_id].append(task.task_id)

            # Track dependencies
            if task.dependencies:
                self._dependencies_graph[task.task_id] = task.dependencies.copy()

            logger.info(
                f"Created task {task.task_id} ({name}) "
                f"with priority {priority.name} and {len(task.dependencies)} dependencies"
            )

            return task.task_id

    def start_task(self, task_id: str, agent_id: Optional[str] = None) -> bool:
        """
        Mark task as started.

        Args:
            task_id: Task identifier
            agent_id: Optional agent ID if not set during creation

        Returns:
            True if task was started successfully

        Emits:
            TASK_STARTED signal
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return False

            if task.status != TaskStatus.PENDING:
                logger.warning(
                    f"Task {task_id} cannot start from status {task.status}"
                )
                return False

            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            if agent_id:
                task.agent_id = agent_id

            logger.info(f"Started task {task_id} ({task.name}) on agent {task.agent_id}")

        # Emit signal outside lock
        self._emitter.emit(
            SignalPayload(
                signal_type=SignalType.TASK_STARTED,
                task_id=task_id,
                agent_id=task.agent_id,
                data={"name": task.name, "priority": task.priority.name},
            )
        )

        return True

    def complete_task(
        self, task_id: str, result: Optional[Any] = None
    ) -> bool:
        """
        Mark task as completed.

        Args:
            task_id: Task identifier
            result: Optional task result data

        Returns:
            True if task was completed successfully

        Emits:
            TASK_COMPLETED signal
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return False

            if task.status != TaskStatus.RUNNING:
                logger.warning(
                    f"Task {task_id} cannot complete from status {task.status}"
                )
                return False

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result

            duration = task.duration_seconds()
            logger.info(
                f"Completed task {task_id} ({task.name}) "
                f"in {duration:.2f}s" if duration else "Completed task {task_id}"
            )

        # Emit signal outside lock
        self._emitter.emit(
            SignalPayload(
                signal_type=SignalType.TASK_COMPLETED,
                task_id=task_id,
                agent_id=task.agent_id,
                data={
                    "name": task.name,
                    "result": result,
                    "duration_seconds": duration,
                },
            )
        )

        return True

    def fail_task(self, task_id: str, error: str) -> bool:
        """
        Mark task as failed.

        Args:
            task_id: Task identifier
            error: Error message or description

        Returns:
            True if task was failed successfully

        Emits:
            TASK_FAILED signal
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                logger.error(f"Task {task_id} not found")
                return False

            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.error = error

            logger.error(f"Failed task {task_id} ({task.name}): {error}")

        # Emit signal outside lock
        self._emitter.emit(
            SignalPayload(
                signal_type=SignalType.TASK_FAILED,
                task_id=task_id,
                agent_id=task.agent_id,
                error=error,
                data={"name": task.name},
            )
        )

        return True

    def get_task(self, task_id: str) -> Optional[TaskMetadata]:
        """Get task metadata."""
        with self._lock:
            task = self._tasks.get(task_id)
            return task

    def get_ready_tasks(self) -> List[TaskMetadata]:
        """
        Get all tasks that are ready to execute (dependencies met).

        Returns:
            List of tasks sorted by priority (highest first)
        """
        with self._lock:
            completed_tasks = {
                tid for tid, t in self._tasks.items() if t.status == TaskStatus.COMPLETED
            }

            ready_tasks = [
                task
                for task in self._tasks.values()
                if task.is_ready(completed_tasks)
            ]

            # Sort by priority (highest first)
            ready_tasks.sort(key=lambda t: t.priority.value, reverse=True)

            return ready_tasks

    def get_children_tasks(self, parent_task_id: str) -> List[TaskMetadata]:
        """Get all child tasks of a parent task."""
        with self._lock:
            child_ids = self._parent_to_children.get(parent_task_id, [])
            return [self._tasks[tid] for tid in child_ids if tid in self._tasks]

    def get_tasks_by_status(self, status: TaskStatus) -> List[TaskMetadata]:
        """Get all tasks with a specific status."""
        with self._lock:
            return [t for t in self._tasks.values() if t.status == status]

    def get_all_tasks(self) -> List[TaskMetadata]:
        """Get all tasks."""
        with self._lock:
            return list(self._tasks.values())

    def has_pending_tasks(self) -> bool:
        """Check if there are any pending or running tasks."""
        with self._lock:
            return any(
                t.status in {TaskStatus.PENDING, TaskStatus.RUNNING}
                for t in self._tasks.values()
            )

    def clear_tasks(self) -> None:
        """Clear all tasks (primarily for testing)."""
        with self._lock:
            self._tasks.clear()
            self._parent_to_children.clear()
            self._dependencies_graph.clear()
            logger.debug("Cleared all tasks")
