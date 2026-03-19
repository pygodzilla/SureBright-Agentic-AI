"""Policy retrieval tool using RAG."""

from typing import Optional
from langchain_core.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun

from src.rag.policy_rag import PolicyRAGPipeline


class PolicyRetrieverTool(BaseTool):
    """Tool for retrieving warranty policy information using RAG."""

    name: str = "policy_retriever"
    description: str = """
    Retrieve warranty policy information for a product category and damage type.
    Use this to check coverage terms, exclusions, and claim requirements.
    
    Input should include: product category, damage type, and damage description.
    """

    def __init__(self, rag_pipeline: Optional[PolicyRAGPipeline] = None):
        """Initialize with optional RAG pipeline."""
        super().__init__()
        self._rag_pipeline = rag_pipeline

    @property
    def rag_pipeline(self) -> PolicyRAGPipeline:
        """Lazy load RAG pipeline."""
        if self._rag_pipeline is None:
            self._rag_pipeline = PolicyRAGPipeline()
        return self._rag_pipeline

    def _run(
        self, run_input: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> dict:
        """Synchronous policy retrieval."""
        # Parse input - expected format: "category | damage_type | description"
        parts = run_input.split("|")
        if len(parts) < 3:
            parts = run_input.split(";")

        product_category = parts[0].strip() if len(parts) > 0 else "general"
        damage_type = parts[1].strip() if len(parts) > 1 else "unknown"
        damage_description = parts[2].strip() if len(parts) > 2 else run_input

        try:
            result = self.rag_pipeline.get_coverage_determination(
                product_category=product_category,
                damage_type=damage_type,
                damage_description=damage_description,
            )
            return result
        except Exception as e:
            return {
                "error": str(e),
                "context_used": "",
                "coverage_analysis": "Unable to retrieve policy information.",
            }

    async def _arun(
        self, run_input: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> dict:
        """Asynchronous policy retrieval."""
        return self._run(run_input, run_manager)


def create_policy_retriever(
    rag_pipeline: Optional[PolicyRAGPipeline] = None,
) -> PolicyRetrieverTool:
    """Factory function to create policy retriever tool."""
    return PolicyRetrieverTool(rag_pipeline=rag_pipeline)
