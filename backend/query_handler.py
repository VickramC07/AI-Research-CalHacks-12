"""
Query handler for ScholarForge.
Coordinates retrieval from Elastic and Chroma, then synthesizes results using Claude.
"""

from typing import Dict, Any, List, Optional
import logging

from backend.elastic_client import get_elastic_client
from backend.chroma_client import get_chroma_client
from backend.claude_client import get_claude_client
from backend.arxiv_client import get_arxiv_client
from backend.data_ingestion import get_paper_ingestor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryHandler:
    """
    Handles user queries by coordinating retrieval and synthesis.

    This is the main interface for the Streamlit app and will be easily
    replaceable with Fetch.ai agents in the future.
    """

    def __init__(self, fetch_from_arxiv: bool = True):
        """
        Initialize query handler with all clients.

        Args:
            fetch_from_arxiv: If True, will fetch papers from arXiv when no local results found
        """
        self.elastic = get_elastic_client()
        self.chroma = get_chroma_client()
        self.claude = get_claude_client()
        self.arxiv = get_arxiv_client()
        self.ingestor = get_paper_ingestor()
        self.fetch_from_arxiv = fetch_from_arxiv
        logger.info(f"Initialized QueryHandler (arXiv fetching: {fetch_from_arxiv})")

    def query_research_gaps(
        self,
        topic: str,
        n_results: int = 10,
        use_semantic: bool = True,
        use_keyword: bool = True,
        relevance_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Main entry point for querying research gaps.

        This function:
        1. Retrieves relevant papers using Chroma (semantic) and/or Elastic (keyword)
        2. Filters by relevance threshold
        3. Sends results to Claude for analysis
        4. Returns structured response with gaps and future directions

        Args:
            topic: Research topic query
            n_results: Number of results to retrieve from each source
            use_semantic: Whether to use Chroma semantic search
            use_keyword: Whether to use Elastic keyword search
            relevance_threshold: Minimum similarity score (0-1) for semantic results

        Returns:
            Dictionary containing:
                - summary: Research gap summary
                - limitations: List of limitations
                - future_directions: List of future directions
                - keyword_trend: Keyword frequency data
                - papers: List of retrieved papers with metadata
        """
        try:
            logger.info(f"Processing query: {topic}")

            # 1. Retrieve relevant papers
            semantic_results = []
            keyword_results = []

            if use_semantic:
                raw_semantic = self._semantic_retrieval(topic, n_results)
                # Filter by relevance (distance threshold - lower is better for Chroma)
                semantic_results = [r for r in raw_semantic if r.get("distance", 1.0) < (1.0 - relevance_threshold)]
                logger.info(f"Retrieved {len(semantic_results)} relevant results from Chroma (filtered from {len(raw_semantic)})")

            if use_keyword:
                keyword_results = self._keyword_retrieval(topic, n_results)
                logger.info(f"Retrieved {len(keyword_results)} results from Elastic")

            # Check if we have any relevant results
            if not semantic_results and not keyword_results:
                logger.warning(f"No relevant results found locally for query: {topic}")

                # Try fetching from arXiv if enabled
                if self.fetch_from_arxiv:
                    logger.info("Attempting to fetch papers from arXiv...")
                    arxiv_papers = self._fetch_and_ingest_from_arxiv(topic, n_results=min(10, n_results))

                    if arxiv_papers > 0:
                        logger.info(f"Fetched and ingested {arxiv_papers} papers from arXiv. Re-searching...")
                        # Re-search after ingestion
                        if use_semantic:
                            raw_semantic = self._semantic_retrieval(topic, n_results)
                            semantic_results = [r for r in raw_semantic if r.get("distance", 1.0) < (1.0 - relevance_threshold)]
                            logger.info(f"Retrieved {len(semantic_results)} relevant results from Chroma after arXiv ingestion")

                        if use_keyword:
                            keyword_results = self._keyword_retrieval(topic, n_results)
                            logger.info(f"Retrieved {len(keyword_results)} results from Elastic after arXiv ingestion")

                # If still no results after arXiv fetch
                if not semantic_results and not keyword_results:
                    return self._empty_response(topic, reason="no_relevant_results")

            # 2. Analyze with Claude
            analysis = self.claude.analyze_research_gaps(
                topic=topic,
                paper_sections=semantic_results,
                elastic_results=keyword_results
            )

            # 3. Combine results
            papers = self._format_papers(semantic_results, keyword_results)

            result = {
                **analysis,
                "papers": papers,
                "retrieval_stats": {
                    "semantic_count": len(semantic_results),
                    "keyword_count": len(keyword_results),
                    "total_count": len(semantic_results) + len(keyword_results),
                    "papers_used": len(papers)
                }
            }

            logger.info(f"Successfully processed query: {topic}")
            return result

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return self._empty_response(topic, error=str(e))

    def _fetch_and_ingest_from_arxiv(
        self,
        query: str,
        n_results: int = 10
    ) -> int:
        """
        Fetch papers from arXiv and ingest them into local databases.

        Args:
            query: Search query
            n_results: Number of papers to fetch

        Returns:
            Number of papers successfully ingested
        """
        try:
            logger.info(f"Fetching papers from arXiv for query: '{query}'")

            # Fetch papers from arXiv
            arxiv_papers = self.arxiv.search_papers(query, max_results=n_results)

            if not arxiv_papers:
                logger.warning("No papers found on arXiv")
                return 0

            logger.info(f"Found {len(arxiv_papers)} papers on arXiv, ingesting...")

            # Ingest papers into Elastic and Chroma
            results = self.ingestor.ingest_arxiv_papers(arxiv_papers)

            logger.info(f"Ingested {results['success']} papers from arXiv ({results['failed']} failed)")
            return results['success']

        except Exception as e:
            logger.error(f"Error fetching from arXiv: {e}")
            return 0

    def _semantic_retrieval(
        self,
        query: str,
        n_results: int
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant paper sections using Chroma vector search."""
        try:
            results = self.chroma.semantic_search(
                query=query,
                n_results=n_results
            )
            return results
        except Exception as e:
            logger.error(f"Error in semantic retrieval: {e}")
            return []

    def _keyword_retrieval(
        self,
        query: str,
        n_results: int
    ) -> List[Dict[str, Any]]:
        """Retrieve papers using Elastic keyword search."""
        try:
            # Search in papers index
            papers = self.elastic.search_papers(
                query=query,
                size=n_results
            )

            # Also search future work sections
            future_work = self.elastic.query_future_work(
                query=query,
                size=n_results
            )

            # Combine results
            all_results = []

            # Add papers
            for paper in papers:
                all_results.append({
                    "type": "paper",
                    "title": paper.get("title", ""),
                    "abstract": paper.get("abstract", ""),
                    "content": paper.get("abstract", ""),
                    "metadata": paper,
                    "score": paper.get("_score", 0)
                })

            # Add future work sections
            for fw in future_work:
                all_results.append({
                    "type": "future_work",
                    "title": fw.get("paper_title", ""),
                    "content": fw.get("content", ""),
                    "limitations": fw.get("limitations", ""),
                    "future_directions": fw.get("future_directions", ""),
                    "metadata": fw,
                    "score": fw.get("_score", 0)
                })

            return all_results

        except Exception as e:
            logger.error(f"Error in keyword retrieval: {e}")
            return []

    def _format_papers(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Format and deduplicate paper results for display with full metadata."""
        papers = []
        seen_titles = set()

        # Process semantic results
        for result in semantic_results[:10]:  # Show more papers
            metadata = result.get("metadata", {})
            title = metadata.get("title", "Unknown")

            if title not in seen_titles and title != "Unknown":
                papers.append({
                    "title": title,
                    "authors": metadata.get("authors", "Unknown Authors"),
                    "year": metadata.get("year", "N/A"),
                    "venue": metadata.get("venue", ""),
                    "field": metadata.get("field", ""),
                    "section": metadata.get("section_name", ""),
                    "relevance_score": 1.0 - result.get("distance", 0),  # Convert distance to similarity
                    "content_preview": result.get("content", "")[:300] + "...",
                    "source": "semantic"
                })
                seen_titles.add(title)

        # Process keyword results
        for result in keyword_results[:10]:
            title = result.get("title", "Unknown")

            if title not in seen_titles and title != "Unknown":
                metadata = result.get("metadata", {})
                papers.append({
                    "title": title,
                    "authors": metadata.get("authors", "Unknown Authors"),
                    "year": metadata.get("year", "N/A"),
                    "venue": metadata.get("venue", ""),
                    "field": metadata.get("field", ""),
                    "relevance_score": result.get("score", 0) / 10.0,  # Normalize Elastic score
                    "content_preview": result.get("content", "")[:300] + "...",
                    "source": "keyword"
                })
                seen_titles.add(title)

        return papers

    def _empty_response(
        self,
        topic: str,
        error: Optional[str] = None,
        reason: str = "no_results"
    ) -> Dict[str, Any]:
        """Return empty response when no results found."""
        if reason == "no_relevant_results":
            message = f"No relevant research papers found for '{topic}'. The database may not contain papers on this specific topic."
        elif error:
            message = f"Error searching for '{topic}': {error}"
        else:
            message = f"No research papers found for '{topic}'. Try a different search term or add more papers to the database."

        return {
            "summary": message,
            "limitations": [],
            "future_directions": [],
            "keyword_trend": [],
            "papers": [],
            "retrieval_stats": {
                "semantic_count": 0,
                "keyword_count": 0,
                "total_count": 0,
                "papers_used": 0
            },
            "no_results": True
        }

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about indexed papers."""
        try:
            chroma_stats = self.chroma.get_collection_stats()

            # Get Elastic stats
            elastic_papers = self.elastic.search_papers("*", size=0)  # Just get count

            return {
                "chroma_documents": chroma_stats.get("document_count", 0),
                "elastic_papers": 0,  # Would need to implement count in elastic_client
                "status": "healthy"
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {
                "chroma_documents": 0,
                "elastic_papers": 0,
                "status": "error"
            }


# Singleton instance
_query_handler = None


def get_query_handler() -> QueryHandler:
    """Get or create QueryHandler singleton."""
    global _query_handler
    if _query_handler is None:
        _query_handler = QueryHandler()
    return _query_handler


# ============================================================================
# FUTURE: Fetch.ai Integration Layer
# ============================================================================

class FetchAgentInterface:
    """
    Interface for Fetch.ai agent integration.

    This class will replace QueryHandler's direct client calls with
    agent-based orchestration using Fetch.ai's Agentverse.

    TODO: Implement after deploying agents to Agentverse
    """

    def __init__(self, insight_agent_address: str):
        """
        Initialize Fetch.ai agent interface.

        Args:
            insight_agent_address: Address of the InsightAgent on Agentverse
        """
        self.insight_agent_address = insight_agent_address
        # TODO: Initialize Fetch.ai client
        pass

    async def query_via_agent(self, topic: str) -> Dict[str, Any]:
        """
        Query research gaps via Fetch.ai InsightAgent.

        The InsightAgent will:
        1. Receive the topic query
        2. Coordinate with IngestAgent for data retrieval
        3. Query Elastic and Chroma
        4. Call Claude API for synthesis
        5. Return structured results

        Args:
            topic: Research topic

        Returns:
            Analysis results from InsightAgent
        """
        # TODO: Implement agent communication
        # message = {
        #     "type": "research_query",
        #     "topic": topic,
        #     "timestamp": datetime.utcnow().isoformat()
        # }
        # response = await self.send_message_to_agent(
        #     self.insight_agent_address,
        #     message
        # )
        # return response
        pass
