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
from backend.semantic_scholar_client import get_semantic_scholar_client
from backend.pubmed_client import get_pubmed_client
from backend.crossref_client import get_crossref_client
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

    def __init__(self, fetch_from_arxiv: bool = True, min_year: Optional[int] = 2020):
        """
        Initialize query handler with all clients.

        Args:
            fetch_from_arxiv: If True, will fetch papers from external sources when no local results found
            min_year: Minimum publication year for prioritizing recent papers (default: 2020)
        """
        self.elastic = get_elastic_client()
        self.chroma = get_chroma_client()
        self.claude = get_claude_client()
        self.arxiv = get_arxiv_client()
        self.semantic_scholar = get_semantic_scholar_client()
        self.pubmed = get_pubmed_client()
        self.crossref = get_crossref_client()
        self.ingestor = get_paper_ingestor()
        self.fetch_from_arxiv = fetch_from_arxiv
        self.min_year = min_year
        logger.info(f"Initialized QueryHandler (external fetching: {fetch_from_arxiv}, prioritizing papers >= {min_year})")

    def query_research_gaps(
        self,
        topic: str,
        n_results: int = 20,
        use_semantic: bool = True,
        use_keyword: bool = True,
        relevance_threshold: float = 0.7,
        use_two_stage: bool = True
    ) -> Dict[str, Any]:
        """
        Main entry point for querying research gaps.

        Two-Stage Hybrid Retrieval (when use_two_stage=True):
        1. Stage 1: Retrieve broad candidate set from Elasticsearch (keyword filtering)
        2. Stage 2: Re-rank candidates using ChromaDB semantic search
        3. Return top N semantically relevant papers

        Traditional Retrieval (when use_two_stage=False):
        1. Retrieve from Chroma (semantic) and/or Elastic (keyword) independently
        2. Combine and filter by relevance threshold
        3. Return merged results

        Args:
            topic: Research topic query
            n_results: Final number of results to return
            use_semantic: Whether to use Chroma semantic search
            use_keyword: Whether to use Elastic keyword search
            relevance_threshold: Minimum similarity score (0-1) for semantic results
            use_two_stage: Whether to use two-stage hybrid retrieval (recommended for large corpus)

        Returns:
            Dictionary containing:
                - summary: Research gap summary
                - limitations: List of limitations
                - future_directions: List of future directions
                - keyword_trend: Keyword frequency data
                - papers: List of retrieved papers with metadata
                - retrieval_method: "two_stage" or "traditional"
        """
        try:
            logger.info(f"Processing query: {topic}")

            # Choose retrieval strategy
            if use_two_stage and use_semantic and use_keyword:
                # TWO-STAGE HYBRID RETRIEVAL
                logger.info("Using two-stage hybrid retrieval (Elasticsearch → ChromaDB)")
                semantic_results, keyword_results = self._two_stage_retrieval(
                    topic,
                    final_k=n_results,
                    relevance_threshold=relevance_threshold
                )
                retrieval_method = "two_stage"
            else:
                # TRADITIONAL INDEPENDENT RETRIEVAL
                logger.info("Using traditional retrieval")
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

                retrieval_method = "traditional"

            # Check if we have any relevant results OR if we need more to reach minimum
            total_found = len(semantic_results) + len(keyword_results)
            min_required = max(10, n_results // 2)  # Be flexible - quality over quantity

            if total_found < min_required:
                logger.warning(f"Found {total_found} papers locally, need at least {min_required}")

                # Try fetching from external sources if enabled
                if self.fetch_from_arxiv:
                    needed = min_required - total_found

                    # Balanced fetching strategy for diversity:
                    # - 50% from arXiv (strong coverage)
                    # - 50% distributed among other sources
                    # - Guarantee at least 2-3 non-arXiv papers
                    arxiv_quota = max(needed // 2, needed - 3)  # At least leave room for 3 non-arXiv
                    other_quota = needed - arxiv_quota

                    logger.info(f"Fetching {needed} papers: {arxiv_quota} from arXiv, {other_quota} from other sources")

                    # Fetch from arXiv first (largest quota)
                    arxiv_fetched = self._fetch_and_ingest_from_arxiv(topic, n_results=arxiv_quota)
                    logger.info(f"Fetched {arxiv_fetched} papers from arXiv")

                    # Distribute remaining among other sources (round-robin)
                    other_sources = [
                        ("Semantic Scholar", self._fetch_and_ingest_from_semantic_scholar),
                        ("PubMed", self._fetch_and_ingest_from_pubmed),
                        ("Crossref", self._fetch_and_ingest_from_crossref)
                    ]

                    remaining = needed - arxiv_fetched
                    per_source = max(1, remaining // len(other_sources))
                    total_other = 0

                    for source_name, fetch_func in other_sources:
                        if remaining <= 0:
                            break
                        fetch_count = min(per_source, remaining)
                        logger.info(f"Attempting to fetch {fetch_count} papers from {source_name}...")
                        fetched = fetch_func(topic, n_results=fetch_count)
                        total_other += fetched
                        remaining -= fetched
                        logger.info(f"Fetched {fetched} papers from {source_name}")

                    total_fetched = arxiv_fetched + total_other
                    logger.info(f"Total fetched: {total_fetched} papers ({arxiv_fetched} arXiv, {total_other} other sources)")

                    if total_fetched > 0:
                        logger.info(f"Fetched and ingested {total_fetched} papers from external sources. Re-searching...")
                        # Re-search after ingestion
                        if use_semantic:
                            raw_semantic = self._semantic_retrieval(topic, n_results)
                            semantic_results = [r for r in raw_semantic if r.get("distance", 1.0) < (1.0 - relevance_threshold)]
                            logger.info(f"Retrieved {len(semantic_results)} relevant results from Chroma after external ingestion")

                        if use_keyword:
                            keyword_results = self._keyword_retrieval(topic, n_results)
                            logger.info(f"Retrieved {len(keyword_results)} results from Elastic after external ingestion")

                # If still no results after external fetches
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

            # 4. Check recent papers in final results (require at least 5 from after 2016)
            paper_years = [{"year": p.get("year", 0)} for p in papers]
            recent_check = self._check_recent_papers_simple(paper_years, min_recent=5, min_year=2017)

            # Add warning if insufficient recent papers
            if not recent_check["sufficient"]:
                warning_msg = f"⚠️ Only {recent_check['recent_count']} of {len(papers)} papers are from after 2016. "
                warning_msg += f"Consider searching for more recent research on this topic."
                analysis["recent_warning"] = warning_msg
                logger.warning(warning_msg)

            result = {
                **analysis,
                "papers": papers,
                "retrieval_stats": {
                    "semantic_count": len(semantic_results),
                    "keyword_count": len(keyword_results),
                    "total_count": len(semantic_results) + len(keyword_results),
                    "papers_used": len(papers)
                },
                "retrieval_method": retrieval_method
            }

            logger.info(f"Successfully processed query: {topic} (method: {retrieval_method})")
            return result

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return self._empty_response(topic, error=str(e))

    def _two_stage_retrieval(
        self,
        query: str,
        final_k: int = 10,
        stage1_candidates: int = 200,
        relevance_threshold: float = 0.7
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Perform two-stage hybrid retrieval for large corpus.

        Stage 1: Elasticsearch - Broad keyword-based filtering
        - Retrieve large candidate set (e.g., 200 papers)
        - Fast keyword matching on title, abstract, full_text
        - Filters by recency, relevance, etc.

        Stage 2: ChromaDB - Semantic re-ranking
        - Take Stage 1 candidates
        - Re-rank using semantic similarity
        - Return top K most semantically relevant

        This is much more efficient than semantic search over entire corpus!

        Args:
            query: Search query
            final_k: Final number of results to return
            stage1_candidates: Number of candidates to retrieve in Stage 1
            relevance_threshold: Minimum similarity for Stage 2

        Returns:
            Tuple of (semantic_results, keyword_results) for compatibility
        """
        logger.info(f"Stage 1: Retrieving {stage1_candidates} candidates from Elasticsearch...")

        # Stage 1: Get broad candidate set from Elasticsearch
        stage1_results = self._keyword_retrieval(query, n_results=stage1_candidates)

        if not stage1_results:
            logger.warning("No candidates from Stage 1")
            return ([], [])

        logger.info(f"Stage 1: Retrieved {len(stage1_results)} candidates")

        # Extract paper IDs from Stage 1
        candidate_ids = set()
        for result in stage1_results:
            paper_id = result.get("metadata", {}).get("paper_id")
            if not paper_id:
                # Try to get from result directly
                paper_id = result.get("paper_id")
            if paper_id:
                candidate_ids.add(paper_id)

        logger.info(f"Stage 2: Re-ranking {len(candidate_ids)} papers with ChromaDB...")
        logger.debug(f"Candidate IDs from Stage 1: {list(candidate_ids)[:5]}...")  # Show first 5

        # Stage 2: Semantic search, but filtered to Stage 1 candidates
        # Get more results from Chroma, then filter to candidates
        chroma_results = self._semantic_retrieval(query, n_results=stage1_candidates)

        # Filter to only include Stage 1 candidates
        # Note: For two-stage retrieval, we relax the threshold since Stage 1 already filtered
        filtered_results = []
        matched_ids = 0
        for result in chroma_results:
            paper_id = result.get("metadata", {}).get("paper_id")
            distance = result.get("distance", 1.0)

            if paper_id in candidate_ids:
                matched_ids += 1
                # Relaxed threshold for two-stage: accept distance < 0.8 (instead of 0.3)
                # Stage 1 already filtered, so we just need reasonable semantic similarity
                if distance < 0.8:
                    filtered_results.append(result)
                    logger.debug(f"  Accepted paper {paper_id} with distance {distance:.3f}")

        logger.info(f"Stage 2: Matched {matched_ids} papers in candidate set")
        logger.info(f"Stage 2: {len(filtered_results)} papers passed relevance filter (distance < 0.8)")

        # Sort by relevance (lower distance = more relevant)
        filtered_results.sort(key=lambda x: x.get("distance", 1.0))

        # Take top K
        final_results = filtered_results[:final_k]

        logger.info(f"Stage 2: Returning top {len(final_results)} semantically relevant papers")

        # Return in format expected by main function
        # semantic_results = Stage 2 output, keyword_results = Stage 1 output (for context)
        return (final_results, stage1_results[:50])  # Return subset of Stage 1 for context

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

    def _fetch_and_ingest_from_semantic_scholar(
        self,
        query: str,
        n_results: int = 10
    ) -> int:
        """
        Fetch papers from Semantic Scholar and ingest them into local databases.

        Args:
            query: Search query
            n_results: Number of papers to fetch

        Returns:
            Number of papers successfully ingested
        """
        try:
            logger.info(f"Fetching papers from Semantic Scholar for query: '{query}'")

            # Fetch papers from Semantic Scholar
            ss_papers = self.semantic_scholar.search_papers(query, max_results=n_results)

            if not ss_papers:
                logger.warning("No papers found on Semantic Scholar")
                return 0

            logger.info(f"Found {len(ss_papers)} papers on Semantic Scholar, ingesting...")

            # Ingest papers into Elastic and Chroma (reuse arXiv ingestion - same format)
            results = self.ingestor.ingest_arxiv_papers(ss_papers)

            logger.info(f"Ingested {results['success']} papers from Semantic Scholar ({results['failed']} failed)")
            return results['success']

        except Exception as e:
            logger.error(f"Error fetching from Semantic Scholar: {e}")
            return 0

    def _fetch_and_ingest_from_pubmed(
        self,
        query: str,
        n_results: int = 10
    ) -> int:
        """
        Fetch papers from PubMed and ingest them into local databases.

        Args:
            query: Search query
            n_results: Number of papers to fetch

        Returns:
            Number of papers successfully ingested
        """
        try:
            logger.info(f"Fetching papers from PubMed for query: '{query}'")

            # Fetch papers from PubMed, prioritizing recent years
            pubmed_papers = self.pubmed.search_papers(
                query,
                max_results=n_results,
                min_year=self.min_year
            )

            if not pubmed_papers:
                logger.warning("No papers found on PubMed")
                return 0

            logger.info(f"Found {len(pubmed_papers)} papers on PubMed, ingesting...")

            # Ingest papers into Elastic and Chroma
            results = self.ingestor.ingest_arxiv_papers(pubmed_papers)

            logger.info(f"Ingested {results['success']} papers from PubMed ({results['failed']} failed)")
            return results['success']

        except Exception as e:
            logger.error(f"Error fetching from PubMed: {e}")
            return 0

    def _fetch_and_ingest_from_crossref(
        self,
        query: str,
        n_results: int = 10
    ) -> int:
        """
        Fetch papers from Crossref and ingest them into local databases.

        Args:
            query: Search query
            n_results: Number of papers to fetch

        Returns:
            Number of papers successfully ingested
        """
        try:
            logger.info(f"Fetching papers from Crossref for query: '{query}'")

            # Fetch papers from Crossref, prioritizing recent years
            crossref_papers = self.crossref.search_papers(
                query,
                max_results=n_results,
                min_year=self.min_year
            )

            if not crossref_papers:
                logger.warning("No papers found on Crossref")
                return 0

            logger.info(f"Found {len(crossref_papers)} papers on Crossref, ingesting...")

            # Ingest papers into Elastic and Chroma
            results = self.ingestor.ingest_arxiv_papers(crossref_papers)

            logger.info(f"Ingested {results['success']} papers from Crossref ({results['failed']} failed)")
            return results['success']

        except Exception as e:
            logger.error(f"Error fetching from Crossref: {e}")
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

    def _check_recent_papers_simple(
        self,
        papers: List[Dict[str, Any]],
        min_recent: int = 5,
        min_year: int = 2017
    ) -> Dict[str, Any]:
        """
        Check if final papers contain enough recent papers.

        Args:
            papers: List of paper dictionaries with 'year' field
            min_recent: Minimum number of recent papers required
            min_year: Year threshold (papers >= this year are "recent")

        Returns:
            Dictionary with check results
        """
        recent_count = 0
        total_count = 0

        for paper in papers:
            year = paper.get("year", 0)

            if year and year > 0:
                total_count += 1
                if year >= min_year:
                    recent_count += 1

        sufficient = recent_count >= min_recent

        logger.info(f"Recent papers check (final): {recent_count}/{total_count} from {min_year}+ (need {min_recent})")

        return {
            "sufficient": sufficient,
            "recent_count": recent_count,
            "total_count": total_count,
            "min_year": min_year,
            "min_recent": min_recent
        }

    def _format_papers(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Format and deduplicate paper results for display with full metadata."""
        papers = []
        seen_titles = set()

        # Helper function to normalize Elastic scores to 0-1 range
        def normalize_elastic_score(score: float) -> float:
            """Normalize Elastic score to 0-1 using asymptotic function."""
            if score <= 0:
                return 0.0
            # Use function: score / (score + k) where k=10
            # This asymptotically approaches 1.0 as score increases
            return score / (score + 10.0)

        # Helper function to determine paper source
        def get_paper_source(metadata):
            venue = metadata.get("venue", "").lower()
            url = metadata.get("url", "").lower()

            # Determine source based on venue or URL
            if "arxiv" in venue or "arxiv.org" in url:
                return "arXiv"
            elif "pubmed" in venue or "pubmed.ncbi.nlm.nih.gov" in url:
                return "PubMed"
            elif "crossref" in venue or "doi.org" in url:
                return "Crossref"
            elif "semantic scholar" in venue or "semanticscholar" in url:
                return "Semantic Scholar"
            elif any(journal in venue for journal in ["ieee", "acm", "springer", "nature", "science", "elsevier"]):
                return metadata.get("venue", "Journal")
            elif any(conf in venue for conf in ["cvpr", "iclr", "neurips", "icml", "aaai", "acl"]):
                return metadata.get("venue", "Conference")
            elif venue and venue != "":
                return metadata.get("venue", "Other")
            else:
                return "Other"

        # Process semantic results (process more to account for duplicates)
        for result in semantic_results[:40]:
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
                    "source": get_paper_source(metadata),
                    "retrieval_method": "semantic"
                })
                seen_titles.add(title)

                # Stop if we have enough papers
                if len(papers) >= 20:
                    break

        # Process keyword results (only if we need more papers)
        if len(papers) < 20:
            for result in keyword_results[:40]:
                title = result.get("title", "Unknown")

                if title not in seen_titles and title != "Unknown":
                    metadata = result.get("metadata", {})
                    papers.append({
                        "title": title,
                        "authors": metadata.get("authors", "Unknown Authors"),
                        "year": metadata.get("year", "N/A"),
                        "venue": metadata.get("venue", ""),
                        "field": metadata.get("field", ""),
                        "relevance_score": normalize_elastic_score(result.get("score", 0)),
                        "content_preview": result.get("content", "")[:300] + "...",
                        "source": get_paper_source(metadata),
                        "retrieval_method": "keyword"
                    })
                    seen_titles.add(title)

                    # Stop if we have enough papers
                    if len(papers) >= 20:
                        break

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
