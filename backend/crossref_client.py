"""
Crossref API client for ScholarForge.
Fetches papers from Crossref's extensive database of scholarly works.
"""

import requests
from typing import Dict, Any, List, Optional
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CrossrefClient:
    """Client for fetching papers from Crossref API."""

    def __init__(self):
        """Initialize Crossref client."""
        self.base_url = "https://api.crossref.org"
        self.headers = {
            "User-Agent": "ScholarForge/2.0 (Research Tool; mailto:scholarforge@research.tool)"
        }
        logger.info("Initialized Crossref client")

    def search_papers(
        self,
        query: str,
        max_results: int = 10,
        min_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search Crossref for papers matching the query.

        Args:
            query: Search query
            max_results: Maximum number of papers to return
            min_year: Minimum publication year

        Returns:
            List of paper dictionaries
        """
        try:
            logger.info(f"Searching Crossref for: '{query}' (max {max_results} results)")

            # Build query parameters
            url = f"{self.base_url}/works"
            params = {
                "query": query,
                "rows": min(max_results, 20),
                "sort": "relevance",
                "filter": "type:journal-article"
            }

            # Add year filter if specified
            if min_year:
                params["filter"] += f",from-pub-date:{min_year}"

            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            items = data.get("message", {}).get("items", [])

            # Format papers
            papers = []
            for item in items:
                paper = self._format_paper(item)
                if paper:
                    papers.append(paper)

            logger.info(f"Retrieved {len(papers)} papers from Crossref")
            return papers

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from Crossref: {e}")
            return []
        except Exception as e:
            logger.error(f"Error processing Crossref results: {e}")
            return []

    def _format_paper(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Format Crossref item into standardized paper dictionary.

        Args:
            item: Raw item from Crossref API

        Returns:
            Formatted paper dictionary
        """
        try:
            # Extract DOI
            doi = item.get("DOI", "")
            if not doi:
                return None

            # Extract title
            title_list = item.get("title", [])
            title = title_list[0] if title_list else ""

            if not title:
                return None

            # Extract abstract
            abstract = item.get("abstract", "")
            if not abstract:
                abstract = title  # Use title if no abstract

            # Extract authors
            authors_data = item.get("author", [])
            authors_list = []
            for author in authors_data:
                given = author.get("given", "")
                family = author.get("family", "")
                if family:
                    name = f"{given} {family}".strip()
                    authors_list.append(name)

            authors = "; ".join(authors_list) if authors_list else "Unknown Authors"

            # Extract year
            pub_date = item.get("published-print") or item.get("published-online") or item.get("created")
            year = 0
            if pub_date and "date-parts" in pub_date:
                date_parts = pub_date["date-parts"][0]
                if date_parts:
                    year = int(date_parts[0])

            # Extract journal/venue
            container_title = item.get("container-title", [])
            venue = container_title[0] if container_title else "Crossref"

            # Extract field from subject
            subjects = item.get("subject", [])
            field = subjects[0].lower().replace(" ", "_") if subjects else "general"

            # URL
            url = item.get("URL", f"https://doi.org/{doi}")

            # Citation count
            citations = item.get("is-referenced-by-count", 0)

            # Create paper dictionary
            paper = {
                "paper_id": f"crossref_{doi.replace('/', '_')}",
                "title": title,
                "authors": authors,
                "year": year,
                "venue": venue,
                "field": field,
                "abstract": abstract,
                "full_text": abstract,
                "url": url,
                "doi": doi,
                "citations": citations,
                "published": "",
                "sections": {
                    "abstract": abstract,
                    "introduction": "",
                    "conclusion": "",
                    "future_work": "",
                    "limitations": ""
                },
                "source_api": "crossref"
            }

            return paper

        except Exception as e:
            logger.error(f"Error formatting Crossref paper: {e}")
            return None


# Singleton instance
_crossref_client = None


def get_crossref_client() -> CrossrefClient:
    """Get or create CrossrefClient singleton."""
    global _crossref_client
    if _crossref_client is None:
        _crossref_client = CrossrefClient()
    return _crossref_client
