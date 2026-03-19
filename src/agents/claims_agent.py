"""Main claims adjudication agent with multi-step orchestration."""

from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.schemas.claim_schemas import (
    ClaimInput,
    ClaimDecisionOutput,
    AgentState,
    ClaimDecision,
)
from src.tools.evidence_extractor import EvidenceExtractorTool
from src.tools.policy_retriever import PolicyRetrieverTool
from src.tools.decision_maker import DecisionMakerTool
from src.rag.policy_rag import PolicyRAGPipeline
from src.config import settings


class AgentStep(str, Enum):
    """Steps in the claims processing workflow."""

    INTAKE = "intake"
    EXTRACT_EVIDENCE = "extract_evidence"
    RETRIEVE_POLICY = "retrieve_policy"
    MAKE_DECISION = "make_decision"
    VALIDATE = "validate"
    FINALIZE = "finalize"


@dataclass
class ClaimsAgent:
    """Agentic system for warranty claims auto-adjudication.

    Orchestrates multi-step workflow:
    1. Intake - Validate and parse claim input
    2. Extract Evidence - Parse claim documents and extract key info
    3. Retrieve Policy - Query RAG system for coverage terms
    4. Make Decision - Determine approve/deny/escalate
    5. Validate - Check decision confidence and completeness
    6. Finalize - Format output and trigger actions
    """

    def __init__(self):
        """Initialize agent with tools and LLM."""
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.0,
        )

        # Initialize RAG pipeline
        self.rag_pipeline = PolicyRAGPipeline()

        # Initialize tools
        self.evidence_extractor = EvidenceExtractorTool()
        self.policy_retriever = PolicyRetrieverTool(rag_pipeline=self.rag_pipeline)
        self.decision_maker = DecisionMakerTool(llm=self.llm)

        # Build state graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph state machine for claims processing."""

        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node(AgentStep.INTAKE, self._intake_step)
        workflow.add_node(AgentStep.EXTRACT_EVIDENCE, self._extract_evidence_step)
        workflow.add_node(AgentStep.RETRIEVE_POLICY, self._retrieve_policy_step)
        workflow.add_node(AgentStep.MAKE_DECISION, self._make_decision_step)
        workflow.add_node(AgentStep.VALIDATE, self._validate_step)
        workflow.add_node(AgentStep.FINALIZE, self._finalize_step)

        # Define edges
        workflow.add_edge(AgentStep.INTAKE, AgentStep.EXTRACT_EVIDENCE)
        workflow.add_edge(AgentStep.EXTRACT_EVIDENCE, AgentStep.RETRIEVE_POLICY)
        workflow.add_edge(AgentStep.RETRIEVE_POLICY, AgentStep.MAKE_DECISION)
        workflow.add_edge(AgentStep.MAKE_DECISION, AgentStep.VALIDATE)
        workflow.add_edge(AgentStep.VALIDATE, AgentStep.FINALIZE)
        workflow.add_edge(AgentStep.FINALIZE, END)

        # Conditional routing from validate
        workflow.add_conditional_edges(
            AgentStep.VALIDATE,
            self._should_escalate,
            {
                "escalate": AgentStep.MAKE_DECISION,  # Loop back with more context
                "finalize": END,
            },
        )

        # Set entry point
        workflow.set_entry_point(AgentStep.INTAKE)

        return workflow.compile()

    def _should_escalate(self, state: AgentState) -> str:
        """Determine if claim should be escalated."""
        if state.requires_human_review:
            return "escalate"
        return "finalize"

    async def _intake_step(self, state: AgentState) -> AgentState:
        """Validate and parse claim input."""
        claim = state.claim_input

        # Validate required fields
        if not claim.claim_id:
            state.error = "Missing claim ID"
            return state

        # Log intake
        print(f"[INTAKE] Processing claim {claim.claim_id}")

        state.current_step = AgentStep.EXTRACT_EVIDENCE
        return state

    async def _extract_evidence_step(self, state: AgentState) -> AgentState:
        """Extract evidence from claim submission."""
        claim = state.claim_input

        # Combine claim info into text for extraction
        claim_text = f"""
        Claim ID: {claim.claim_id}
        Product Category: {claim.product_category}
        Damage Description: {claim.damage_description}
        Additional Notes: {claim.additional_notes or "None"}
        """

        print(f"[EXTRACT] Extracting evidence for claim {claim.claim_id}")

        # Run evidence extraction
        evidence_result = await self.evidence_extractor._arun(claim_text)

        state.tool_results["evidence"] = evidence_result
        state.current_step = AgentStep.RETRIEVE_POLICY

        return state

    async def _retrieve_policy_step(self, state: AgentState) -> AgentState:
        """Retrieve relevant policy information."""
        claim = state.claim_input
        evidence = state.tool_results.get("evidence", {})
        damage_type = evidence.get("damage_type", "unknown")

        print(f"[RETRIEVE] Fetching policy for claim {claim.claim_id}")

        # Build query for RAG
        query = f"{claim.product_category} | {damage_type} | {claim.damage_description}"

        # Retrieve policy info
        policy_result = await self.policy_retriever._arun(query)

        state.tool_results["policy"] = policy_result
        state.current_step = AgentStep.MAKE_DECISION

        return state

    async def _make_decision_step(self, state: AgentState) -> AgentState:
        """Make adjudication decision."""
        claim = state.claim_input
        evidence = state.tool_results.get("evidence", {})
        policy = state.tool_results.get("policy", {})

        print(f"[DECIDE] Making decision for claim {claim.claim_id}")

        # Format input for decision maker
        decision_input = f"{evidence} | {policy} | {claim.claim_id}"

        # Make decision
        decision_result = await self.decision_maker._arun(decision_input)

        state.draft_decision = ClaimDecisionOutput(**decision_result)

        # Check if escalation needed
        state.requires_human_review = (
            state.draft_decision.confidence_score < 0.7
            or state.draft_decision.decision == ClaimDecision.ESCALATED
        )

        state.current_step = AgentStep.VALIDATE

        return state

    async def _validate_step(self, state: AgentState) -> AgentState:
        """Validate decision completeness and quality."""
        decision = state.draft_decision

        # Validation checks
        is_valid = True

        if decision is None:
            is_valid = False
            state.error = "No decision was made"
        elif decision.confidence_score < 0.5:
            is_valid = False
            state.error = "Confidence too low"
        elif not decision.reasoning:
            is_valid = False
            state.error = "Missing reasoning"

        if not is_valid:
            state.requires_human_review = True

        print(
            f"[VALIDATE] Decision valid: {is_valid}, Escalation: {state.requires_human_review}"
        )

        return state

    async def _finalize_step(self, state: AgentState) -> AgentState:
        """Finalize and format decision output."""
        print(f"[FINALIZE] Finalizing claim {state.claim_input.claim_id}")

        # Add metadata
        if state.draft_decision:
            state.draft_decision.processed_at = datetime.utcnow().isoformat()
            state.draft_decision.agent_version = "1.0.0"

        state.current_step = AgentStep.FINALIZE
        return state

    async def process_claim(self, claim_input: ClaimInput) -> ClaimDecisionOutput:
        """Process a warranty claim through the agentic workflow."""

        # Initialize state
        initial_state = AgentState(claim_input=claim_input)

        # Run through graph
        result_state = await self.graph.ainvoke(initial_state)

        return result_state.draft_decision

    def process_claim_sync(self, claim_input: ClaimInput) -> ClaimDecisionOutput:
        """Synchronous claim processing for FastAPI."""
        import asyncio

        return asyncio.run(self.process_claim(claim_input))


def create_claims_agent() -> ClaimsAgent:
    """Factory function to create claims agent."""
    return ClaimsAgent()
