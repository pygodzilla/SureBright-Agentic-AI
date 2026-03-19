# Architecture Documentation

## System Overview

The Warranty Claims Auto-Adjudication System is an agentic AI system that processes warranty claims through a multi-step workflow, making decisions about approval, denial, or escalation.

## Core Components

### 1. Claims Agent (Orchestrator)

**Technology**: LangGraph

The agent orchestrates the entire claims processing workflow using a state machine:

```
States:
- INTAKE: Validate claim input
- EXTRACT_EVIDENCE: Parse claim documents
- RETRIEVE_POLICY: Query RAG for coverage terms
- MAKE_DECISION: Generate adjudication decision
- VALIDATE: Check decision quality
- FINALIZE: Format output
```

**Key Features**:
- Async/await for concurrent operations
- State persistence across steps
- Conditional routing for escalations
- Error handling and recovery

### 2. Tools

#### Evidence Extractor
- Parses claim text and documents
- Extracts: product model, dates, damage type
- Uses regex patterns and LLM classification

#### Policy Retriever (RAG)
- ChromaDB vector store
- Semantic search over policy documents
- Returns relevant coverage information

#### Decision Maker
- Rule-based + LLM reasoning
- Structured JSON output
- Confidence scoring

### 3. RAG Pipeline

**Document Processing**:
1. Load warranty policies (TXT, PDF)
2. Chunk into 1000-char segments with 200-char overlap
3. Generate embeddings using OpenAI `text-embedding-3-small`
4. Store in ChromaDB

**Retrieval**:
1. Query embedding generation
2. Similarity search (k=5)
3. Context formatting with relevance scores
4. LLM synthesis for coverage determination

### 4. API Server

**Technology**: FastAPI + Uvicorn

**Endpoints**:
- `POST /api/v1/claims/process` - Single claim processing
- `POST /api/v1/claims/batch` - Batch processing
- `GET /api/v1/claims/{id}` - Status check
- `GET /health` - Health check

## Data Flow

```
Claim Request
    │
    ▼
┌─────────┐
│  API    │ HTTP Request
└────┬────┘
     │
     ▼
┌─────────┐
│ FastAPI │ Validation
└────┬────┘
     │
     ▼
┌──────────────┐
│ Claims Agent │ Orchestration
└──────┬───────┘
       │
       ├──▶ Evidence Extractor
       │
       ├──▶ Policy Retriever (RAG)
       │
       └──▶ Decision Maker
              │
              ▼
       ┌─────────────┐
       │  Decision   │ JSON Response
       └─────────────┘
```

## Schema Design

### ClaimDecisionOutput

```python
{
    "decision": "approved" | "denied" | "escalated" | "pending_information",
    "confidence_score": 0.0-1.0,
    "reasoning": "string",
    "evidence": {
        "product_model": "string",
        "damage_type": "enum",
        "images_provided": boolean,
        ...
    },
    "policy_coverage": {...},
    "required_actions": ["string"],
    "escalation_reason": "string | null"
}
```

## Scalability Considerations

1. **Horizontal Scaling**: Stateless API allows load balancing
2. **Async Processing**: Batch endpoints for high volume
3. **Caching**: Vector store embeddings cached
4. **Rate Limiting**: Protect LLM API quotas

## Security

- API key authentication (production)
- Input validation via Pydantic
- No sensitive data in logs
- Audit trail for decisions

## Monitoring

- Structured logging (JSON format)
- LangFuse for LLM tracing
- Prometheus metrics (future)
- Error rate alerting (future)
