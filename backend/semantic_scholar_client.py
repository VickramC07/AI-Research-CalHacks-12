"""
Semantic Scholar API client for ScholarForge.
Fetches research papers from Semantic Scholar API as an alternative to arXiv.
"""

import requests
from typing import Dict, Any, List, Optional
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticScholarClient:
    """Client for fetching papers from Semantic Scholar API."""

    def __init__(self):
        """Initialize Semantic Scholar client."""
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.headers = {
            "User-Agent": "ScholarForge/2.0 (Research Tool)"
        }
        logger.info("Initialized Semantic Scholar client")

    def search_papers(
        self,
        query: str,
        max_results: int = 10,
        fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search Semantic Scholar for papers matching the query.

        Args:
            query: Search query (topic, keywords, etc.)
            max_results: Maximum number of papers to return
            fields: List of fields to retrieve

        Returns:
            List of paper dictionaries with metadata and content
        """
        if fields is None:
            fields = [
                "paperId", "title", "abstract", "year", "authors",
                "venue", "publicationDate", "citationCount",
                "externalIds", "url", "fieldsOfStudy"
            ]

        try:
            logger.info(f"Searching Semantic Scholar for: '{query}' (max {max_results} results)")

            # Make API request
            url = f"{self.base_url}/paper/search"
            params = {
                "query": query,
                "limit": min(max_results, 100),  # API limit
                "fields": ",".join(fields)
            }

            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            raw_papers = data.get("data", [])

            # Format papers
            papers = []
            for paper_data in raw_papers:
                paper = self._format_paper(paper_data)
                if paper:
                    papers.append(paper)

            logger.info(f"Retrieved {len(papers)} papers from Semantic Scholar")
            return papers

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from Semantic Scholar: {e}")
            return []
        except Exception as e:
            logger.error(f"Error processing Semantic Scholar results: {e}")
            return []

    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific paper by its Semantic Scholar ID.

        Args:
            paper_id: Semantic Scholar paper ID

        Returns:
            Paper dictionary or None if not found
        """
        try:
            url = f"{self.base_url}/paper/{paper_id}"
            params = {
                "fields": "paperId,title,abstract,year,authors,venue,publicationDate,citationCount,externalIds,url,fieldsOfStudy"
            }

            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()

            paper_data = response.json()
            return self._format_paper(paper_data)

        except Exception as e:
            logger.error(f"Error fetching paper {paper_id} from Semantic Scholar: {e}")
            return None

    def _format_paper(self, paper_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Format Semantic Scholar result into standardized paper dictionary.

        Args:
            paper_data: Raw paper data from Semantic Scholar API

        Returns:
            Formatted paper dictionary
        """
        try:
            # Extract basic info
            paper_id = f"s2_{paper_data.get('paperId', 'unknown')}"
            title = paper_data.get("title", "")
            abstract = paper_data.get("abstract", "")

            if not title or not abstract:
                return None

            # Extract authors
            authors_data = paper_data.get("authors", [])
            authors = "; ".join([a.get("name", "") for a in authors_data if a.get("name")])

            # Extract year
            year = paper_data.get("year")
            if not year:
                pub_date = paper_data.get("publicationDate", "")
                if pub_date:
                    try:
                        year = int(pub_date.split("-")[0])
                    except:
                        year = None

            # Extract venue
            venue = paper_data.get("venue", "Semantic Scholar")
            if not venue:
                venue = "Semantic Scholar"

            # Extract field
            fields_of_study = paper_data.get("fieldsOfStudy", [])
            if fields_of_study and len(fields_of_study) > 0:
                field = fields_of_study[0].lower().replace(" ", "_")
            else:
                field = "general"

            # Get external IDs (DOI, arXiv, etc.)
            external_ids = paper_data.get("externalIds", {})
            doi = external_ids.get("DOI", "")
            arxiv_id = external_ids.get("ArXiv", "")

            # URL
            url = paper_data.get("url", f"https://www.semanticscholar.org/paper/{paper_data.get('paperId')}")

            # Citation count
            citations = paper_data.get("citationCount", 0)

            # Create sections
            sections = {
                "abstract": abstract,
                "introduction": "",
                "conclusion": "",
                "future_work": "",
                "limitations": ""
            }

            # Format paper
            paper = {
                "paper_id": paper_id,
                "title": title,
                "authors": authors if authors else "Unknown Authors",
                "year": year if year else 0,
                "venue": venue,
                "field": field,
                "abstract": abstract,
                "full_text": abstract,  # Use abstract as full text
                "url": url,
                "doi": doi,
                "arxiv_id": arxiv_id,
                "citations": citations,
                "published": paper_data.get("publicationDate", ""),
                "sections": sections,
                "source_api": "semantic_scholar"
            }

            return paper

        except Exception as e:
            logger.error(f"Error formatting Semantic Scholar paper: {e}")
            return None

    def search_by_field(
        self,
        field: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search papers by field of study.

        Args:
            field: Field of study (e.g., "Computer Science", "Medicine")
            max_results: Maximum results

        Returns:
            List of papers
        """
        query = f"fieldsOfStudy:{field}"
        return self.search_papers(query, max_results)

    def search_recent_papers(
        self,
        query: str,
        max_results: int = 10,
        min_year: int = 2020
    ) -> List[Dict[str, Any]]:
        """
        Search for recent papers.

        Args:
            query: Search query
            max_results: Maximum results
            min_year: Minimum publication year

        Returns:
            List of recent papers
        """
        papers = self.search_papers(query, max_results=max_results * 2)

        # Filter by year
        recent_papers = [p for p in papers if p.get("year", 0) >= min_year]

        return recent_papers[:max_results]


# Singleton instance
_semantic_scholar_client = None


def get_semantic_scholar_client() -> SemanticScholarClient:
    """Get or create SemanticScholarClient singleton."""
    global _semantic_scholar_client
    if _semantic_scholar_client is None:
        _semantic_scholar_client = SemanticScholarClient()
    return _semantic_scholar_client
