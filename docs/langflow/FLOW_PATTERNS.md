# Langflow Flow Patterns and Pipeline Mapping

This document describes how Langflow visual workflows relate to and complement the existing Python pipeline in `src/pipeline.py`.

## Architecture Overview

### Current Pipeline (`src/pipeline.py`)

The Python pipeline provides:
- **Fixture-based testing**: Pre-recorded JSON responses for CI/CD
- **Live mode**: Direct API calls to Ollama
- **OllamaClient**: Protocol-based abstraction for LLM interactions
- **Memory integration**: Chroma DB for vector embeddings and context

### Langflow Workflows

Langflow provides:
- **Visual orchestration**: Drag-and-drop workflow design
- **Component library**: Pre-built nodes for common tasks
- **API access**: REST endpoints for programmatic execution
- **UI-based testing**: Interactive flow testing and debugging

## Integration Patterns

### Pattern 1: Parallel Alternatives

Langflow and pipeline can serve the same purpose through different interfaces.

**Example: Code Generation**

Python Pipeline:
```python
client = OllamaClient(base_url="http://ollama:11434")
response = client.generate(
    model="qwen2.5-coder:7b-q4_0",
    prompt="Write a Python function to calculate fibonacci"
)
```

Langflow Flow:
- Import `simple-code-generation.json`
- Use visual interface to input prompt
- Execute through UI or API

**When to use each:**
- Pipeline: Automated, CI/CD, programmatic
- Langflow: Interactive, experimentation, non-technical users

### Pattern 2: Complementary Capabilities

Langflow can extend pipeline functionality with visual capabilities.

**Example: Multi-Step Review**

Pipeline handles basic review:
```python
# Basic single-shot review
review = client.generate(model, review_prompt)
```

Langflow provides multi-stage review:
1. Initial analysis node
2. Security check node
3. Performance analysis node
4. Aggregation node
5. Formatted output

### Pattern 3: Pipeline-Driven Langflow

Python pipeline can orchestrate Langflow flows programmatically.

**Example: Hybrid Approach**

```python
# src/pipeline.py extension
from typing import Dict, Any
import requests

class LangflowIntegration:
    """Integration layer for Langflow flows."""
    
    def __init__(self, langflow_url: str = "http://localhost:7860"):
        self.base_url = langflow_url
    
    def execute_flow(
        self, 
        flow_id: str, 
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a Langflow flow from the pipeline.
        
        Args:
            flow_id: UUID of the Langflow flow
            inputs: Input parameters for the flow
            
        Returns:
            Flow execution results
        """
        response = requests.post(
            f"{self.base_url}/api/v1/run/{flow_id}",
            json={"inputs": inputs}
        )
        response.raise_for_status()
        return response.json()

# Usage in pipeline
langflow = LangflowIntegration()
result = langflow.execute_flow(
    flow_id="code-review-flow-uuid",
    inputs={"code": code_snippet, "context": "security"}
)
```

## Flow Pattern Catalog

### 1. Simple Linear Flow

**Structure**: Input → Transform → LLM → Output

**Best For**:
- Single-purpose tasks
- Quick prototyping
- Simple transformations

**Examples**:
- Code generation
- Documentation generation
- Simple code formatting

**Pipeline Equivalent**: Direct `client.generate()` call

### 2. Multi-Input Flow

**Structure**: Input1 + Input2 → Merge → LLM → Output

**Best For**:
- Contextual operations
- Comparison tasks
- Conditional logic

**Examples**:
- Code review with context
- Diff analysis
- Conditional generation

**Pipeline Equivalent**: Template formatting before `generate()`

### 3. Chain Flow

**Structure**: Input → LLM1 → LLM2 → LLM3 → Output

**Best For**:
- Multi-stage processing
- Refinement workflows
- Sequential analysis

**Examples**:
- Generate → Review → Refine
- Analyze → Summarize → Format
- Extract → Transform → Load

**Pipeline Equivalent**: Multiple sequential `generate()` calls

### 4. Branch Flow

**Structure**: Input → Conditional → [PathA | PathB] → Merge → Output

**Best For**:
- Decision-based routing
- Type-specific processing
- Error handling

**Examples**:
- Route by language (Python vs JavaScript)
- Route by task type (review vs generate)
- Route by complexity (simple vs complex)

**Pipeline Equivalent**: Python conditionals + different `generate()` calls

### 5. Parallel Processing Flow

**Structure**: Input → [LLM1, LLM2, LLM3] → Aggregate → Output

**Best For**:
- Multi-perspective analysis
- Ensemble approaches
- Comprehensive reviews

**Examples**:
- Security + Performance + Style reviews in parallel
- Multiple model comparison
- Diverse suggestion generation

**Pipeline Equivalent**: ThreadPoolExecutor + multiple `generate()` calls

## Component Mapping

### Pipeline Components → Langflow Nodes

| Pipeline Component | Langflow Node | Notes |
|-------------------|---------------|-------|
| `OllamaClient.generate()` | OllamaModel node | Direct 1:1 mapping |
| String templates | PromptTemplate node | Visual template editing |
| Function parameters | TextInput node | UI-based input |
| Return values | TextOutput node | Visual output display |
| Error handling | ConditionalRouter | Visual error routes |
| Context retrieval | VectorStoreRetriever | Chroma integration possible |
| Chain logic | Chain node | Sequential operations |
| Parsing/validation | PythonFunction node | Custom Python code |

### Langflow Nodes → Pipeline Implementation

| Langflow Node | Pipeline Code | Implementation |
|--------------|--------------|----------------|
| OllamaModel | `client.generate()` | Direct API call |
| PromptTemplate | f-string or template | String formatting |
| TextInput | Function parameter | Method argument |
| TextOutput | Return value | Function return |
| Chain | Sequential calls | Multiple `generate()` |
| ConditionalRouter | if/else | Python conditionals |
| PythonFunction | Custom function | Regular Python |
| VectorStore | ChromaDB client | Vector operations |

## Use Case Decision Matrix

| Use Case | Recommended Approach | Rationale |
|----------|---------------------|-----------|
| CI/CD automation | Pipeline | Programmatic, testable |
| Interactive prototyping | Langflow | Visual, iterative |
| API endpoints | Pipeline | Better control, typing |
| Non-technical users | Langflow | No coding required |
| Complex workflows | Langflow (design) + Pipeline (execute) | Visual design, programmatic execution |
| Testing variations | Langflow | Quick iteration |
| Production deployment | Pipeline | Better monitoring, error handling |
| Documentation/training | Langflow | Visual, self-documenting |

## Migration Paths

### From Pipeline to Langflow

To convert a pipeline operation to Langflow:

1. **Identify the operation**:
   ```python
   result = client.generate(model, prompt)
   ```

2. **Map to Langflow nodes**:
   - Input → TextInput
   - prompt → PromptTemplate
   - client.generate → OllamaModel
   - result → TextOutput

3. **Create flow in UI**:
   - Drag nodes onto canvas
   - Configure parameters
   - Connect nodes
   - Test execution

4. **Export flow**:
   - Export as JSON
   - Save to `docs/langflow/examples/`
   - Document in README

### From Langflow to Pipeline

To implement a Langflow flow in pipeline:

1. **Analyze flow structure**:
   - Identify input nodes
   - Map transformation logic
   - Identify LLM calls
   - Map output format

2. **Implement in Python**:
   ```python
   def flow_implementation(inputs: Dict[str, str]) -> str:
       # Map inputs
       prompt = template.format(**inputs)
       
       # LLM call
       result = client.generate(model, prompt)
       
       # Transform output
       return process_output(result)
   ```

3. **Test equivalence**:
   - Use same inputs
   - Compare outputs
   - Validate behavior

## Best Practices

### When to Use Langflow

✅ **Use Langflow for:**
- Rapid prototyping
- Visual documentation
- User-facing tools
- Experimentation
- Non-developer access
- Complex workflow visualization

❌ **Avoid Langflow for:**
- High-volume production APIs
- Critical CI/CD paths
- Latency-sensitive operations
- Heavy computational tasks

### When to Use Pipeline

✅ **Use Pipeline for:**
- Production APIs
- CI/CD integration
- Automated testing
- Performance-critical operations
- Complex error handling
- Integration with other services

❌ **Avoid Pipeline for:**
- One-off experiments
- User-facing flow design
- Non-technical user access

### Hybrid Approach

Best practice for complex systems:

1. **Design in Langflow**: Visual workflow design and prototyping
2. **Implement in Pipeline**: Production-ready code with proper error handling
3. **Reference Langflow**: Keep flows as documentation of intended behavior
4. **Maintain both**: Langflow for experimentation, Pipeline for execution

## Example Hybrid Workflow

```python
# Development phase: Use Langflow
# 1. Create flow in UI: code-review-with-context
# 2. Test with sample inputs
# 3. Export flow definition
# 4. Document expected behavior

# Production phase: Implement in pipeline
class CodeReviewService:
    def __init__(self, ollama_client: OllamaClient):
        self.client = ollama_client
    
    def review_code(self, code: str, context: str) -> dict:
        """Production implementation of code-review-with-context flow."""
        # Template from Langflow flow
        prompt = f"""You are an expert code reviewer. 
        Review the following code with focus on: {context}
        
        Code to review:
        ```
        {code}
        ```
        
        Provide structured review..."""
        
        # Execute via pipeline
        result = self.client.generate(
            model="qwen2.5-coder:7b-q4_0",
            prompt=prompt,
            temperature=0.2
        )
        
        # Parse and return structured output
        return self._parse_review(result)
```

## Monitoring and Observability

### Langflow Flows
- Use built-in execution logs
- Monitor through UI
- Export execution history
- Limited programmatic monitoring

### Pipeline Operations
- Structured logging
- Metrics collection
- Error tracking
- Performance monitoring
- Integration with observability tools

## Future Integration Opportunities

1. **Shared Component Library**: Create reusable components for both
2. **Flow-to-Code Generator**: Auto-generate pipeline code from Langflow
3. **Bidirectional Sync**: Keep flows and code in sync
4. **Unified Testing**: Test both Langflow and pipeline implementations
5. **Performance Comparison**: Benchmark equivalent implementations

## Resources

- [Langflow API Documentation](https://docs.langflow.org/api/reference)
- [Pipeline Implementation](../../src/pipeline.py)
- [Example Flows](./examples/README.md)
- [Ollama API Reference](https://github.com/ollama/ollama/blob/main/docs/api.md)
