"""FastAPI server for Claims Adjudication Agent."""

from typing import Optional
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from structlog import structlog

from src.agents.claims_agent import ClaimsAgent, create_claims_agent
from src.schemas.claim_schemas import ClaimInput, ClaimDecisionOutput, ClaimDecision
from src.config import settings

# Configure structured logging
logging.basicConfig(level=settings.log_level)
log = structlog.get_logger()

# Global agent instance
agent: Optional[ClaimsAgent] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global agent
    log.info("starting_claims_agent")
    agent = create_claims_agent()
    log.info("claims_agent_ready")
    yield
    log.info("shutting_down_claims_agent")


app = FastAPI(
    title="SureBright Claims Auto-Adjudication API",
    description="Agentic AI system for warranty claims processing",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ClaimRequest(BaseModel):
    """API request model for claim submission."""

    claim_id: str = Field(..., description="Unique claim identifier")
    customer_id: str = Field(..., description="Customer identifier")
    product_id: str = Field(..., description="Product identifier")
    product_category: str = Field(
        ..., description="Product category (electronics, appliance, furniture)"
    )
    damage_description: str = Field(..., description="Description of the issue")
    additional_notes: Optional[str] = Field(
        None, description="Additional customer notes"
    )


class ClaimResponse(BaseModel):
    """API response model for claim decision."""

    claim_id: str
    decision: ClaimDecision
    confidence_score: float
    reasoning: str
    required_actions: list[str]
    requires_human_review: bool
    escalation_reason: Optional[str] = None


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "claims-adjudication-v1"}


@app.post("/api/v1/claims/process", response_model=ClaimResponse)
async def process_claim(request: ClaimRequest) -> ClaimResponse:
    """Process a warranty claim through the agentic workflow.

    Returns structured decision with reasoning and confidence score.
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Convert request to ClaimInput
        claim_input = ClaimInput(
            claim_id=request.claim_id,
            customer_id=request.customer_id,
            product_id=request.product_id,
            product_category=request.product_category,
            damage_description=request.damage_description,
            additional_notes=request.additional_notes,
        )

        log.info("processing_claim", claim_id=request.claim_id)

        # Process through agent
        decision = await agent.process_claim(claim_input)

        log.info(
            "claim_processed",
            claim_id=request.claim_id,
            decision=decision.decision.value,
            confidence=decision.confidence_score,
        )

        return ClaimResponse(
            claim_id=request.claim_id,
            decision=decision.decision,
            confidence_score=decision.confidence_score,
            reasoning=decision.reasoning,
            required_actions=decision.required_actions,
            requires_human_review=decision.confidence_score < 0.7
            or decision.decision == ClaimDecision.ESCALATED,
            escalation_reason=decision.escalation_reason,
        )

    except Exception as e:
        log.error("claim_processing_failed", claim_id=request.claim_id, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Claim processing failed: {str(e)}"
        )


@app.post("/api/v1/claims/batch")
async def process_claims_batch(
    requests: list[ClaimRequest], background_tasks: BackgroundTasks
) -> dict:
    """Process multiple claims in batch.

    Claims are processed asynchronously and results are logged.
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    claim_ids = [r.claim_id for r in requests]
    log.info("batch_processing_started", count=len(claim_ids))

    # Process in background
    background_tasks.add_task(process_batch, requests, agent)

    return {
        "status": "accepted",
        "message": f"Processing {len(requests)} claims",
        "claim_ids": claim_ids,
    }


async def process_batch(requests: list[ClaimRequest], claims_agent: ClaimsAgent):
    """Background task to process claims batch."""
    for request in requests:
        try:
            claim_input = ClaimInput(
                claim_id=request.claim_id,
                customer_id=request.customer_id,
                product_id=request.product_id,
                product_category=request.product_category,
                damage_description=request.damage_description,
                additional_notes=request.additional_notes,
            )
            await claims_agent.process_claim(claim_input)
        except Exception as e:
            log.error("batch_item_failed", claim_id=request.claim_id, error=str(e))


@app.get("/api/v1/claims/{claim_id}")
async def get_claim_status(claim_id: str) -> dict:
    """Get status of a processed claim."""
    # In production, this would query a database
    return {
        "claim_id": claim_id,
        "status": "processed",
        "message": "Claim status endpoint - integrate with database for full functionality",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
