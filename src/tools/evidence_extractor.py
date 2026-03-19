"""Evidence extraction tool for claims processing."""

from typing import Optional
from pydantic import Field

from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun

from src.schemas.claim_schemas import ClaimInput, ClaimEvidence, DamageType


class EvidenceExtractorInput(BaseModel):
    """Input schema for evidence extraction tool."""

    claim_input: ClaimInput = Field(..., description="The original claim input")
    customer_history: Optional[str] = Field(
        None, description="Customer claim history if available"
    )


class EvidenceExtractorTool(BaseTool):
    """Tool for extracting evidence from claim submissions."""

    name: str = "evidence_extractor"
    description: str = """
    Extract key information and evidence from a warranty claim.
    Use this to parse claim forms, extract product info, dates, and damage descriptions.
    
    Input should be the claim text/description to analyze.
    """

    def _run(
        self, run_input: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> dict:
        """Synchronous evidence extraction."""
        # Simulated evidence extraction logic
        # In production, this would use LLM with vision for images

        evidence = ClaimEvidence(
            product_model=self._extract_product_model(run_input),
            purchase_date=self._extract_date(run_input, "purchase"),
            damage_date=self._extract_date(run_input, "damage"),
            damage_type=self._classify_damage(run_input),
            damage_description=self._extract_damage_description(run_input),
            images_provided="image" in run_input.lower()
            or "photo" in run_input.lower(),
            receipt_provided="receipt" in run_input.lower()
            or "invoice" in run_input.lower(),
        )

        return evidence.model_dump()

    async def _arun(
        self, run_input: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> dict:
        """Asynchronous evidence extraction."""
        return self._run(run_input, run_manager)

    def _extract_product_model(self, text: str) -> Optional[str]:
        """Extract product model/serial number from text."""
        import re

        patterns = [
            r"Model[:\s]+([A-Z0-9\-]+)",
            r"Serial[:\s]+([A-Z0-9\-]+)",
            r"Product[:\s]+(.+?)(?:\n|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_date(self, text: str, date_type: str) -> Optional[str]:
        """Extract dates from text."""
        import re

        patterns = [
            rf"{date_type}[\s]+(?:date[:\s]+)?(\d{{1,2}}[/\-]\d{{1,2}}[/\-]\d{{2,4}})",
            rf"(\d{{1,2}}[/\-]\d{{1,2}}[/\-]\d{{2,4}})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _classify_damage(self, text: str) -> DamageType:
        """Classify damage type from description."""
        text_lower = text.lower()

        if any(
            word in text_lower
            for word in ["defect", "faulty", "malfunction", "not working"]
        ):
            return DamageType.MANUFACTURING_DEFECT
        elif any(
            word in text_lower for word in ["dropped", "cracked", "spilled", "accident"]
        ):
            return DamageType.ACCIDENTAL_DAMAGE
        elif any(
            word in text_lower for word in ["shipping", "delivery", "arrived damaged"]
        ):
            return DamageType.SHIPPING_DAMAGE
        elif any(
            word in text_lower for word in ["worn", "scratched", "faded", "normal use"]
        ):
            return DamageType.NORMAL_WEAR
        return DamageType.UNKNOWN

    def _extract_damage_description(self, text: str) -> Optional[str]:
        """Extract damage description from text."""
        import re

        patterns = [
            r"Description[:\s]+(.+?)(?:\n|$)",
            r"Issue[:\s]+(.+?)(?:\n|$)",
            r"Problem[:\s]+(.+?)(?:\n|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Return first 200 chars as description
        return text[:200] if len(text) > 200 else text


def create_evidence_extractor() -> EvidenceExtractorTool:
    """Factory function to create evidence extractor tool."""
    return EvidenceExtractorTool()
