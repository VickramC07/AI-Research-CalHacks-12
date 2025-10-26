"""
Elastic Search client for ScholarForge.
Handles paper metadata storage and keyword-based search.
"""

from elasticsearch import Elasticsearch
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from backend.config import (
    ELASTIC_API_KEY,
    ELASTIC_URL,
    PAPERS_INDEX,
    FUTURE_WORK_INDEX
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ElasticClient:
    """Client for interacting with Elasticsearch for paper storage and retrieval."""

    def __init__(self):
        """Initialize Elasticsearch client with credentials."""
        try:
            self.client = Elasticsearch(
                ELASTIC_URL,
                api_key=ELASTIC_API_KEY,
                verify_certs=True
            )

            # Test connection
            if self.client.ping():
                logger.info("Successfully connected to Elasticsearch")
            else:
                logger.error("Failed to connect to Elasticsearch")

            # Create indices if they don't exist
            self._create_indices()

        except Exception as e:
            logger.error(f"Error initializing Elasticsearch client: {e}")
            raise

    def _create_indices(self):
        """Create Elasticsearch indices for papers and future work if they don't exist."""

        # Papers index mapping
        papers_mapping = {
            "mappings": {
                "properties": {
                    "paper_id": {"type": "keyword"},
                    "title": {"type": "text", "analyzer": "english"},
                    "authors": {"type": "text"},
                    "year": {"type": "integer"},
                    "venue": {"type": "text"},
                    "field": {"type": "keyword"},
                    "abstract": {"type": "text", "analyzer": "english"},
                    "full_text": {"type": "text", "analyzer": "english"},
                    "url": {"type": "keyword"},
                    "doi": {"type": "keyword"},
                    "citations": {"type": "integer"},
                    "created_at": {"type": "date"}
                }
            }
        }

        # Future work index mapping
        future_work_mapping = {
            "mappings": {
                "properties": {
                    "paper_id": {"type": "keyword"},
                    "paper_title": {"type": "text"},
                    "section_name": {"type": "keyword"},
                    "content": {"type": "text", "analyzer": "english"},
                    "limitations": {"type": "text", "analyzer": "english"},
                    "future_directions": {"type": "text", "analyzer": "english"},
                    "keywords": {"type": "keyword"},
                    "created_at": {"type": "date"}
                }
            }
        }

        # Create papers index
        try:
            if not self.client.indices.exists(index=PAPERS_INDEX):
                self.client.indices.create(index=PAPERS_INDEX, body=papers_mapping)
                logger.info(f"Created index: {PAPERS_INDEX}")
            else:
                logger.info(f"Index already exists: {PAPERS_INDEX}")
        except Exception as e:
            logger.error(f"Error creating papers index: {e}")

        # Create future work index
        try:
            if not self.client.indices.exists(index=FUTURE_WORK_INDEX):
                self.client.indices.create(index=FUTURE_WORK_INDEX, body=future_work_mapping)
                logger.info(f"Created index: {FUTURE_WORK_INDEX}")
            else:
                logger.info(f"Index already exists: {FUTURE_WORK_INDEX}")
        except Exception as e:
            logger.error(f"Error creating future work index: {e}")

    def insert_paper_metadata(self, paper_data: Dict[str, Any]) -> bool:
        """
        Insert paper metadata into Elasticsearch.

        Args:
            paper_data: Dictionary containing paper metadata
                Required fields: title, authors, abstract
                Optional fields: year, venue, field, url, doi, citations

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add timestamp
            paper_data["created_at"] = datetime.utcnow()

            # Generate paper_id if not provided
            if "paper_id" not in paper_data:
                paper_data["paper_id"] = f"paper_{datetime.utcnow().timestamp()}"

            # Insert into Elasticsearch
            response = self.client.index(
                index=PAPERS_INDEX,
                id=paper_data["paper_id"],
                document=paper_data
            )

            logger.info(f"Inserted paper: {paper_data.get('title', 'Unknown')}")
            return response["result"] in ["created", "updated"]

        except Exception as e:
            logger.error(f"Error inserting paper metadata: {e}")
            return False

    def insert_future_work(self, future_work_data: Dict[str, Any]) -> bool:
        """
        Insert future work section into Elasticsearch.

        Args:
            future_work_data: Dictionary containing future work information
                Required fields: paper_id, content
                Optional fields: limitations, future_directions, keywords

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add timestamp
            future_work_data["created_at"] = datetime.utcnow()

            # Insert into Elasticsearch
            response = self.client.index(
                index=FUTURE_WORK_INDEX,
                document=future_work_data
            )

            logger.info(f"Inserted future work for paper: {future_work_data.get('paper_id', 'Unknown')}")
            return response["result"] in ["created", "updated"]

        except Exception as e:
            logger.error(f"Error inserting future work: {e}")
            return False

    def search_papers(
        self,
        query: str,
        fields: List[str] = None,
        size: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for papers using keyword-based search.

        Args:
            query: Search query string
            fields: List of fields to search in (default: title, abstract, full_text)
            size: Number of results to return
            filters: Additional filters (e.g., year, field)

        Returns:
            List of matching papers
        """
        if fields is None:
            fields = ["title^3", "abstract^2", "full_text"]

        try:
            # Build query
            search_query = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": fields,
                                    "type": "best_fields"
                                }
                            }
                        ]
                    }
                },
                "size": size
            }

            # Add filters if provided
            if filters:
                filter_clauses = []
                for field, value in filters.items():
                    filter_clauses.append({"term": {field: value}})
                search_query["query"]["bool"]["filter"] = filter_clauses

            # Execute search
            response = self.client.search(index=PAPERS_INDEX, body=search_query)

            # Extract results
            results = []
            for hit in response["hits"]["hits"]:
                paper = hit["_source"]
                paper["_score"] = hit["_score"]
                results.append(paper)

            logger.info(f"Found {len(results)} papers for query: {query}")
            return results

        except Exception as e:
            logger.error(f"Error searching papers: {e}")
            return []

    def query_future_work(
        self,
        query: str,
        size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query future work sections based on keywords.

        Args:
            query: Search query string
            size: Number of results to return

        Returns:
            List of matching future work sections
        """
        try:
            search_query = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["content^2", "limitations", "future_directions", "keywords^3"],
                        "type": "best_fields"
                    }
                },
                "size": size
            }

            response = self.client.search(index=FUTURE_WORK_INDEX, body=search_query)

            # Extract results
            results = []
            for hit in response["hits"]["hits"]:
                future_work = hit["_source"]
                future_work["_score"] = hit["_score"]
                results.append(future_work)

            logger.info(f"Found {len(results)} future work sections for query: {query}")
            return results

        except Exception as e:
            logger.error(f"Error querying future work: {e}")
            return []

    def get_paper_by_id(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a paper by its ID.

        Args:
            paper_id: Paper identifier

        Returns:
            Paper data or None if not found
        """
        try:
            response = self.client.get(index=PAPERS_INDEX, id=paper_id)
            return response["_source"]
        except Exception as e:
            logger.error(f"Error retrieving paper {paper_id}: {e}")
            return None

    def delete_paper(self, paper_id: str) -> bool:
        """
        Delete a paper from the index.

        Args:
            paper_id: Paper identifier

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.client.delete(index=PAPERS_INDEX, id=paper_id)
            logger.info(f"Deleted paper: {paper_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting paper {paper_id}: {e}")
            return False

    def close(self):
        """Close the Elasticsearch client connection."""
        try:
            self.client.close()
            logger.info("Closed Elasticsearch connection")
        except Exception as e:
            logger.error(f"Error closing Elasticsearch connection: {e}")


# Singleton instance
_elastic_client = None


def get_elastic_client() -> ElasticClient:
    """Get or create Elasticsearch client singleton."""
    global _elastic_client
    if _elastic_client is None:
        _elastic_client = ElasticClient()
    return _elastic_client
