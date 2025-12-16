"""
Task Orchestrator for Agent Coordination

This module provides the main orchestration logic for coordinating multiple
agent tasks using a signal-based event-driven approach.

Key Features:
- Event-driven task coordination using signals
- Support for parallel and sequential task execution
- Automatic dependency resolution
- Agent pool management
- Graceful error handling and task retry
"""

import logging
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Set

from src.signals import (
    SignalPayload,
    SignalType,
    TaskStatus,
    get_global_emitter,
)
from src.task_manager import (
    TaskExecutionMode,
    TaskManager,
    TaskMetadata,
    TaskPriority,
)


logger = logging.getLogger(__name__)


class TaskExecutor:
    """Executes individual tasks with proper signal emission."""

    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager

    def execute_task(
        self,
        task_id: str,
        task_func: Callable[..., Any],
        *args,
        **kwargs,
    ) -> Any:
        """
        Execute a task function with proper lifecycle management.

        Args:
            task_id: Task identifier
            task_func: Function to execute for this task
            *args: Positional arguments for task function
            **kwargs: Keyword arguments for task function

        Returns:
            Result from task function

        Raises:
            Exception: If task function raises an exception
        """
        task = self.task_manager.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        logger.info(f"Executing task {task_id} ({task.name})")

        try:
            # Start task
            self.task_manager.start_task(task_id)

            # Execute
            result = task_func(*args, **kwargs)

            # Complete task
            self.task_manager.complete_task(task_id, result=result)

            return result

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            self.task_manager.fail_task(task_id, error=str(e))
            raise


class TaskOrchestrator:
    """
    Orchestrates multiple agent tasks with signal-based coordination.

    This class manages task execution, dependency resolution, and agent
    coordination using an event-driven approach with signals.
    """

    def __init__(
        self,
        max_parallel_tasks: int = 4,
        task_manager: Optional[TaskManager] = None,
    ):
        """
        Initialize task orchestrator.

        Args:
            max_parallel_tasks: Maximum number of tasks to execute in parallel
            task_manager: Optional TaskManager instance
        """
        self._max_parallel = max_parallel_tasks
        self._task_manager = task_manager or TaskManager()
        self._executor = TaskExecutor(self._task_manager)
        self._emitter = get_global_emitter()

        # Thread pool for parallel execution
        self._thread_pool = ThreadPoolExecutor(max_workers=max_parallel_tasks)

        # Track futures for parallel tasks
        self._futures: Dict[str, Future] = {}
        self._futures_lock = threading.Lock()

        # Subscribe to task completion signals
        self._setup_signal_handlers()

        logger.info(
            f"Initialized TaskOrchestrator with {max_parallel_tasks} parallel workers"
        )

    def _setup_signal_handlers(self):
        """Setup signal handlers for task lifecycle events."""

        def on_task_completed(signal: SignalPayload):
            """Handle task completion signal."""
            logger.debug(f"Received completion signal for task {signal.task_id}")
            # Trigger next tasks if dependencies are met
            self._check_and_start_dependent_tasks(signal.task_id)

        def on_task_failed(signal: SignalPayload):
            """Handle task failure signal."""
            logger.warning(
                f"Task {signal.task_id} failed: {signal.error}"
            )
            # Could implement retry logic here

        # Subscribe to completion and failure signals
        self._emitter.subscribe(
            subscriber_id="orchestrator_completion",
            signal_types={SignalType.TASK_COMPLETED},
            callback=on_task_completed,
        )

        self._emitter.subscribe(
            subscriber_id="orchestrator_failure",
            signal_types={SignalType.TASK_FAILED},
            callback=on_task_failed,
        )

    def _check_and_start_dependent_tasks(self, completed_task_id: str):
        """Check if any tasks became ready after a task completed."""
        ready_tasks = self._task_manager.get_ready_tasks()
        if ready_tasks:
            logger.info(
                f"Found {len(ready_tasks)} ready tasks after {completed_task_id} completed"
            )
            # Auto-start ready tasks if orchestrator is running
            # (Implementation depends on orchestrator mode)

    def create_task(
        self,
        name: str,
        task_func: Callable[..., Any],
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        description: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        agent_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        dependencies: Optional[Set[str]] = None,
        execution_mode: TaskExecutionMode = TaskExecutionMode.SEQUENTIAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new task with associated execution function.

        Args:
            name: Task name
            task_func: Function to execute for this task
            args: Positional arguments for task function
            kwargs: Keyword arguments for task function
            description: Task description
            priority: Task priority
            agent_id: Agent assigned to task
            parent_task_id: Parent task ID (for subtasks)
            dependencies: Task IDs that must complete first
            execution_mode: Sequential or parallel
            metadata: Additional metadata

        Returns:
            task_id: Created task identifier
        """
        task_id = self._task_manager.create_task(
            name=name,
            description=description,
            priority=priority,
            agent_id=agent_id,
            parent_task_id=parent_task_id,
            dependencies=dependencies,
            execution_mode=execution_mode,
            metadata=metadata or {},
        )

        # Store task function and args in metadata
        task = self._task_manager.get_task(task_id)
        if task:
            task.metadata["_task_func"] = task_func
            task.metadata["_task_args"] = args
            task.metadata["_task_kwargs"] = kwargs or {}

        return task_id

    def execute_task(self, task_id: str) -> Any:
        """
        Execute a single task immediately.

        Args:
            task_id: Task identifier

        Returns:
            Task execution result
        """
        task = self._task_manager.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        task_func = task.metadata.get("_task_func")
        if not task_func:
            raise ValueError(f"No task function defined for {task_id}")

        args = task.metadata.get("_task_args", ())
        kwargs = task.metadata.get("_task_kwargs", {})

        return self._executor.execute_task(task_id, task_func, *args, **kwargs)

    def execute_tasks_parallel(self, task_ids: List[str]) -> Dict[str, Any]:
        """
        Execute multiple tasks in parallel.

        Args:
            task_ids: List of task identifiers to execute

        Returns:
            Dictionary mapping task_id to result
        """
        logger.info(f"Executing {len(task_ids)} tasks in parallel")

        with self._futures_lock:
            # Submit all tasks to thread pool
            for task_id in task_ids:
                task = self._task_manager.get_task(task_id)
                if not task:
                    logger.error(f"Task {task_id} not found")
                    continue

                task_func = task.metadata.get("_task_func")
                if not task_func:
                    logger.error(f"No task function for {task_id}")
                    continue

                args = task.metadata.get("_task_args", ())
                kwargs = task.metadata.get("_task_kwargs", {})

                future = self._thread_pool.submit(
                    self._executor.execute_task, task_id, task_func, *args, **kwargs
                )
                self._futures[task_id] = future

        # Wait for all tasks to complete
        results = {}
        for task_id in task_ids:
            future = self._futures.get(task_id)
            if future:
                try:
                    results[task_id] = future.result()
                except Exception as e:
                    logger.error(f"Task {task_id} raised exception: {e}")
                    results[task_id] = None

        # Clean up futures
        with self._futures_lock:
            for task_id in task_ids:
                self._futures.pop(task_id, None)

        return results

    def execute_tasks_sequential(self, task_ids: List[str]) -> Dict[str, Any]:
        """
        Execute multiple tasks sequentially.

        Args:
            task_ids: List of task identifiers to execute in order

        Returns:
            Dictionary mapping task_id to result
        """
        logger.info(f"Executing {len(task_ids)} tasks sequentially")

        results = {}
        for task_id in task_ids:
            try:
                result = self.execute_task(task_id)
                results[task_id] = result
            except Exception as e:
                logger.error(f"Task {task_id} failed, stopping sequential execution: {e}")
                # Stop on first failure in sequential mode
                break

        return results

    def execute_task_group(
        self,
        parent_task_id: str,
        mode: TaskExecutionMode = TaskExecutionMode.SEQUENTIAL,
    ) -> Dict[str, Any]:
        """
        Execute all child tasks of a parent task.

        Args:
            parent_task_id: Parent task identifier
            mode: Execution mode (parallel or sequential)

        Returns:
            Dictionary mapping child task_id to result
        """
        children = self._task_manager.get_children_tasks(parent_task_id)
        if not children:
            logger.warning(f"No child tasks found for {parent_task_id}")
            return {}

        child_ids = [c.task_id for c in children]

        if mode == TaskExecutionMode.PARALLEL:
            return self.execute_tasks_parallel(child_ids)
        else:
            return self.execute_tasks_sequential(child_ids)

    def run_until_complete(self, max_iterations: int = 100) -> None:
        """
        Run orchestrator until all pending tasks are complete.

        This continuously checks for ready tasks and executes them
        until no pending tasks remain.

        Args:
            max_iterations: Maximum number of scheduling iterations
        """
        logger.info("Starting orchestrator run-until-complete mode")

        iteration = 0
        while iteration < max_iterations:
            iteration += 1

            # Check for ready tasks
            ready_tasks = self._task_manager.get_ready_tasks()
            if not ready_tasks:
                # Check if any tasks are still running
                if not self._task_manager.has_pending_tasks():
                    logger.info("All tasks completed")
                    break

                # Wait a bit for running tasks to complete
                time.sleep(0.1)
                continue

            # Execute ready tasks
            # Group by execution mode
            parallel_tasks = [
                t for t in ready_tasks if t.execution_mode == TaskExecutionMode.PARALLEL
            ]
            sequential_tasks = [
                t for t in ready_tasks if t.execution_mode == TaskExecutionMode.SEQUENTIAL
            ]

            # Execute parallel tasks
            if parallel_tasks:
                task_ids = [t.task_id for t in parallel_tasks]
                self.execute_tasks_parallel(task_ids)

            # Execute sequential tasks
            if sequential_tasks:
                task_ids = [t.task_id for t in sequential_tasks]
                self.execute_tasks_sequential(task_ids)

        if iteration >= max_iterations:
            logger.warning(f"Reached max iterations ({max_iterations})")

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get status of a task."""
        task = self._task_manager.get_task(task_id)
        return task.status if task else None

    def get_all_tasks(self) -> List[TaskMetadata]:
        """Get all tasks."""
        return self._task_manager.get_all_tasks()

    def shutdown(self):
        """Shutdown orchestrator and cleanup resources."""
        logger.info("Shutting down orchestrator")
        self._thread_pool.shutdown(wait=True)
        self._emitter.unsubscribe("orchestrator_completion")
        self._emitter.unsubscribe("orchestrator_failure")
