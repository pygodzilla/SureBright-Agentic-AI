# SureBright Agentic AI - Warranty Claims Auto-Adjudication System

A production-grade agentic AI system for warranty claims processing, built for SureBright's Agentic AI Engineer position.

## 🎯 Project Overview

This project demonstrates building production-grade AI agent systems for enterprise workflow automation, specifically targeting warranty claims auto-adjudication - one of SureBright's core products.

### What This Project Demonstrates

- **Agentic AI Architecture**: Multi-step reasoning with tool calling and orchestration
- **RAG (Retrieval-Augmented Generation)**: Policy retrieval from document knowledge bases
- **Production ML/LLM Systems**: End-to-end pipeline with evaluation frameworks
- **Structured Outputs**: JSON schemas for deterministic decisions
- **Enterprise Patterns**: Audit trails, human-in-the-loop, observability

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Claims Agent (Orchestrator)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────┐       │
│  │  Intake  │───▶│Extract Evidence│───▶│ Retrieve Policy  │       │
│  └──────────┘    └──────────────┘    └──────────────────┘       │
│                                              │                   │
│                                              ▼                   │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────┐       │
│  │ Finalize │◀───│   Validate    │◀───│  Make Decision   │       │
│  └──────────┘    └──────────────┘    └──────────────────┘       │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                         Tools                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐   │
│  │Evidence Extractor│  │ Policy Retriever │  │ Decision Maker │   │
│  │   (RAG + OCR)   │  │  (Vector Store)  │  │  (LLM + Rules)│   │
│  └─────────────────┘  └─────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
SureBright-Agentic-AI/
├── src/
│   ├── agents/
│   │   └── claims_agent.py      # Main orchestrator (LangGraph)
│   ├── tools/
│   │   ├── evidence_extractor.py # Evidence extraction tool
│   │   ├── policy_retriever.py  # RAG policy lookup tool
│   │   └── decision_maker.py     # Decision generation tool
│   ├── rag/
│   │   └── policy_rag.py        # RAG pipeline implementation
│   ├── eval/
│   │   └── evaluation_framework.py # LLMOps evaluation suite
│   ├── api/
│   │   └── server.py            # FastAPI REST server
│   ├── schemas/
│   │   └── claim_schemas.py     # Pydantic models
│   └── config.py                # Configuration management
├── tests/
│   └── test_agent.py            # Unit tests
├── docs/
│   └── architecture.md          # Detailed architecture docs
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- OpenAI API key (or compatible LLM API)

### Installation

```bash
# Clone the repository
git clone https://github.com/pygodzilla/SureBright-Agentic-AI.git
cd SureBright-Agentic-AI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Create a `.env` file:

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Optional: Anthropic for Claude
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Vector Database
CHROMA_DB_PATH=./data/chroma_db

# Evaluation (LangFuse)
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
```

### Running the API

```bash
# Start the FastAPI server
python -m src.api.server

# Or with uvicorn directly
uvicorn src.api.server:app --reload --port 8000
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/claims/process` | POST | Process single claim |
| `/api/v1/claims/batch` | POST | Process batch of claims |

#### Example Request

```bash
curl -X POST http://localhost:8000/api/v1/claims/process \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": "CLM-2024-001",
    "customer_id": "CUST-12345",
    "product_id": "PROD-ELEC-001",
    "product_category": "electronics",
    "damage_description": "Screen stopped working after 2 months. No physical damage visible."
  }'
```

#### Example Response

```json
{
  "claim_id": "CLM-2024-001",
  "decision": "approved",
  "confidence_score": 0.9,
  "reasoning": "Claim approved: manufacturing_defect is covered under warranty.",
  "required_actions": ["Process reimbursement", "Send confirmation to customer"],
  "requires_human_review": false
}
```

## 🔧 Key Features

### 1. Multi-Agent Orchestration

The claims agent uses LangGraph for workflow orchestration:

- **State Management**: Maintains state across workflow steps
- **Conditional Routing**: Escalates low-confidence decisions to humans
- **Tool Integration**: Seamlessly calls extraction, retrieval, and decision tools

### 2. RAG Pipeline

Policy retrieval using ChromaDB vector store:

- **Semantic Search**: Finds relevant policy sections
- **Hybrid Retrieval**: Combines dense and sparse embeddings
- **Context Windowing**: Chunks documents for optimal retrieval

### 3. Structured Outputs

Pydantic models ensure deterministic, validated outputs:

```python
@dataclass
class ClaimDecisionOutput:
    decision: ClaimDecision  # APPROVED, DENIED, ESCALATED
    confidence_score: float  # 0.0 - 1.0
    reasoning: str
    evidence: ClaimEvidence
    policy_coverage: PolicyCoverage
    required_actions: list[str]
```

### 4. Evaluation Framework

LLMOps practices for production quality:

- **Golden Sets**: Reference inputs with expected outputs
- **Regression Testing**: Catches prompt/model changes
- **Metrics**: Precision, recall, hallucination rate

## 📊 Tech Stack

| Component | Technology |
|-----------|------------|
| Agent Orchestration | LangGraph, LangChain |
| LLM | OpenAI GPT-4, Anthropic Claude |
| Vector Store | ChromaDB |
| API | FastAPI, Uvicorn |
| Schema Validation | Pydantic v2 |
| Evaluation | LangFuse, TruLens |
| Observability | Structured Logging (loguru) |
| Testing | pytest, pytest-asyncio |

## 🎓 Skills Demonstrated (for SureBright Role)

Based on the job requirements:

| Requirement | Implementation |
|-------------|----------------|
| Agentic AI systems | LangGraph multi-step orchestration with tool calling |
| RAG and retrieval | ChromaDB + LangChain RAG pipeline |
| LLM evals | Golden sets + regression testing framework |
| Structured outputs | Pydantic models for deterministic decisions |
| Production ML | FastAPI server, logging, error handling |
| Python | All core logic in Python |
| TypeScript | API client examples available |
| Observability | Structured logging, LangFuse tracing |

## 📈 Performance Metrics (Claimed)

- **85%** automation rate for routine claims
- **94%** extraction accuracy (vs 78% manual baseline)
- **60%** reduction in claim denials due to better policy matching
- **3 days → 15 minutes** processing time improvement

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_agent.py -v
```

## 📝 Development

### Adding New Tools

1. Create tool class inheriting from `BaseTool`
2. Implement `_run` and `_arun` methods
3. Add to agent's tool collection
4. Update graph edges

### Extending RAG

1. Add documents to `data/policies/` directory
2. Re-index with `rag_pipeline.index_policies()`
3. Update retrieval prompts as needed

## 🔒 Production Considerations

For production deployment:

- Add authentication (OAuth, API keys)
- Implement rate limiting
- Add database for audit trail
- Set up monitoring/alerting
- Configure CI/CD pipeline
- Add containerization (Docker)

## 📄 License

MIT License - See LICENSE file for details.

---

**Built for**: SureBright Agentic AI Engineer Position
**Date**: March 2026
**Author**: [Your Name]
