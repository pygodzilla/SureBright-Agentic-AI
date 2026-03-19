"""Pydantic schemas for structured outputs."""

from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class ClaimDecision(str, Enum):
    APPROVED = "approved"
    DENIED = "denied"
    ESCALATED = "escalated"
    PENDING_INFO = "pending_information"


class DamageType(str, Enum):
    MANUFACTURING_DEFECT = "manufacturing_defect"
    ACCIDENTAL_DAMAGE = "accidental_damage"
    SHIPPING_DAMAGE = "shipping_damage"
    NORMAL_WEAR = "normal_wear"
    UNKNOWN = "unknown"


class ClaimEvidence(BaseModel):
    """Evidence extracted from claim submission."""

    product_model: Optional[str] = Field(
        None, description="Product model/serial number"
    )
    purchase_date: Optional[str] = Field(None, description="Purchase date")
    damage_date: Optional[str] = Field(None, description="Date of damage")
    damage_type: DamageType = Field(DamageType.UNKNOWN, description="Type of damage")
    damage_description: Optional[str] = Field(None, description="Description of damage")
    images_provided: bool = Field(False, description="Whether images were provided")
    receipt_provided: bool = Field(False, description="Whether receipt was provided")


class PolicyCoverage(BaseModel):
    """Policy coverage information."""

    is_covered: bool = Field(..., description="Whether the claim is covered")
    coverage_type: Optional[str] = Field(
        None, description="Type of coverage applicable"
    )
    coverage_start: Optional[str] = Field(None, description="Coverage start date")
    coverage_end: Optional[str] = Field(None, description="Coverage end date")
    deductible_amount: Optional[float] = Field(None, description="Deductible amount")
    max_coverage_amount: Optional[float] = Field(
        None, description="Maximum coverage amount"
    )
    excluded_items: list[str] = Field(
        default_factory=list, description="Excluded items"
    )


class ClaimDecisionOutput(BaseModel):
    """Structured output for claim decision."""

    decision: ClaimDecision = Field(..., description="Final claim decision")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in decision (0-1)"
    )
    reasoning: str = Field(..., description="Detailed reasoning for the decision")
    evidence: ClaimEvidence = Field(..., description="Extracted evidence from claim")
    policy_coverage: Optional[PolicyCoverage] = Field(
        None, description="Policy coverage info"
    )
    required_actions: list[str] = Field(
        default_factory=list, description="Actions required (if any)"
    )
    escalation_reason: Optional[str] = Field(
        None, description="Reason for escalation (if applicable)"
    )


class ClaimInput(BaseModel):
    """Input schema for claim submission."""

    claim_id: str = Field(..., description="Unique claim identifier")
    customer_id: str = Field(..., description="Customer identifier")
    product_id: str = Field(..., description="Product identifier")
    product_category: str = Field(..., description="Product category")
    damage_description: str = Field(..., description="Description of the issue")
    additional_notes: Optional[str] = Field(
        None, description="Additional customer notes"
    )


class AgentState(BaseModel):
    """State maintained across agentic workflow."""

    claim_input: ClaimInput
    current_step: str = Field(default="intake", description="Current workflow step")
    extracted_evidence: Optional[ClaimEvidence] = None
    retrieved_policy: Optional[PolicyCoverage] = None
    draft_decision: Optional[ClaimDecisionOutput] = None
    tool_results: dict = Field(
        default_factory=dict, description="Results from tool calls"
    )
    error: Optional[str] = None
    requires_human_review: bool = Field(
        default=False, description="Whether human review is needed"
    )
