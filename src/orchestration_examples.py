"""
Example Usage of Signal-Based Agent Orchestration System

This module demonstrates how to use the signal-based orchestration system
for coordinating multiple agent tasks with parallel and sequential execution.

Examples included:
1. Simple sequential task execution
2. Parallel task execution
3. Task dependencies
4. Agent-based task execution
5. Real-world workflow (the next 3 immediate tasks)
"""

import logging
import time
from typing import Any

from src.agents import Agent, AgentPool, create_agent_from_persona, load_personas_from_yaml
from src.orchestrator import TaskOrchestrator
from src.signals import SignalPayload, SignalType, get_global_emitter
from src.task_manager import TaskExecutionMode, TaskPriority


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def example_1_sequential_tasks():
    """Example 1: Simple sequential task execution."""
    logger.info("=" * 60)
    logger.info("Example 1: Sequential Task Execution")
    logger.info("=" * 60)

    orchestrator = TaskOrchestrator(max_parallel_tasks=2)

    # Define simple tasks
    def task1():
        logger.info("  Executing Task 1: Infrastructure check")
        time.sleep(0.1)
        return {"status": "infrastructure_ok"}

    def task2():
        logger.info("  Executing Task 2: Model validation")
        time.sleep(0.1)
        return {"status": "models_ok"}

    def task3():
        logger.info("  Executing Task 3: Pipeline test")
        time.sleep(0.1)
        return {"status": "pipeline_ok"}

    # Create tasks
    task1_id = orchestrator.create_task(name="Infrastructure", task_func=task1)
    task2_id = orchestrator.create_task(name="Models", task_func=task2)
    task3_id = orchestrator.create_task(name="Pipeline", task_func=task3)

    # Execute sequentially
    results = orchestrator.execute_tasks_sequential([task1_id, task2_id, task3_id])

    logger.info(f"Results: {results}")
    orchestrator.shutdown()


def example_2_parallel_tasks():
    """Example 2: Parallel task execution."""
    logger.info("=" * 60)
    logger.info("Example 2: Parallel Task Execution")
    logger.info("=" * 60)

    orchestrator = TaskOrchestrator(max_parallel_tasks=4)

    # Define tasks that can run in parallel
    def langflow_task():
        logger.info("  Creating Langflow flows...")
        time.sleep(0.2)
        return {"flows_created": 3}

    def enclave_task():
        logger.info("  Setting up Zephyr enclaves...")
        time.sleep(0.2)
        return {"enclaves_ready": True}

    def devux_task():
        logger.info("  Configuring dev environment...")
        time.sleep(0.2)
        return {"workspace_ready": True}

    # Create tasks
    task_ids = []
    task_ids.append(
        orchestrator.create_task(
            name="Langflow Setup",
            task_func=langflow_task,
            execution_mode=TaskExecutionMode.PARALLEL,
        )
    )
    task_ids.append(
        orchestrator.create_task(
            name="Enclave Setup",
            task_func=enclave_task,
            execution_mode=TaskExecutionMode.PARALLEL,
        )
    )
    task_ids.append(
        orchestrator.create_task(
            name="DevUX Setup",
            task_func=devux_task,
            execution_mode=TaskExecutionMode.PARALLEL,
        )
    )

    # Execute in parallel
    start_time = time.time()
    results = orchestrator.execute_tasks_parallel(task_ids)
    duration = time.time() - start_time

    logger.info(f"Completed in {duration:.2f}s (parallel execution)")
    logger.info(f"Results: {results}")
    orchestrator.shutdown()


def example_3_task_dependencies():
    """Example 3: Task execution with dependencies."""
    logger.info("=" * 60)
    logger.info("Example 3: Task Dependencies")
    logger.info("=" * 60)

    orchestrator = TaskOrchestrator(max_parallel_tasks=2)

    # Define tasks
    def setup_env():
        logger.info("  Setting up environment...")
        time.sleep(0.1)
        return {"env": "ready"}

    def pull_models():
        logger.info("  Pulling models...")
        time.sleep(0.1)
        return {"models": ["qwen2.5-coder", "mistral"]}

    def run_pipeline():
        logger.info("  Running pipeline...")
        time.sleep(0.1)
        return {"pipeline": "success"}

    # Create tasks with dependencies
    env_id = orchestrator.create_task(name="Setup Environment", task_func=setup_env)

    models_id = orchestrator.create_task(
        name="Pull Models",
        task_func=pull_models,
        dependencies={env_id},  # Depends on environment
    )

    pipeline_id = orchestrator.create_task(
        name="Run Pipeline",
        task_func=run_pipeline,
        dependencies={env_id, models_id},  # Depends on both
        priority=TaskPriority.HIGH,
    )

    # Execute tasks respecting dependencies
    orchestrator.execute_task(env_id)
    orchestrator.execute_task(models_id)
    orchestrator.execute_task(pipeline_id)

    logger.info("All tasks completed with dependencies resolved")
    orchestrator.shutdown()


def example_4_agent_based_execution():
    """Example 4: Agent-based task execution."""
    logger.info("=" * 60)
    logger.info("Example 4: Agent-Based Task Execution")
    logger.info("=" * 60)

    orchestrator = TaskOrchestrator(max_parallel_tasks=2)
    agent_pool = AgentPool()

    # Load personas from YAML
    personas = load_personas_from_yaml("personas.yaml")

    # Create agents from personas
    def python_work():
        logger.info("  [Python Specialist] Implementing Python tasks...")
        time.sleep(0.1)
        return {"code": "generated"}

    def review_work():
        logger.info("  [Quality Assessor] Reviewing outputs...")
        time.sleep(0.1)
        return {"review": "approved"}

    python_agent = create_agent_from_persona("python_worker", python_work, personas)
    reviewer_agent = create_agent_from_persona("reviewer", review_work, personas)

    if python_agent:
        agent_pool.add_agent(python_agent)
    if reviewer_agent:
        agent_pool.add_agent(reviewer_agent)

    # Create tasks and assign to agents
    code_task_id = orchestrator.create_task(
        name="Write Code",
        task_func=python_work,
        agent_id=python_agent.metadata.agent_id if python_agent else None,
    )

    review_task_id = orchestrator.create_task(
        name="Review Code",
        task_func=review_work,
        agent_id=reviewer_agent.metadata.agent_id if reviewer_agent else None,
        dependencies={code_task_id},
    )

    # Execute tasks
    orchestrator.execute_task(code_task_id)
    orchestrator.execute_task(review_task_id)

    # Show agent stats
    stats = agent_pool.get_pool_stats()
    logger.info(f"Agent Pool Stats: {stats}")

    orchestrator.shutdown()


def example_5_next_three_tasks():
    """
    Example 5: Real-world workflow for the next 3 immediate tasks.

    Based on the analysis:
    - Task 04: Langflow flows
    - Task 05: Enclaves/Zephyr
    - Task 06: Dev UX & automation

    These can be executed in parallel since they're independent.
    """
    logger.info("=" * 60)
    logger.info("Example 5: Next 3 Immediate Tasks (Parallel)")
    logger.info("=" * 60)

    orchestrator = TaskOrchestrator(max_parallel_tasks=4)

    # Subscribe to task completion signals for monitoring
    completed_tasks = []

    def on_task_completed(signal: SignalPayload):
        completed_tasks.append(signal.task_id)
        logger.info(
            f"  ✓ Task completed: {signal.data.get('name')} "
            f"(duration: {signal.data.get('duration_seconds', 0):.2f}s)"
        )

    emitter = get_global_emitter()
    emitter.subscribe(
        subscriber_id="monitor",
        signal_types={SignalType.TASK_COMPLETED},
        callback=on_task_completed,
    )

    # Task 04: Langflow flows
    def task_04_langflow():
        logger.info("  [Task 04] Creating Langflow flows...")
        # Subtasks:
        # - Inspect langflow container config
        # - Create example flows
        # - Document flow patterns
        time.sleep(0.3)
        return {
            "status": "complete",
            "flows": ["code_review_flow", "task_decomposition_flow"],
            "db_path": "./langflow_data/langflow.db",
        }

    # Task 05: Enclaves/Zephyr
    def task_05_enclaves():
        logger.info("  [Task 05] Setting up Zephyr enclaves...")
        # Subtasks:
        # - Inspect zephyr/core and zephyr/exec
        # - Add example enclave
        # - Add tests for isolation
        time.sleep(0.3)
        return {
            "status": "complete",
            "enclaves": ["example_enclave"],
            "isolation_verified": True,
        }

    # Task 06: Dev UX & automation
    def task_06_devux():
        logger.info("  [Task 06] Polishing development environment...")
        # Subtasks:
        # - Polish code-server workspace
        # - Update documentation
        # - Improve scripts
        time.sleep(0.3)
        return {
            "status": "complete",
            "workspace_ready": True,
            "scripts_updated": ["build.sh", "deploy.sh"],
        }

    # Create tasks with high priority
    task_04_id = orchestrator.create_task(
        name="Task 04: Langflow",
        task_func=task_04_langflow,
        description="Create reproducible flows for common tasks",
        priority=TaskPriority.HIGH,
        execution_mode=TaskExecutionMode.PARALLEL,
        metadata={"tracker": "trackers/tasks/04-langflow.md"},
    )

    task_05_id = orchestrator.create_task(
        name="Task 05: Enclaves",
        task_func=task_05_enclaves,
        description="Test and integrate Zephyr enclaves",
        priority=TaskPriority.HIGH,
        execution_mode=TaskExecutionMode.PARALLEL,
        metadata={"tracker": "trackers/tasks/05-enclaves-zephyr.md"},
    )

    task_06_id = orchestrator.create_task(
        name="Task 06: Dev UX",
        task_func=task_06_devux,
        description="Polish development experience and automation",
        priority=TaskPriority.HIGH,
        execution_mode=TaskExecutionMode.PARALLEL,
        metadata={"tracker": "trackers/tasks/06-dev-ux.md"},
    )

    # Execute all three tasks in parallel
    logger.info("\nStarting parallel execution of next 3 tasks...")
    start_time = time.time()

    results = orchestrator.execute_tasks_parallel([task_04_id, task_05_id, task_06_id])

    duration = time.time() - start_time

    logger.info(f"\n✓ All 3 tasks completed in {duration:.2f}s")
    logger.info(f"Task 04 result: {results.get(task_04_id)}")
    logger.info(f"Task 05 result: {results.get(task_05_id)}")
    logger.info(f"Task 06 result: {results.get(task_06_id)}")

    orchestrator.shutdown()


def main():
    """Run all examples."""
    logger.info("\n" + "=" * 60)
    logger.info("Signal-Based Agent Orchestration Examples")
    logger.info("=" * 60 + "\n")

    # Run examples
    example_1_sequential_tasks()
    print()

    example_2_parallel_tasks()
    print()

    example_3_task_dependencies()
    print()

    example_4_agent_based_execution()
    print()

    example_5_next_three_tasks()

    logger.info("\n" + "=" * 60)
    logger.info("All examples completed!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
