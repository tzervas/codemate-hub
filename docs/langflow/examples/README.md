# Langflow Example Flows

This directory contains example Langflow workflows that demonstrate common coding assistant tasks and integration patterns.

## Available Flows

### 1. Simple Code Generation (`simple-code-generation.json`)

**Purpose**: Generate code snippets based on natural language descriptions.

**Components**:
- Input: Text prompt describing the code to generate
- LLM: Ollama component (qwen2.5-coder:7b-q4_0)
- Output: Generated code snippet

**Use Case**: Quick code generation for common programming tasks.

**Integration**: Mirrors the basic functionality of `pipeline.py` generate operation.

**How to Use**:
1. Import the flow into Langflow
2. Configure the Ollama component with base URL: `http://ollama:11434`
3. Set the model to `qwen2.5-coder:7b-q4_0`
4. Run the flow with a prompt like "Write a Python function to calculate fibonacci numbers"

---

### 2. Code Review with Context (`code-review-with-context.json`)

**Purpose**: Review code with contextual understanding and provide improvement suggestions.

**Components**:
- Input 1: Code snippet to review
- Input 2: Context/requirements
- Prompt Template: Structured review prompt
- LLM: Ollama component
- Output: Review feedback with suggestions

**Use Case**: Automated code review with specific context and requirements.

**Integration**: Can complement the review orchestrator in `services/review_orchestrator/`.

**How to Use**:
1. Import the flow into Langflow
2. Provide the code to review in the first input
3. Provide context (e.g., "Check for security issues", "Focus on performance")
4. Review the generated feedback

---

### 3. Bug Analysis Pipeline (`bug-analysis-pipeline.json`)

**Purpose**: Analyze code for potential bugs and provide detailed explanations.

**Components**:
- Input: Code snippet or file content
- Chain: Multi-step analysis (syntax → logic → edge cases)
- LLM: Ollama component
- Output: Structured bug report

**Use Case**: Deep analysis of code for potential issues before deployment.

**Integration**: Can be integrated with CI/CD pipeline for automated bug detection.

**How to Use**:
1. Import the flow into Langflow
2. Paste code to analyze
3. Review the multi-stage analysis output
4. Address identified issues

---

### 4. Documentation Generator (`documentation-generator.json`)

**Purpose**: Generate comprehensive documentation from code.

**Components**:
- Input: Code snippet or function
- Prompt Template: Documentation structure template
- LLM: Ollama component
- Output: Formatted documentation (markdown)

**Use Case**: Automated documentation generation for functions, classes, and modules.

**Integration**: Can be used alongside existing pipeline for documentation tasks.

**How to Use**:
1. Import the flow into Langflow
2. Provide the code to document
3. Specify documentation style (e.g., "Google style", "NumPy style")
4. Generate and review documentation

---

### 5. Test Case Generator (`test-case-generator.json`)

**Purpose**: Generate unit tests for given code.

**Components**:
- Input: Code to test
- Prompt Template: Test generation template with framework specification
- LLM: Ollama component
- Output: Test cases

**Use Case**: Quickly generate test cases for new or existing code.

**Integration**: Complements existing test infrastructure in `tests/`.

**How to Use**:
1. Import the flow into Langflow
2. Provide the code to test
3. Specify test framework (e.g., "pytest", "unittest")
4. Review and refine generated tests

---

## Flow Templates Structure

Each flow JSON file contains:

```json
{
  "name": "Flow Name",
  "description": "Flow description",
  "data": {
    "nodes": [...],    // Flow components and configuration
    "edges": [...]     // Connections between components
  }
}
```

## Creating New Flows

When creating new example flows:

1. **Design**: Plan the workflow components and data flow
2. **Build**: Create the flow in Langflow UI
3. **Test**: Verify the flow works with sample inputs
4. **Export**: Export as JSON to this directory
5. **Document**: Add entry to this README with:
   - Purpose and use case
   - Component description
   - Integration points
   - Usage instructions

## Flow Naming Conventions

- Use lowercase with hyphens: `my-flow-name.json`
- Be descriptive: flow name should indicate purpose
- Include version if applicable: `code-review-v2.json`

## Integration with Pipeline

### Calling Flows from Python

Example code to integrate Langflow flows with the Python pipeline:

```python
import requests
from typing import Dict, Any

class LangflowClient:
    """Client for executing Langflow workflows."""
    
    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url
    
    def run_flow(self, flow_id: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Langflow flow with given inputs.
        
        Args:
            flow_id: The UUID of the flow to execute
            inputs: Dictionary of input values for the flow
            
        Returns:
            Dictionary containing flow execution results
        """
        url = f"{self.base_url}/api/v1/run/{flow_id}"
        response = requests.post(url, json={"inputs": inputs})
        response.raise_for_status()
        return response.json()

# Usage example
client = LangflowClient()
result = client.run_flow(
    flow_id="your-flow-id-here",
    inputs={"code": "def hello(): pass", "context": "review for style"}
)
print(result)
```

### Pipeline Mapping

| Flow Type | Pipeline Component | Relationship |
|-----------|-------------------|--------------|
| Simple Code Generation | `pipeline.py` generate | Direct alternative |
| Code Review | Review orchestrator | Complementary |
| Bug Analysis | Static analysis | Complementary |
| Documentation | N/A | New capability |
| Test Generation | N/A | New capability |

## Testing Flows

### Manual Testing
1. Import flow into Langflow UI
2. Use the built-in test feature
3. Verify outputs match expectations
4. Test edge cases and error handling

### Automated Testing
Consider creating integration tests:

```python
# tests/test_langflow_integration.py
import pytest
from langflow_client import LangflowClient

def test_code_generation_flow():
    client = LangflowClient()
    result = client.run_flow(
        flow_id="code-generation-flow-id",
        inputs={"prompt": "Create a hello world function"}
    )
    assert "def" in result["output"]
    assert "hello" in result["output"].lower()
```

## Troubleshooting

### Flow Won't Import
- Verify JSON syntax with `jq . flow.json`
- Check Langflow version compatibility
- Review error messages in Langflow logs

### Ollama Connection Failed
- Verify `OLLAMA_BASE_URL` environment variable
- Check Ollama service is running: `docker compose ps ollama`
- Test connection: `curl http://localhost:11434/api/tags`

### Flow Execution Timeout
- Check model is loaded: `docker compose exec ollama ollama list`
- Increase timeout in flow configuration
- Monitor resource usage: `docker stats`

## Best Practices

1. **Version Control**: Always export and commit flows after significant changes
2. **Documentation**: Document inputs, outputs, and expected behavior
3. **Testing**: Test flows with various inputs before production use
4. **Security**: Sanitize user inputs in flows that accept external data
5. **Performance**: Monitor token usage and response times
6. **Error Handling**: Include error handling nodes for robust workflows

## Contributing

When adding new example flows:

1. Ensure the flow is well-tested and documented
2. Follow naming conventions
3. Update this README with flow details
4. Include sample inputs/outputs
5. Document any special configuration requirements

## Resources

- [Langflow Components](https://docs.langflow.org/components/overview)
- [Creating Custom Components](https://docs.langflow.org/components/custom)
- [Langflow API Reference](https://docs.langflow.org/api/reference)
