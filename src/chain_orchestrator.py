from __future__ import annotations
import logging
import yaml
from typing import Any, Dict, List, Optional

from .pipeline import OllamaClient

logger = logging.getLogger(__name__)


class ChainOrchestrator:
    """A robust orchestrator implementing a Manager-Worker-Evaluator loop.

    This orchestrator decomposes objectives into tasks, routes them to specialized workers,
    and uses an evaluator for quality control gating.
    """

    def __init__(
        self,
        client: OllamaClient,
        manager_model: str,
        worker_model: str,
        evaluator_model: str,
        personas_path: str = "personas.yaml",
    ):
        self.client = client
        self.manager_model = manager_model
        self.worker_model = worker_model
        self.evaluator_model = evaluator_model
        self.personas = self._load_personas(personas_path)

    def _load_personas(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load personas from {path}: {e}")
            return {}

    def run_workflow(self, objective: str) -> Dict[str, Any]:
        """Run the full multi-agentic workflow for a given objective."""
        logger.info(f"Starting workflow for objective: {objective}")

        # Phase 1: Decomposition (Manager)
        manager_persona = self.personas.get("manager", {})
        decomposition_prompt = (
            f"Role: {manager_persona.get('role')}\n"
            f"Goal: {manager_persona.get('goal')}\n"
            f"Backstory: {manager_persona.get('backstory')}\n\n"
            f"Objective: {objective}\n\n"
            "Decompose this objective into a list of manageable, tightly scoped tasks. "
            "Return each task on a new line starting with 'TASK: '."
        )

        manager_out = self.client.generate(decomposition_prompt, model=self.manager_model)
        tasks = [
            line.replace("TASK: ", "").strip()
            for line in manager_out.get("response", "").split("\n")
            if line.startswith("TASK:")
        ]

        if not tasks:
            logger.warning(
                "Manager failed to decompose objective into tasks. Using objective as single task."
            )
            tasks = [objective]

        workflow_results = []

        for task in tasks:
            logger.info(f"Processing task: {task}")
            task_result = self._process_task_with_loop(task)
            workflow_results.append(task_result)

        return {"objective": objective, "tasks": workflow_results, "status": "completed"}

    def _process_task_with_loop(self, task: str, max_iterations: int = 3) -> Dict[str, Any]:
        """Process a single task with the Worker-Evaluator loop."""
        iteration = 0
        feedback = ""
        worker_output = ""

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Task iteration {iteration} for: {task}")

            # Phase 2: Implementation (Worker)
            # For simplicity, we use python_worker as default, but could route based on task content
            worker_persona = self.personas.get("python_worker", {})
            worker_prompt = (
                f"Role: {worker_persona.get('role')}\n"
                f"Goal: {worker_persona.get('goal')}\n"
                f"Backstory: {worker_persona.get('backstory')}\n\n"
                f"Task: {task}\n"
                f"Previous Feedback: {feedback if feedback else 'None'}\n\n"
                "Implement the task and provide the deliverables."
            )

            worker_out = self.client.generate(worker_prompt, model=self.worker_model)
            worker_output = worker_out.get("response", "")

            # Phase 3: Quality Control (Evaluator)
            evaluator_persona = self.personas.get("evaluator", {})
            evaluator_prompt = (
                f"Role: {evaluator_persona.get('role')}\n"
                f"Goal: {evaluator_persona.get('goal')}\n"
                f"Backstory: {evaluator_persona.get('backstory')}\n\n"
                f"Task: {task}\n"
                f"Worker Output: {worker_output}\n\n"
                "Evaluate the worker output against the task requirements and best practices. "
                "If it meets requirements, start your response with 'APPROVED'. "
                "If not, start with 'REJECTED' and provide detailed analysis and guidance for improvement."
            )

            evaluator_out = self.client.generate(evaluator_prompt, model=self.evaluator_model)
            evaluator_response = evaluator_out.get("response", "")

            if evaluator_response.strip().upper().startswith("APPROVED"):
                logger.info(f"Task approved by evaluator on iteration {iteration}")
                return {
                    "task": task,
                    "output": worker_output,
                    "evaluator_notes": evaluator_response,
                    "iterations": iteration,
                    "status": "approved",
                }
            else:
                logger.warning(
                    f"Task rejected by evaluator on iteration {iteration}. Feedback: {evaluator_response[:100]}..."
                )
                feedback = evaluator_response

        logger.error(f"Task failed to meet requirements after {max_iterations} iterations.")
        return {
            "task": task,
            "output": worker_output,
            "evaluator_notes": feedback,
            "iterations": iteration,
            "status": "failed",
        }
