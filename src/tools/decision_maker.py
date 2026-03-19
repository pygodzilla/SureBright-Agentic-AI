"""Decision making tool for claims adjudication."""

from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_openai import ChatOpenAI

from src.schemas.claim_schemas import (
    ClaimDecision,
    ClaimDecisionOutput,
    ClaimEvidence,
    PolicyCoverage,
    DamageType,
)
from src.config import settings


class DecisionMakerInput(BaseModel):
    """Input schema for decision making tool."""

    evidence: dict = Field(..., description="Extracted evidence from claim")
    policy_info: dict = Field(..., description="Retrieved policy information")
    claim_id: str = Field(..., description="Claim identifier")


class DecisionMakerTool(BaseTool):
    """Tool for making claims adjudication decisions."""

    name: str = "decision_maker"
    description: str = """
    Make a claim adjudication decision based on evidence and policy information.
    Returns structured decision with reasoning and confidence score.
    
    Input should be: evidence dict | policy info dict | claim_id
    """

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """Initialize with optional LLM."""
        super().__init__()
        self._llm = llm

    @property
    def llm(self) -> ChatOpenAI:
        """Lazy load LLM."""
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=0.0,  # Deterministic for decisions
            )
        return self._llm

    def _run(
        self, run_input: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> dict:
        """Make claims decision based on evidence and policy."""
        # Parse input
        parts = run_input.split("|")
        if len(parts) < 3:
            return {
                "error": "Invalid input format. Expected: evidence | policy_info | claim_id"
            }

        evidence_dict = (
            eval(parts[0].strip())
            if isinstance(parts[0].strip(), str)
            else parts[0].strip()
        )
        policy_info = (
            eval(parts[1].strip())
            if isinstance(parts[1].strip(), str)
            else parts[1].strip()
        )
        claim_id = parts[2].strip()

        # Create evidence object
        evidence = (
            ClaimEvidence(**evidence_dict)
            if isinstance(evidence_dict, dict)
            else evidence_dict
        )

        # Determine decision based on rules
        decision, confidence, reasoning = self._determine_decision(
            evidence, policy_info
        )

        # Check if escalation needed
        requires_escalation = (
            evidence.damage_type == DamageType.UNKNOWN
            or confidence < 0.7
            or evidence.product_model is None
            or not evidence.receipt_provided
        )

        # Build output
        output = ClaimDecisionOutput(
            decision=decision,
            confidence_score=confidence,
            reasoning=reasoning,
            evidence=evidence,
            policy_coverage=self._parse_policy_coverage(policy_info),
            required_actions=self._get_required_actions(decision, evidence),
            escalation_reason="High uncertainty - requires human review"
            if requires_escalation
            else None,
        )

        return output.model_dump()

    def _determine_decision(
        self, evidence: ClaimEvidence, policy_info: dict
    ) -> tuple[ClaimDecision, float, str]:
        """Determine claim decision based on evidence and policy."""
        # Rule-based decision logic (simplified)
        coverage_analysis = policy_info.get("coverage_analysis", "").lower()

        # Check if covered
        if "not covered" in coverage_analysis or "excluded" in coverage_analysis:
            return (
                ClaimDecision.DENIED,
                0.95,
                "Damage type is explicitly excluded from warranty coverage.",
            )

        # Check for required documentation
        missing_docs = []
        if not evidence.receipt_provided:
            missing_docs.append("proof of purchase")
        if not evidence.images_provided:
            missing_docs.append("photos of damage")

        if missing_docs:
            return (
                ClaimDecision.PENDING_INFO,
                0.6,
                f"Additional information required: {', '.join(missing_docs)}",
            )

        # Check damage type coverage
        damage_coverage_rules = {
            DamageType.MANUFACTURING_DEFECT: ("covered", 0.9),
            DamageType.SHIPPING_DAMAGE: ("covered", 0.85),
            DamageType.ACCIDENTAL_DAMAGE: ("not covered", 0.95),
            DamageType.NORMAL_WEAR: ("not covered", 0.9),
            DamageType.UNKNOWN: ("unknown", 0.5),
        }

        coverage_status, confidence = damage_coverage_rules.get(
            evidence.damage_type, ("unknown", 0.5)
        )

        if coverage_status == "covered":
            return (
                ClaimDecision.APPROVED,
                confidence,
                f"Claim approved: {evidence.damage_type.value} is covered under warranty.",
            )
        elif coverage_status == "not covered":
            return (
                ClaimDecision.DENIED,
                confidence,
                f"Claim denied: {evidence.damage_type.value} is not covered under warranty.",
            )
        else:
            return (
                ClaimDecision.ESCALATED,
                confidence,
                "Unable to determine coverage - escalated for human review.",
            )

    def _parse_policy_coverage(self, policy_info: dict) -> Optional[PolicyCoverage]:
        """Parse policy information into structured coverage object."""
        # Simplified parsing - in production would use LLM
        return PolicyCoverage(
            is_covered="not covered"
            not in policy_info.get("coverage_analysis", "").lower(),
            coverage_type="Standard Warranty",
            deductible_amount=25.0,
            max_coverage_amount=2000.0,
            excluded_items=["accidental damage", "misuse", "cosmetic damage"],
        )

    def _get_required_actions(
        self, decision: ClaimDecision, evidence: ClaimEvidence
    ) -> list[str]:
        """Get required actions based on decision."""
        actions = []

        if decision == ClaimDecision.PENDING_INFO:
            if not evidence.receipt_provided:
                actions.append("Submit proof of purchase")
            if not evidence.images_provided:
                actions.append("Submit photos of damage")

        elif decision == ClaimDecision.APPROVED:
            actions.append("Process reimbursement")
            actions.append("Send confirmation to customer")

        elif decision == ClaimDecision.DENIED:
            actions.append("Send denial letter with reason")
            actions.append("Offer appeal process")

        elif decision == ClaimDecision.ESCALATED:
            actions.append("Assign to senior claims adjuster")

        return actions

    async def _arun(
        self, run_input: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> dict:
        """Async version - delegate to sync."""
        return self._run(run_input, run_manager)


def create_decision_maker(llm: Optional[ChatOpenAI] = None) -> DecisionMakerTool:
    """Factory function to create decision maker tool."""
    return DecisionMakerTool(llm=llm)
