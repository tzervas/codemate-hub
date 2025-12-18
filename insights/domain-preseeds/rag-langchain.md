# Preseed: RAG and LangChain Best Practices

## RAG Architecture

### Document Processing Pipeline
1. **Ingestion**: Load documents from various sources
2. **Chunking**: Split into manageable pieces with overlap
3. **Embedding**: Convert to vector representations
4. **Storage**: Index in vector database
5. **Retrieval**: Find relevant chunks for queries
6. **Generation**: Augment LLM responses with context

### Chunking Strategies
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len,
)
```

**Best Practices:**
- Chunk size: 500-1500 characters (depends on content)
- Overlap: 10-20% of chunk size
- Preserve semantic boundaries (paragraphs, sections)

## Vector Databases

### ChromaDB Usage
```python
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    base_url="http://ollama:11434",
    model="nomic-embed-text",
)

vectorstore = Chroma(
    collection_name="documents",
    embedding_function=embeddings,
    persist_directory="./chroma_db",
)
```

### Similarity Search
```python
# Basic search
results = vectorstore.similarity_search(query, k=5)

# With relevance scores
results = vectorstore.similarity_search_with_relevance_scores(
    query,
    k=5,
    score_threshold=0.7,  # Filter low-relevance results
)
```

## Prompt Engineering

### RAG Prompt Template
```python
RAG_PROMPT = """You are a helpful assistant. Use the following context to answer the question.
If the answer is not in the context, say "I don't have enough information."

Context:
{context}

Question: {question}

Answer:"""
```

### Chain Construction
```python
from langchain.chains import RetrievalQA

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",  # or "map_reduce" for long contexts
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True,
)
```

## Embedding Models

### Recommended Models
| Model | Dimensions | Use Case |
|-------|-----------|----------|
| nomic-embed-text | 768 | General purpose, fast |
| all-minilm | 384 | Lightweight, fast |
| mxbai-embed-large | 1024 | Higher accuracy |

### Embedding Best Practices
- Use same model for indexing and queries
- Batch embeddings for efficiency
- Cache frequently used embeddings
- Consider dimensionality reduction for scale

## Query Optimization

### Hybrid Search
Combine semantic and keyword search:
```python
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers import BM25Retriever

ensemble = EnsembleRetriever(
    retrievers=[semantic_retriever, bm25_retriever],
    weights=[0.7, 0.3],
)
```

### Re-ranking
```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

compressor = LLMChainExtractor.from_llm(llm)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=retriever,
)
```

## Memory and Context

### Conversation Memory
```python
from langchain.memory import ConversationBufferWindowMemory

memory = ConversationBufferWindowMemory(
    k=5,  # Keep last 5 exchanges
    memory_key="chat_history",
    return_messages=True,
)
```

### Context Window Management
- Monitor token usage
- Summarize long conversations
- Prioritize recent context
- Use sliding window for memory

## Error Handling

### Graceful Degradation
```python
async def query_with_fallback(question: str) -> str:
    try:
        # Try RAG first
        result = await qa_chain.ainvoke({"query": question})
        if result["source_documents"]:
            return result["result"]
    except Exception as e:
        logger.warning(f"RAG failed: {e}")
    
    # Fall back to direct LLM
    return await llm.ainvoke(question)
```
