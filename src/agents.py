"""
Agent Management System for Task Execution

This module provides agent abstractions that integrate with the task
orchestration system, supporting both simple callable agents and
CrewAI-based agents.

Key Features:
- Agent abstraction with consistent interface
- Integration with CrewAI agents and personas
- Agent pool management
- Agent state tracking (ready, busy)
- Signal emission for agent lifecycle events
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional

import yaml

from src.signals import SignalPayload, SignalType, get_global_emitter


logger = logging.getLogger(__name__)


class AgentState(str, Enum):
    """Agent operational state."""

    IDLE = "idle"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class AgentMetadata:
    """Metadata about an agent."""

    agent_id: str
    name: str
    role: str
    state: AgentState = AgentState.IDLE
    current_task_id: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = None
    capabilities: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class Agent:
    """
    Base agent abstraction for task execution.

    This provides a consistent interface for different types of agents
    (simple functions, CrewAI agents, etc.)
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str,
        execute_func: Callable[..., Any],
        capabilities: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize an agent.

        Args:
            agent_id: Unique agent identifier
            name: Agent name
            role: Agent role/type
            execute_func: Function to execute tasks
            capabilities: Dict describing agent capabilities
        """
        self.metadata = AgentMetadata(
            agent_id=agent_id,
            name=name,
            role=role,
            capabilities=capabilities or {},
        )
        self._execute_func = execute_func
        self._emitter = get_global_emitter()

    def execute(self, task_id: str, *args, **kwargs) -> Any:
        """
        Execute a task.

        Args:
            task_id: Task identifier
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Task execution result
        """
        # Update state
        self.metadata.state = AgentState.BUSY
        self.metadata.current_task_id = task_id
        self.metadata.last_active = datetime.utcnow()

        # Emit agent busy signal
        self._emitter.emit(
            SignalPayload(
                signal_type=SignalType.AGENT_BUSY,
                task_id=task_id,
                agent_id=self.metadata.agent_id,
                data={"agent_name": self.metadata.name, "role": self.metadata.role},
            )
        )

        try:
            # Execute task
            result = self._execute_func(*args, **kwargs)

            # Update state on success
            self.metadata.state = AgentState.READY
            self.metadata.current_task_id = None
            self.metadata.tasks_completed += 1
            self.metadata.last_active = datetime.utcnow()

            # Emit agent ready signal
            self._emitter.emit(
                SignalPayload(
                    signal_type=SignalType.AGENT_READY,
                    task_id=task_id,
                    agent_id=self.metadata.agent_id,
                    data={
                        "agent_name": self.metadata.name,
                        "tasks_completed": self.metadata.tasks_completed,
                    },
                )
            )

            return result

        except Exception as e:
            # Update state on failure
            self.metadata.state = AgentState.ERROR
            self.metadata.current_task_id = None
            self.metadata.tasks_failed += 1
            self.metadata.last_active = datetime.utcnow()

            logger.error(f"Agent {self.metadata.agent_id} failed executing task: {e}")
            raise

    def set_ready(self):
        """Mark agent as ready."""
        self.metadata.state = AgentState.READY

    def set_offline(self):
        """Mark agent as offline."""
        self.metadata.state = AgentState.OFFLINE

    @property
    def is_available(self) -> bool:
        """Check if agent is available for tasks."""
        return self.metadata.state in {AgentState.IDLE, AgentState.READY}


class AgentPool:
    """
    Manages a pool of agents for task execution.

    Provides agent selection, load balancing, and availability tracking.
    """

    def __init__(self):
        """Initialize agent pool."""
        self._agents: Dict[str, Agent] = {}

    def add_agent(self, agent: Agent):
        """
        Add an agent to the pool.

        Args:
            agent: Agent instance to add
        """
        self._agents[agent.metadata.agent_id] = agent
        agent.set_ready()
        logger.info(
            f"Added agent {agent.metadata.agent_id} ({agent.metadata.name}) "
            f"with role {agent.metadata.role} to pool"
        )

    def remove_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the pool.

        Args:
            agent_id: Agent identifier

        Returns:
            True if agent was removed
        """
        if agent_id in self._agents:
            agent = self._agents.pop(agent_id)
            agent.set_offline()
            logger.info(f"Removed agent {agent_id} from pool")
            return True
        return False

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def get_available_agents(self, role: Optional[str] = None) -> list[Agent]:
        """
        Get all available agents, optionally filtered by role.

        Args:
            role: Optional role filter

        Returns:
            List of available agents
        """
        agents = [a for a in self._agents.values() if a.is_available]

        if role:
            agents = [a for a in agents if a.metadata.role == role]

        return agents

    def get_agent_by_role(self, role: str) -> Optional[Agent]:
        """
        Get first available agent with specified role.

        Args:
            role: Agent role to find

        Returns:
            First available agent with role, or None
        """
        available = self.get_available_agents(role=role)
        return available[0] if available else None

    def get_all_agents(self) -> list[Agent]:
        """Get all agents in pool."""
        return list(self._agents.values())

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get statistics about the agent pool."""
        agents = self._agents.values()
        return {
            "total_agents": len(agents),
            "available_agents": len([a for a in agents if a.is_available]),
            "busy_agents": len(
                [a for a in agents if a.metadata.state == AgentState.BUSY]
            ),
            "offline_agents": len(
                [a for a in agents if a.metadata.state == AgentState.OFFLINE]
            ),
            "total_tasks_completed": sum(a.metadata.tasks_completed for a in agents),
            "total_tasks_failed": sum(a.metadata.tasks_failed for a in agents),
        }


def load_personas_from_yaml(yaml_path: str = "personas.yaml") -> Dict[str, Dict[str, str]]:
    """
    Load agent personas from YAML file.

    Args:
        yaml_path: Path to personas.yaml file

    Returns:
        Dictionary mapping persona name to persona config
    """
    try:
        with open(yaml_path, "r") as f:
            personas = yaml.safe_load(f)
            logger.info(f"Loaded {len(personas)} personas from {yaml_path}")
            return personas
    except Exception as e:
        logger.error(f"Failed to load personas from {yaml_path}: {e}")
        return {}


def create_agent_from_persona(
    persona_name: str,
    execute_func: Callable[..., Any],
    personas: Optional[Dict[str, Dict[str, str]]] = None,
) -> Optional[Agent]:
    """
    Create an agent from a persona definition.

    Args:
        persona_name: Name of persona in personas.yaml
        execute_func: Function to execute tasks
        personas: Optional pre-loaded personas dict

    Returns:
        Agent instance, or None if persona not found
    """
    if personas is None:
        personas = load_personas_from_yaml()

    persona_config = personas.get(persona_name)
    if not persona_config:
        logger.error(f"Persona {persona_name} not found")
        return None

    agent = Agent(
        agent_id=f"agent_{persona_name}",
        name=persona_config.get("role", persona_name),
        role=persona_config.get("role", "unknown"),
        execute_func=execute_func,
        capabilities={
            "goal": persona_config.get("goal", ""),
            "backstory": persona_config.get("backstory", ""),
            "preseed_query": persona_config.get("preseed_query", ""),
        },
    )

    logger.info(f"Created agent from persona {persona_name}")
    return agent
