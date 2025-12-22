import logging
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pipeline import OllamaClient
<<<<<<< HEAD
from src.orchestrator import ChainOrchestrator
=======
from src.chain_orchestrator import ChainOrchestrator
>>>>>>> origin/devel

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    # Configuration
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = "qwen2.5-coder:7b-q4_0"  # Default model

    logger.info(f"Connecting to Ollama at {ollama_url}")
    client = OllamaClient(base_url=ollama_url)

    # Initialize Orchestrator
    orchestrator = ChainOrchestrator(
        client=client, manager_model=model, worker_model=model, evaluator_model=model
    )

    # Test Objective
    objective = "Implement a simple Python function to calculate the Fibonacci sequence up to N terms, with type hints and a docstring."

    logger.info("Starting test workflow...")
    result = orchestrator.run_workflow(objective)

    logger.info("Workflow Result:")
    import json

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
