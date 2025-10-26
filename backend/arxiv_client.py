"""
arXiv API client for ScholarForge.
Fetches research papers from arXiv based on queries.
"""

import arxiv
from typing import Dict, Any, List, Optional
import logging
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArxivClient:
    """Client for fetching papers from arXiv API."""

    def __init__(self):
        """Initialize arXiv client."""
        self.client = arxiv.Client()
        logger.info("Initialized arXiv client")

    def search_papers(
        self,
        query: str,
        max_results: int = 10,
        sort_by: arxiv.SortCriterion = arxiv.SortCriterion.Relevance
    ) -> List[Dict[str, Any]]:
        """
        Search arXiv for papers matching the query.

        Args:
            query: Search query (topic, keywords, etc.)
            max_results: Maximum number of papers to return
            sort_by: Sort criterion (Relevance, LastUpdatedDate, SubmittedDate)

        Returns:
            List of paper dictionaries with metadata and content
        """
        try:
            logger.info(f"Searching arXiv for: '{query}' (max {max_results} results)")

            # Create search
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=sort_by
            )

            # Fetch results
            papers = []
            for result in self.client.results(search):
                paper = self._format_paper(result)
                papers.append(paper)

            logger.info(f"Retrieved {len(papers)} papers from arXiv")
            return papers

        except Exception as e:
            logger.error(f"Error searching arXiv: {e}")
            return []

    def get_paper_by_id(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific paper by its arXiv ID.

        Args:
            arxiv_id: arXiv ID (e.g., "2301.12345" or "cs/0001234")

        Returns:
            Paper dictionary or None if not found
        """
        try:
            search = arxiv.Search(id_list=[arxiv_id])
            result = next(self.client.results(search))
            return self._format_paper(result)

        except Exception as e:
            logger.error(f"Error fetching paper {arxiv_id}: {e}")
            return None

    def _format_paper(self, result: arxiv.Result) -> Dict[str, Any]:
        """
        Format arXiv result into standardized paper dictionary.

        Args:
            result: arXiv API result object

        Returns:
            Formatted paper dictionary
        """
        # Generate paper ID
        paper_id = f"arxiv_{result.entry_id.split('/')[-1]}"

        # Extract authors
        authors = "; ".join([author.name for author in result.authors])

        # Extract categories/field
        categories = result.categories
        primary_category = result.primary_category
        field = self._categorize_field(primary_category)

        # Extract abstract and create sections
        abstract = result.summary.replace("\n", " ").strip()

        # Extract year from published date
        year = result.published.year

        # PDF link
        pdf_url = result.pdf_url

        # Create sections dictionary
        sections = {
            "abstract": abstract,
            "introduction": "",  # arXiv API doesn't provide full text sections
            "conclusion": "",
            "future_work": "",
            "limitations": ""
        }

        # Try to extract future work mentions from abstract
        future_work_keywords = ["future work", "future research", "future direction", "further research", "next step"]
        limitations_keywords = ["limitation", "challenge", "drawback", "constraint"]

        abstract_lower = abstract.lower()
        if any(keyword in abstract_lower for keyword in future_work_keywords):
            # Extract sentences mentioning future work
            sentences = re.split(r'[.!?]', abstract)
            future_sentences = [s.strip() for s in sentences
                              if any(kw in s.lower() for kw in future_work_keywords)]
            sections["future_work"] = ". ".join(future_sentences)

        if any(keyword in abstract_lower for keyword in limitations_keywords):
            # Extract sentences mentioning limitations
            sentences = re.split(r'[.!?]', abstract)
            limitation_sentences = [s.strip() for s in sentences
                                   if any(kw in s.lower() for kw in limitations_keywords)]
            sections["limitations"] = ". ".join(limitation_sentences)

        # Format paper
        paper = {
            "paper_id": paper_id,
            "title": result.title,
            "authors": authors,
            "year": year,
            "venue": "arXiv",  # arXiv is the venue
            "field": field,
            "abstract": abstract,
            "full_text": abstract,  # Use abstract as full text (full PDF parsing would require additional tools)
            "url": result.entry_id,
            "pdf_url": pdf_url,
            "doi": result.doi if result.doi else "",
            "categories": categories,
            "primary_category": primary_category,
            "published": result.published.isoformat(),
            "updated": result.updated.isoformat(),
            "sections": sections
        }

        return paper

    def _categorize_field(self, primary_category: str) -> str:
        """
        Categorize arXiv category into broader field.

        Args:
            primary_category: arXiv primary category (e.g., "cs.AI", "physics.quant-ph")

        Returns:
            Broader field category
        """
        category_map = {
            "cs.AI": "artificial_intelligence",
            "cs.LG": "machine_learning",
            "cs.CL": "natural_language_processing",
            "cs.CV": "computer_vision",
            "cs.CR": "cryptography",
            "cs.DB": "databases",
            "cs.DC": "distributed_computing",
            "cs.DS": "data_structures",
            "cs.NE": "neural_networks",
            "cs.RO": "robotics",
            "stat.ML": "machine_learning",
            "quant-ph": "quantum_computing",
            "physics.comp-ph": "computational_physics",
            "q-bio": "computational_biology",
            "eess.SP": "signal_processing",
            "math.OC": "optimization",
        }

        # Try exact match first
        if primary_category in category_map:
            return category_map[primary_category]

        # Try prefix match (e.g., "cs.*" -> "computer_science")
        prefix = primary_category.split(".")[0]
        prefix_map = {
            "cs": "computer_science",
            "stat": "statistics",
            "math": "mathematics",
            "physics": "physics",
            "q-bio": "biology",
            "econ": "economics",
            "eess": "electrical_engineering"
        }

        return prefix_map.get(prefix, "general")

    def search_by_category(
        self,
        category: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search papers by arXiv category.

        Args:
            category: arXiv category (e.g., "cs.AI", "cs.LG")
            max_results: Maximum number of results

        Returns:
            List of papers
        """
        query = f"cat:{category}"
        return self.search_papers(query, max_results)

    def search_recent_papers(
        self,
        query: str,
        max_results: int = 10,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Search for recent papers (last N days).

        Args:
            query: Search query
            max_results: Maximum results
            days: Look back N days

        Returns:
            List of recent papers
        """
        # arXiv API doesn't support date filtering in query directly
        # So we fetch more results and filter by date
        all_papers = self.search_papers(
            query,
            max_results=max_results * 2,  # Fetch more to account for filtering
            sort_by=arxiv.SortCriterion.LastUpdatedDate
        )

        # Filter by recency
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days)

        recent_papers = []
        for paper in all_papers:
            published_str = paper.get("published", "")
            if published_str:
                published_date = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                if published_date.replace(tzinfo=None) >= cutoff_date:
                    recent_papers.append(paper)

            if len(recent_papers) >= max_results:
                break

        logger.info(f"Filtered to {len(recent_papers)} papers from last {days} days")
        return recent_papers


# Singleton instance
_arxiv_client = None


def get_arxiv_client() -> ArxivClient:
    """Get or create ArxivClient singleton."""
    global _arxiv_client
    if _arxiv_client is None:
        _arxiv_client = ArxivClient()
    return _arxiv_client
