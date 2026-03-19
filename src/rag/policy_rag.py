"""RAG pipeline for warranty policy retrieval."""

import os
from typing import Optional, AsyncGenerator
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config import settings


class PolicyRAGPipeline:
    """RAG pipeline for retrieving warranty policy information."""

    def __init__(
        self,
        embeddings: Optional[OpenAIEmbeddings] = None,
        vector_store: Optional[Chroma] = None,
    ):
        """Initialize RAG pipeline with embeddings and vector store."""
        self.embeddings = embeddings or OpenAIEmbeddings(
            model=settings.embedding_model, api_key=settings.openai_api_key
        )
        self.vector_store = vector_store
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.0,  # Deterministic for retrieval
        )

        # Retrieval prompt for warranty policies
        self.retrieval_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a warranty policy expert. Given the user's claim question, 
            retrieve relevant policy information to help determine coverage.
            
            Context from warranty policies:
            {context}
            
            User question: {question}
            
            Provide a concise answer based on the retrieved policy information.""",
                ),
                ("human", "{question}"),
            ]
        )

    def load_policies(self, policies_dir: str = "./data/policies") -> list[Document]:
        """Load warranty policy documents from directory."""
        policy_path = Path(policies_dir)
        if not policy_path.exists():
            # Create sample policies for demo
            self._create_sample_policies(policy_path)

        loader = DirectoryLoader(
            str(policy_path), glob="**/*.txt", loader_cls=TextLoader, show_progress=True
        )
        return loader.load()

    def _create_sample_policies(self, policy_path: Path) -> None:
        """Create sample warranty policies for demonstration."""
        policy_path.mkdir(parents=True, exist_ok=True)

        sample_policies = {
            "electronics_warranty.txt": """ELECTRONICS WARRANTY POLICY
            
            Coverage Period: 2 years from purchase date
            
            Covered Items:
            - Manufacturing defects in electronic components
            - Failure due to normal use
            - Power supply issues
            
            NOT Covered:
            - Accidental damage (drops, liquid damage)
            - Damage from unauthorized repairs
            - Cosmetic damage
            - Software issues
            
            Claim Process:
            1. Submit claim with proof of purchase
            2. Provide product serial number
            3. Describe the issue
            4. Submit photos of damage if applicable
            
            Deductible: $0 for manufacturing defects
            Maximum Coverage: Original purchase price
            """,
            "appliance_warranty.txt": """APPLIANCE WARRANTY POLICY
            
            Coverage Period: 1 year manufacturer + 1 year extended
            
            Covered Items:
            - Mechanical failures
            - Electrical component failures
            - Motor failures (unless from misuse)
            
            NOT Covered:
            - Cosmetic damage
            - Damage from improper installation
            - Commercial use limitations
            - Filters, bulbs, and consumables
            
            Claim Requirements:
            - Proof of purchase required
            - Product model number
            - Photos of the appliance
            - Description of malfunction
            
            Deductible: $25 for service calls
            Maximum Coverage: $2000 per claim
            """,
            "furniture_warranty.txt": """FURNITURE WARRANTY POLICY
            
            Coverage Period: 5 years structural, 1 year fabric
            
            Covered Items:
            - Structural defects (frame, joints)
            - Fabric defects under normal use
            - Leather cracking (not from misuse)
            - Mechanism failures (recliner, drawers)
            
            NOT Covered:
            - Damage from pets
            - Stains or spills (unless fabric protection purchased)
            - Misuse or overloading
            - Natural color fading
            
            Claim Process:
            1. Register purchase within 30 days
            2. Keep original receipt
            3. Provide photos of defect
            4. Allow inspection if requested
            
            Deductible: $0
            Maximum Coverage: Original purchase price
            """,
        }

        for filename, content in sample_policies.items():
            (policy_path / filename).write_text(content)

    def index_policies(self, policies_dir: str = "./data/policies") -> None:
        """Index warranty policies into vector store."""
        documents = self.load_policies(policies_dir)

        # Split documents
        chunks = self.text_splitter.split_documents(documents)

        # Create or update vector store
        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=settings.chroma_db_path,
        )

        # Persist for future use
        self.vector_store.persist()

    def retrieve_relevant_context(
        self, query: str, k: int = 5, filter_category: Optional[str] = None
    ) -> str:
        """Retrieve relevant policy context for a claim query."""
        if self.vector_store is None:
            # Try to load existing vector store
            if os.path.exists(settings.chroma_db_path):
                self.vector_store = Chroma(
                    persist_directory=settings.chroma_db_path,
                    embedding_function=self.embeddings,
                )
            else:
                # Index first
                self.index_policies()

        # Retrieve documents
        results = self.vector_store.similarity_search_with_score(
            query,
            k=k,
            filter={"category": filter_category} if filter_category else None,
        )

        # Format context
        context_parts = []
        for doc, score in results:
            context_parts.append(f"[Relevance: {1 - score:.2f}]\n{doc.page_content}")

        return "\n\n---\n\n".join(context_parts)

    def get_coverage_determination(
        self, product_category: str, damage_type: str, damage_description: str
    ) -> dict:
        """Get coverage determination based on product and damage info."""
        query = f"""
        Product Category: {product_category}
        Damage Type: {damage_type}
        Description: {damage_description}
        
        Is this damage covered under warranty? What are the specific terms?
        """

        context = self.retrieve_relevant_context(
            query, k=3, filter_category=product_category
        )

        # Generate answer using LLM
        chain = self.retrieval_prompt | self.llm | StrOutputParser()
        answer = chain.invoke({"context": context, "question": query})

        return {"context_used": context, "coverage_analysis": answer}


def create_rag_pipeline() -> PolicyRAGPipeline:
    """Factory function to create RAG pipeline."""
    return PolicyRAGPipeline()
