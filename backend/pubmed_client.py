"""
PubMed API client for ScholarForge.
Fetches biomedical and life sciences research papers.
"""

import requests
from typing import Dict, Any, List, Optional
import logging
import time
from xml.etree import ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PubMedClient:
    """Client for fetching papers from PubMed API."""

    def __init__(self):
        """Initialize PubMed client."""
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.tool = "ScholarForge"
        self.email = "scholarforge@research.tool"
        logger.info("Initialized PubMed client")

    def search_papers(
        self,
        query: str,
        max_results: int = 10,
        min_year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search PubMed for papers matching the query.

        Args:
            query: Search query
            max_results: Maximum number of papers to return
            min_year: Minimum publication year (for recent papers)

        Returns:
            List of paper dictionaries
        """
        try:
            logger.info(f"Searching PubMed for: '{query}' (max {max_results} results)")

            # Add year filter if specified
            if min_year:
                query = f"{query} AND {min_year}[PDAT]:3000[PDAT]"

            # Step 1: Search to get PMIDs
            search_url = f"{self.base_url}/esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance",
                "tool": self.tool,
                "email": self.email
            }

            search_response = requests.get(search_url, params=search_params, timeout=10)
            search_response.raise_for_status()
            search_data = search_response.json()

            pmids = search_data.get("esearchresult", {}).get("idlist", [])

            if not pmids:
                logger.warning("No papers found on PubMed")
                return []

            logger.info(f"Found {len(pmids)} PMIDs, fetching details...")

            # Step 2: Fetch details for PMIDs
            time.sleep(0.34)  # Rate limiting: 3 requests per second
            fetch_url = f"{self.base_url}/efetch.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "tool": self.tool,
                "email": self.email
            }

            fetch_response = requests.get(fetch_url, params=fetch_params, timeout=15)
            fetch_response.raise_for_status()

            # Parse XML response
            papers = self._parse_pubmed_xml(fetch_response.text)

            logger.info(f"Retrieved {len(papers)} papers from PubMed")
            return papers

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching from PubMed: {e}")
            return []
        except Exception as e:
            logger.error(f"Error processing PubMed results: {e}")
            return []

    def _parse_pubmed_xml(self, xml_text: str) -> List[Dict[str, Any]]:
        """
        Parse PubMed XML response into paper dictionaries.

        Args:
            xml_text: XML response from PubMed

        Returns:
            List of formatted papers
        """
        papers = []

        try:
            root = ET.fromstring(xml_text)

            for article in root.findall(".//PubmedArticle"):
                try:
                    paper = self._parse_article(article)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    logger.warning(f"Error parsing PubMed article: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing PubMed XML: {e}")

        return papers

    def _parse_article(self, article: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse a single PubMed article."""
        try:
            # Extract PMID
            pmid_elem = article.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else "unknown"

            # Extract title
            title_elem = article.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else ""

            if not title:
                return None

            # Extract abstract
            abstract_parts = article.findall(".//AbstractText")
            abstract = " ".join([
                part.text for part in abstract_parts
                if part.text is not None
            ])

            if not abstract:
                abstract = title  # Use title if no abstract

            # Extract authors
            authors_list = []
            for author in article.findall(".//Author"):
                last_name = author.find("LastName")
                first_name = author.find("ForeName")
                if last_name is not None:
                    name = last_name.text
                    if first_name is not None:
                        name = f"{first_name.text} {name}"
                    authors_list.append(name)

            authors = "; ".join(authors_list) if authors_list else "Unknown Authors"

            # Extract year
            year_elem = article.find(".//PubDate/Year")
            year = int(year_elem.text) if year_elem is not None else 0

            # Extract journal
            journal_elem = article.find(".//Journal/Title")
            venue = journal_elem.text if journal_elem is not None else "PubMed"

            # Create paper dictionary
            paper = {
                "paper_id": f"pubmed_{pmid}",
                "title": title,
                "authors": authors,
                "year": year,
                "venue": venue,
                "field": "biomedical",
                "abstract": abstract,
                "full_text": abstract,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "doi": "",
                "citations": 0,
                "published": "",
                "sections": {
                    "abstract": abstract,
                    "introduction": "",
                    "conclusion": "",
                    "future_work": "",
                    "limitations": ""
                },
                "source_api": "pubmed"
            }

            return paper

        except Exception as e:
            logger.error(f"Error parsing article: {e}")
            return None


# Singleton instance
_pubmed_client = None


def get_pubmed_client() -> PubMedClient:
    """Get or create PubMedClient singleton."""
    global _pubmed_client
    if _pubmed_client is None:
        _pubmed_client = PubMedClient()
    return _pubmed_client
