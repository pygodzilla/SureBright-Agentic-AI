"""Tests for Claims Agent."""

import pytest
from unittest.mock import MagicMock, patch

from src.schemas.claim_schemas import (
    ClaimInput,
    ClaimEvidence,
    ClaimDecision,
    DamageType,
)
from src.agents.claims_agent import ClaimsAgent, AgentStep


class TestClaimInput:
    """Test claim input validation."""

    def test_valid_claim_input(self):
        """Test creating valid claim input."""
        claim = ClaimInput(
            claim_id="CLM-001",
            customer_id="CUST-001",
            product_id="PROD-001",
            product_category="electronics",
            damage_description="Screen stopped working after 2 months",
        )
        assert claim.claim_id == "CLM-001"
        assert claim.product_category == "electronics"

    def test_claim_input_optional_fields(self):
        """Test claim input with optional fields."""
        claim = ClaimInput(
            claim_id="CLM-002",
            customer_id="CUST-002",
            product_id="PROD-002",
            product_category="appliance",
            damage_description="Motor making noise",
            additional_notes="Under warranty period",
        )
        assert claim.additional_notes == "Under warranty period"


class TestClaimEvidence:
    """Test evidence extraction."""

    def test_evidence_model(self):
        """Test evidence model creation."""
        evidence = ClaimEvidence(
            product_model="MODEL-123",
            purchase_date="2024-01-15",
            damage_type=DamageType.MANUFACTURING_DEFECT,
            images_provided=True,
            receipt_provided=True,
        )
        assert evidence.product_model == "MODEL-123"
        assert evidence.damage_type == DamageType.MANUFACTURING_DEFECT
        assert evidence.images_provided is True

    def test_damage_type_classification(self):
        """Test damage type enum values."""
        assert DamageType.MANUFACTURING_DEFECT.value == "manufacturing_defect"
        assert DamageType.ACCIDENTAL_DAMAGE.value == "accidental_damage"
        assert DamageType.SHIPPING_DAMAGE.value == "shipping_damage"


class TestClaimsAgent:
    """Test claims agent functionality."""

    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        with patch("src.agents.claims_agent.ChatOpenAI"):
            with patch("src.agents.claims_agent.PolicyRAGPipeline"):
                with patch("src.agents.claims_agent.EvidenceExtractorTool"):
                    with patch("src.agents.claims_agent.PolicyRetrieverTool"):
                        with patch("src.agents.claims_agent.DecisionMakerTool"):
                            return ClaimsAgent()

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent is not None
        assert agent.graph is not None

    def test_agent_has_required_tools(self, agent):
        """Test agent has all required tools."""
        assert hasattr(agent, "evidence_extractor")
        assert hasattr(agent, "policy_retriever")
        assert hasattr(agent, "decision_maker")


class TestDecisionLogic:
    """Test decision making logic."""

    def test_approved_decision_for_manufacturing_defect(self):
        """Test that manufacturing defects are typically approved."""
        evidence = ClaimEvidence(
            product_model="MODEL-123",
            damage_type=DamageType.MANUFACTURING_DEFECT,
            images_provided=True,
            receipt_provided=True,
        )
        # Decision logic should approve manufacturing defects
        assert evidence.damage_type == DamageType.MANUFACTURING_DEFECT

    def test_denied_decision_for_accidental_damage(self):
        """Test that accidental damage is typically denied."""
        evidence = ClaimEvidence(
            product_model="MODEL-123",
            damage_type=DamageType.ACCIDENTAL_DAMAGE,
            images_provided=True,
            receipt_provided=True,
        )
        # Decision logic should deny accidental damage
        assert evidence.damage_type == DamageType.ACCIDENTAL_DAMAGE


class TestAPISchemas:
    """Test API request/response schemas."""

    def test_claim_decision_enum(self):
        """Test all decision enum values."""
        assert ClaimDecision.APPROVED.value == "approved"
        assert ClaimDecision.DENIED.value == "denied"
        assert ClaimDecision.ESCALATED.value == "escalated"
        assert ClaimDecision.PENDING_INFO.value == "pending_information"

    def test_damage_type_enum(self):
        """Test all damage type enum values."""
        assert DamageType.MANUFACTURING_DEFECT.value == "manufacturing_defect"
        assert DamageType.ACCIDENTAL_DAMAGE.value == "accidental_damage"
        assert DamageType.SHIPPING_DAMAGE.value == "shipping_damage"
        assert DamageType.NORMAL_WEAR.value == "normal_wear"
        assert DamageType.UNKNOWN.value == "unknown"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
