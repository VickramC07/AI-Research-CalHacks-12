"""
Chroma vector database client for ScholarForge.
Handles semantic search and embedding storage for paper sections.
"""

import chromadb
from chromadb.config import Settings
from typing import Dict, Any, List, Optional
import logging
import hashlib

from backend.config import (
    CHROMA_PERSIST_DIRECTORY,
    CHROMA_COLLECTION_NAME,
    CHROMA_SERVER_URL
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChromaClient:
    """Client for interacting with Chroma vector database."""

    def __init__(self):
        """Initialize Chroma client."""
        try:
            # Initialize Chroma client
            if CHROMA_SERVER_URL:
                # Client-server mode
                self.client = chromadb.HttpClient(
                    host=CHROMA_SERVER_URL.split("://")[1].split(":")[0],
                    port=int(CHROMA_SERVER_URL.split(":")[-1])
                )
                logger.info(f"Connected to remote Chroma server: {CHROMA_SERVER_URL}")
            else:
                # Persistent local mode
                self.client = chromadb.PersistentClient(
                    path=CHROMA_PERSIST_DIRECTORY,
                    settings=Settings(anonymized_telemetry=False)
                )
                logger.info(f"Initialized local Chroma DB at: {CHROMA_PERSIST_DIRECTORY}")

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=CHROMA_COLLECTION_NAME,
                metadata={"description": "Research paper sections for semantic search"}
            )
            logger.info(f"Loaded collection: {CHROMA_COLLECTION_NAME}")

        except Exception as e:
            logger.error(f"Error initializing Chroma client: {e}")
            raise

    def add_paper_section(
        self,
        paper_id: str,
        section_name: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> bool:
        """
        Add a paper section to the vector database.

        Args:
            paper_id: Unique paper identifier
            section_name: Name of the section (e.g., "abstract", "conclusion")
            content: Text content of the section
            metadata: Additional metadata (title, authors, year, etc.)
            embedding: Pre-computed embedding vector (optional, will be computed if not provided)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Generate unique document ID
            doc_id = self._generate_doc_id(paper_id, section_name)

            # Prepare metadata
            meta = metadata or {}
            meta.update({
                "paper_id": paper_id,
                "section_name": section_name
            })

            # Add to collection
            if embedding:
                self.collection.add(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[meta],
                    embeddings=[embedding]
                )
            else:
                # Let Chroma compute embeddings automatically
                self.collection.add(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[meta]
                )

            logger.info(f"Added section '{section_name}' for paper: {paper_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding paper section: {e}")
            return False

    def add_paper_sections_batch(
        self,
        paper_id: str,
        sections: Dict[str, str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add multiple sections from a paper in a single batch operation.

        Args:
            paper_id: Unique paper identifier
            sections: Dictionary mapping section names to content
            metadata: Common metadata for all sections

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            ids = []
            documents = []
            metadatas = []

            base_meta = metadata or {}

            for section_name, content in sections.items():
                if not content or not content.strip():
                    continue

                doc_id = self._generate_doc_id(paper_id, section_name)
                meta = base_meta.copy()
                meta.update({
                    "paper_id": paper_id,
                    "section_name": section_name
                })

                ids.append(doc_id)
                documents.append(content)
                metadatas.append(meta)

            if ids:
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                logger.info(f"Added {len(ids)} sections for paper: {paper_id}")
                return True
            else:
                logger.warning(f"No valid sections to add for paper: {paper_id}")
                return False

        except Exception as e:
            logger.error(f"Error adding paper sections batch: {e}")
            return False

    def semantic_search(
        self,
        query: str,
        n_results: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search for relevant paper sections.

        Args:
            query: Search query text
            n_results: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"section_name": "abstract"})

        Returns:
            List of matching paper sections with metadata and similarity scores
        """
        try:
            # Perform query
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filter_metadata
            )

            # Format results
            formatted_results = []
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    result = {
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if "distances" in results else None
                    }
                    formatted_results.append(result)

            logger.info(f"Found {len(formatted_results)} results for query: '{query[:50]}...'")
            return formatted_results

        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            return []

    def get_paper_sections(self, paper_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all sections for a specific paper.

        Args:
            paper_id: Paper identifier

        Returns:
            List of paper sections
        """
        try:
            results = self.collection.get(
                where={"paper_id": paper_id}
            )

            sections = []
            if results["ids"]:
                for i in range(len(results["ids"])):
                    section = {
                        "id": results["ids"][i],
                        "content": results["documents"][i],
                        "metadata": results["metadatas"][i]
                    }
                    sections.append(section)

            logger.info(f"Retrieved {len(sections)} sections for paper: {paper_id}")
            return sections

        except Exception as e:
            logger.error(f"Error retrieving paper sections: {e}")
            return []

    def delete_paper(self, paper_id: str) -> bool:
        """
        Delete all sections for a paper.

        Args:
            paper_id: Paper identifier

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.collection.delete(
                where={"paper_id": paper_id}
            )
            logger.info(f"Deleted all sections for paper: {paper_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting paper sections: {e}")
            return False

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.

        Returns:
            Dictionary with collection stats
        """
        try:
            count = self.collection.count()
            return {
                "name": CHROMA_COLLECTION_NAME,
                "document_count": count,
                "persist_directory": CHROMA_PERSIST_DIRECTORY
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}

    def _generate_doc_id(self, paper_id: str, section_name: str) -> str:
        """
        Generate a unique document ID for a paper section.

        Args:
            paper_id: Paper identifier
            section_name: Section name

        Returns:
            Unique document ID
        """
        combined = f"{paper_id}_{section_name}"
        return hashlib.md5(combined.encode()).hexdigest()

    def reset_collection(self) -> bool:
        """
        Delete and recreate the collection (WARNING: deletes all data).

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.client.delete_collection(name=CHROMA_COLLECTION_NAME)
            self.collection = self.client.create_collection(
                name=CHROMA_COLLECTION_NAME,
                metadata={"description": "Research paper sections for semantic search"}
            )
            logger.warning(f"Reset collection: {CHROMA_COLLECTION_NAME}")
            return True

        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            return False


# Singleton instance
_chroma_client = None


def get_chroma_client() -> ChromaClient:
    """Get or create Chroma client singleton."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = ChromaClient()
    return _chroma_client
