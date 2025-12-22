# Signal-Based Agent Orchestration System

## Overview

The signal-based agent orchestration system provides event-driven coordination for multiple agent tasks with support for parallel and sequential execution, dependency resolution, and comprehensive state management.

## Architecture

### Core Components

1. **Signal System** (`src/signals.py`)
   - Pub-sub signal emitter/consumer
   - Thread-safe event handling
   - Signal history tracking
   - Type-safe payloads with Pydantic

2. **Task Manager** (`src/task_manager.py`)
   - Task lifecycle management
   - State tracking (pending, running, completed, failed)
   - Dependency resolution
   - Priority-based scheduling

3. **Orchestrator** (`src/orchestrator.py`)
   - Event-driven task coordination
   - Parallel and sequential execution
   - Thread pool management
   - Automatic dependency resolution

4. **Agent System** (`src/agents.py`)
   - Agent abstraction layer
   - Agent pool management
   - Integration with personas.yaml
   - Agent state tracking

## Quick Start

### Basic Sequential Execution

```python
from src.orchestrator import TaskOrchestrator

orchestrator = TaskOrchestrator(max_parallel_tasks=4)

# Define tasks
def task1():
    return "result1"

def task2():
    return "result2"

# Create tasks
task1_id = orchestrator.create_task(name="Task 1", task_func=task1)
task2_id = orchestrator.create_task(name="Task 2", task_func=task2)

# Execute sequentially
results = orchestrator.execute_tasks_sequential([task1_id, task2_id])
```

### Parallel Execution

```python
# Execute tasks in parallel
results = orchestrator.execute_tasks_parallel([task1_id, task2_id, task3_id])
```

### Task Dependencies

```python
# Create tasks with dependencies
base_id = orchestrator.create_task(name="Base Task", task_func=base_func)

dependent_id = orchestrator.create_task(
    name="Dependent Task",
    task_func=dependent_func,
    dependencies={base_id}  # Will only run after base_id completes
)

# Execute - orchestrator handles dependency order
orchestrator.execute_task(base_id)
orchestrator.execute_task(dependent_id)
```

### Agent-Based Execution

```python
from src.agents import create_agent_from_persona, AgentPool, load_personas_from_yaml

# Load personas
personas = load_personas_from_yaml("personas.yaml")

# Create agents
def python_work():
    return "python code"

python_agent = create_agent_from_persona("python_worker", python_work, personas)

# Create agent pool
pool = AgentPool()
pool.add_agent(python_agent)

# Create task assigned to agent
task_id = orchestrator.create_task(
    name="Python Task",
    task_func=python_work,
    agent_id=python_agent.metadata.agent_id
)
```

## Signal System

### Signal Types

- `TASK_STARTED` - Task execution begins
- `TASK_COMPLETED` - Task completes successfully
- `TASK_FAILED` - Task fails with error
- `TASK_CANCELLED` - Task is cancelled
- `AGENT_READY` - Agent becomes available
- `AGENT_BUSY` - Agent starts working

### Subscribing to Signals

```python
from src.signals import get_global_emitter, SignalType

def on_task_complete(signal):
    print(f"Task {signal.task_id} completed!")

emitter = get_global_emitter()
emitter.subscribe(
    subscriber_id="my_observer",
    signal_types={SignalType.TASK_COMPLETED},
    callback=on_task_complete
)
```

## Real-World Example: Next 3 Tasks

See `src/orchestration_examples.py` for a complete demonstration of coordinating the next 3 immediate project tasks (Langflow, Enclaves, Dev UX) in parallel.

## Testing

```bash
# Test signal system
python -m pytest tests/test_signals.py -v

# Test orchestrator
python -m pytest tests/test_orchestrator.py -v

# Run examples
python -m src.orchestration_examples
```

## API Reference

### TaskOrchestrator

- `create_task(...)` - Create a new task
- `execute_task(task_id)` - Execute single task
- `execute_tasks_parallel(task_ids)` - Execute tasks concurrently
- `execute_tasks_sequential(task_ids)` - Execute tasks in order
- `shutdown()` - Clean up resources

### SignalEmitter

- `emit(signal)` - Emit signal to subscribers
- `subscribe(...)` - Subscribe to signal types
- `unsubscribe(subscriber_id)` - Remove subscription

## Best Practices

1. Use dependencies for task ordering
2. Choose appropriate execution modes (parallel vs sequential)
3. Set task priorities appropriately
4. Subscribe to signals for monitoring
5. Handle errors gracefully
6. Always call `orchestrator.shutdown()` when done

For complete documentation, see full examples in `src/orchestration_examples.py`.
