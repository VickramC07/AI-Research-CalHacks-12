"""
Data ingestion module for ScholarForge.
Handles parsing and uploading paper metadata and text to Elastic and Chroma.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import re

from backend.elastic_client import get_elastic_client
from backend.chroma_client import get_chroma_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaperIngestor:
    """Handles ingestion of research papers into Elastic and Chroma."""

    def __init__(self):
        """Initialize the paper ingestor with clients."""
        self.elastic = get_elastic_client()
        self.chroma = get_chroma_client()
        logger.info("Initialized PaperIngestor")

    def ingest_paper(
        self,
        paper_data: Dict[str, Any],
        sections: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Ingest a single paper into both Elastic and Chroma.

        Args:
            paper_data: Dictionary containing paper metadata
                Required: title, abstract
                Optional: authors, year, venue, field, url, doi, citations, full_text, sections
            sections: Dictionary mapping section names to content
                e.g., {"abstract": "...", "conclusion": "...", "future_work": "..."}
                If None, will use paper_data["sections"] if available

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Extract sections from paper_data if not provided separately
            if sections is None and "sections" in paper_data:
                sections = paper_data.pop("sections")

            # Generate paper ID if not provided
            paper_id = paper_data.get("paper_id")
            if not paper_id:
                paper_id = self._generate_paper_id(paper_data.get("title", ""))
                paper_data["paper_id"] = paper_id

            # Validate required fields
            if not paper_data.get("title") or not paper_data.get("abstract"):
                logger.error("Paper must have at least title and abstract")
                return False

            # Check if paper already exists (avoid duplicates)
            existing = self.elastic.get_paper_by_id(paper_id)
            if existing:
                logger.info(f"Paper already exists, skipping: {paper_id}")
                return True

            # 1. Insert metadata into Elastic
            elastic_success = self.elastic.insert_paper_metadata(paper_data)
            if not elastic_success:
                logger.error(f"Failed to insert paper metadata into Elastic: {paper_id}")
                return False

            # 2. Insert sections into Chroma for semantic search
            if sections:
                chroma_success = self._ingest_sections_to_chroma(
                    paper_id,
                    sections,
                    paper_data
                )
                if not chroma_success:
                    logger.warning(f"Failed to insert sections into Chroma: {paper_id}")
            else:
                # If no sections provided, use abstract as default
                default_sections = {"abstract": paper_data.get("abstract", "")}
                self._ingest_sections_to_chroma(paper_id, default_sections, paper_data)

            # 3. Extract and store future work sections in Elastic
            if sections and ("future_work" in sections or "limitations" in sections):
                self._ingest_future_work(paper_id, sections, paper_data)

            logger.info(f"Successfully ingested paper: {paper_data.get('title')}")
            return True

        except Exception as e:
            logger.error(f"Error ingesting paper: {e}")
            return False

    def ingest_arxiv_papers(
        self,
        papers: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Ingest papers from arXiv (already formatted by arxiv_client).

        Args:
            papers: List of paper dictionaries from arxiv_client

        Returns:
            Dictionary with success/failure counts
        """
        logger.info(f"Ingesting {len(papers)} papers from arXiv")
        return self.ingest_papers_batch(papers)

    def ingest_papers_batch(
        self,
        papers: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Ingest multiple papers in batch.

        Args:
            papers: List of paper dictionaries with metadata and sections

        Returns:
            Dictionary with success/failure counts
        """
        results = {"success": 0, "failed": 0}

        for paper in papers:
            sections = paper.pop("sections", None)  # Extract sections if present
            success = self.ingest_paper(paper, sections)

            if success:
                results["success"] += 1
            else:
                results["failed"] += 1

        logger.info(f"Batch ingestion complete: {results['success']} succeeded, {results['failed']} failed")
        return results

    def _ingest_sections_to_chroma(
        self,
        paper_id: str,
        sections: Dict[str, str],
        paper_data: Dict[str, Any]
    ) -> bool:
        """Ingest paper sections into Chroma vector database."""
        try:
            # Prepare metadata for all sections
            metadata = {
                "title": paper_data.get("title", ""),
                "authors": paper_data.get("authors", ""),
                "year": paper_data.get("year", 0),
                "field": paper_data.get("field", ""),
                "venue": paper_data.get("venue", "")
            }

            # Add sections to Chroma
            success = self.chroma.add_paper_sections_batch(
                paper_id=paper_id,
                sections=sections,
                metadata=metadata
            )

            return success

        except Exception as e:
            logger.error(f"Error ingesting sections to Chroma: {e}")
            return False

    def _ingest_future_work(
        self,
        paper_id: str,
        sections: Dict[str, str],
        paper_data: Dict[str, Any]
    ) -> bool:
        """Extract and ingest future work sections into Elastic."""
        try:
            future_work_data = {
                "paper_id": paper_id,
                "paper_title": paper_data.get("title", ""),
                "content": sections.get("future_work", ""),
                "limitations": sections.get("limitations", ""),
                "future_directions": sections.get("future_work", ""),
                "keywords": self._extract_keywords(
                    sections.get("future_work", "") + " " + sections.get("limitations", "")
                )
            }

            return self.elastic.insert_future_work(future_work_data)

        except Exception as e:
            logger.error(f"Error ingesting future work: {e}")
            return False

    def _generate_paper_id(self, title: str) -> str:
        """Generate a unique paper ID from title."""
        # Clean title and create ID
        clean_title = re.sub(r'[^a-z0-9]+', '_', title.lower())
        timestamp = str(int(datetime.utcnow().timestamp()))
        return f"paper_{clean_title[:30]}_{timestamp}"

    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract keywords from text using simple frequency analysis."""
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'this', 'that', 'these', 'those', 'we', 'our', 'will', 'can'
        }

        # Tokenize and count
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        word_freq = {}

        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency and return top N
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_n]]

    def create_sample_papers(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Create sample papers for testing (mock data).

        Args:
            count: Number of sample papers to create

        Returns:
            List of sample paper dictionaries
        """
        samples = [
            {
                "title": "Efficient Quantum Simulation using SU(3) Lattice Gauge Theory",
                "authors": "Smith, J.; Johnson, A.; Williams, B.",
                "year": 2023,
                "venue": "Nature Physics",
                "field": "quantum_computing",
                "abstract": "We present a novel approach to quantum simulation using SU(3) lattice gauge theory. Our method demonstrates significant improvements in scalability and efficiency compared to existing techniques.",
                "sections": {
                    "abstract": "We present a novel approach to quantum simulation using SU(3) lattice gauge theory. Our method demonstrates significant improvements in scalability and efficiency compared to existing techniques.",
                    "introduction": "Quantum simulation has emerged as one of the most promising applications of quantum computers. However, current approaches face significant scalability challenges.",
                    "conclusion": "Our results demonstrate the potential of SU(3) lattice gauge theory for efficient quantum simulation. We achieve a 10x improvement in runtime compared to baseline methods.",
                    "future_work": "Future work should focus on developing more efficient state stitching methods for large-scale systems and exploring hybrid variational-adiabatic protocols.",
                    "limitations": "The current implementation is limited by measurement overhead and lacks efficient stitching methods for systems beyond 100 qubits."
                },
                "doi": "10.1038/np.2023.001",
                "citations": 45
            },
            {
                "title": "Transformer Interpretability: Understanding Attention Mechanisms",
                "authors": "Chen, L.; Zhang, M.; Kumar, R.",
                "year": 2024,
                "venue": "NeurIPS",
                "field": "machine_learning",
                "abstract": "This paper explores interpretability techniques for transformer models, focusing on attention mechanism visualization and analysis. We propose novel methods for understanding what transformers learn.",
                "sections": {
                    "abstract": "This paper explores interpretability techniques for transformer models, focusing on attention mechanism visualization and analysis. We propose novel methods for understanding what transformers learn.",
                    "introduction": "Transformer models have achieved remarkable success across various domains, yet understanding their internal mechanisms remains challenging.",
                    "conclusion": "We demonstrate that attention patterns reveal meaningful semantic relationships and task-specific learned features.",
                    "future_work": "Future research should investigate interpretability in larger models and develop automated tools for attention pattern analysis.",
                    "limitations": "Current analysis is limited to models with fewer than 10B parameters. Scaling to larger models requires more efficient visualization techniques."
                },
                "doi": "10.5555/neurips.2024.002",
                "citations": 23
            },
            {
                "title": "Scalable Vector Databases for Modern AI Applications",
                "authors": "Anderson, P.; Taylor, S.",
                "year": 2024,
                "venue": "VLDB",
                "field": "databases",
                "abstract": "We present a scalable architecture for vector databases optimized for AI workloads. Our system handles billions of high-dimensional vectors with sub-millisecond query latency.",
                "sections": {
                    "abstract": "We present a scalable architecture for vector databases optimized for AI workloads. Our system handles billions of high-dimensional vectors with sub-millisecond query latency.",
                    "introduction": "As AI applications scale, the need for efficient vector similarity search has become critical. Traditional database systems are not optimized for this workload.",
                    "conclusion": "Our architecture demonstrates linear scalability up to 10 billion vectors while maintaining high query performance.",
                    "future_work": "Future directions include supporting dynamic embeddings, multi-vector queries, and integration with federated learning systems.",
                    "limitations": "The system currently supports only L2 and cosine similarity metrics. Other distance functions require architectural modifications."
                },
                "doi": "10.14778/vldb.2024.003",
                "citations": 18
            },
            {
                "title": "Federated Learning with Differential Privacy Guarantees",
                "authors": "Martinez, C.; Lee, K.; Brown, D.",
                "year": 2023,
                "venue": "ICML",
                "field": "machine_learning",
                "abstract": "This work proposes a federated learning framework with formal differential privacy guarantees. We achieve strong privacy protection while maintaining model accuracy.",
                "sections": {
                    "abstract": "This work proposes a federated learning framework with formal differential privacy guarantees. We achieve strong privacy protection while maintaining model accuracy.",
                    "introduction": "Federated learning enables collaborative model training without centralizing data. However, privacy concerns remain a significant challenge.",
                    "conclusion": "Our framework provides epsilon-delta differential privacy while achieving 95% of centralized model accuracy.",
                    "future_work": "Future work should address heterogeneous device capabilities and develop adaptive privacy budget allocation mechanisms.",
                    "limitations": "The approach incurs 20-30% communication overhead compared to standard federated learning. More efficient aggregation protocols are needed."
                },
                "doi": "10.5555/icml.2023.004",
                "citations": 67
            },
            {
                "title": "Graph Neural Networks for Drug Discovery",
                "authors": "Wang, X.; Patel, N.; Garcia, M.",
                "year": 2023,
                "venue": "Nature Machine Intelligence",
                "field": "computational_biology",
                "abstract": "We apply graph neural networks to molecular property prediction and demonstrate state-of-the-art results on drug discovery benchmarks.",
                "sections": {
                    "abstract": "We apply graph neural networks to molecular property prediction and demonstrate state-of-the-art results on drug discovery benchmarks.",
                    "introduction": "Drug discovery is a time-consuming and expensive process. Machine learning methods offer the potential to accelerate early-stage screening.",
                    "conclusion": "Our GNN architecture achieves 15% improvement over previous methods on molecular property prediction tasks.",
                    "future_work": "Future directions include incorporating 3D molecular structure, protein-ligand interaction modeling, and multi-task learning across related properties.",
                    "limitations": "Current models are limited to molecules with known structural data. Predicting properties for novel scaffolds remains challenging."
                },
                "doi": "10.1038/nmi.2023.005",
                "citations": 89
            }
        ]

        return samples[:count]


# Singleton instance
_paper_ingestor = None


def get_paper_ingestor() -> PaperIngestor:
    """Get or create PaperIngestor singleton."""
    global _paper_ingestor
    if _paper_ingestor is None:
        _paper_ingestor = PaperIngestor()
    return _paper_ingestor
