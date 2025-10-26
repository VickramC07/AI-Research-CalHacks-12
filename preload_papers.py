#!/usr/bin/env python3
"""
Bulk Paper Preload Script

This script preloads a large corpus of academic papers from arXiv into
Elasticsearch and ChromaDB for high-performance hybrid search.

Strategy:
1. Fetch papers from multiple arXiv categories
2. Index ALL papers into Elasticsearch (keyword search)
3. Selectively embed recent papers into ChromaDB (semantic search)
4. Use two-stage retrieval: ES for filtering → ChromaDB for re-ranking

Usage:
    python preload_papers.py --target 10000 --categories all
    python preload_papers.py --target 1000 --categories cs.AI,cs.LG
"""

import argparse
import logging
import time
from datetime import datetime
from typing import List, Dict, Any
import random

from backend.arxiv_client import get_arxiv_client
from backend.elastic_client import get_elastic_client
from backend.chroma_client import get_chroma_client
from backend.data_ingestion import get_paper_ingestor
from backend.config import (
    ARXIV_CATEGORIES,
    PAPERS_PER_CATEGORY,
    TARGET_CORPUS_SIZE,
    ELASTICSEARCH_BATCH_SIZE,
    CHROMADB_BATCH_SIZE,
    CHROMADB_EMBED_RATIO,
    CHROMADB_MIN_YEAR
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BulkPreloader:
    """Handles bulk preloading of papers from arXiv."""

    def __init__(self):
        """Initialize all clients."""
        self.arxiv = get_arxiv_client()
        self.elastic = get_elastic_client()
        self.chroma = get_chroma_client()
        self.ingestor = get_paper_ingestor()

        # Statistics
        self.stats = {
            "papers_fetched": 0,
            "papers_in_elastic": 0,
            "papers_in_chroma": 0,
            "errors": 0,
            "categories_processed": 0,
            "start_time": None,
            "end_time": None
        }

    def should_embed_in_chroma(self, paper: Dict[str, Any]) -> bool:
        """
        Determine if a paper should be embedded in ChromaDB.

        Strategy:
        - Only embed recent papers (>= CHROMADB_MIN_YEAR)
        - Only embed CHROMADB_EMBED_RATIO% of papers
        - This saves compute/storage while maintaining semantic search quality

        Args:
            paper: Paper dictionary

        Returns:
            bool: True if should embed, False otherwise
        """
        # Check year
        year = paper.get("year", 0)
        if year < CHROMADB_MIN_YEAR:
            return False

        # Random sampling based on ratio
        if random.random() > CHROMADB_EMBED_RATIO:
            return False

        return True

    def fetch_papers_for_category(
        self,
        category: str,
        max_papers: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch papers for a specific arXiv category.

        Args:
            category: arXiv category (e.g., "cs.AI")
            max_papers: Maximum number of papers to fetch

        Returns:
            List of paper dictionaries
        """
        logger.info(f"Fetching up to {max_papers} papers from category: {category}")

        try:
            papers = self.arxiv.search_by_category(
                category=category,
                max_results=max_papers
            )

            logger.info(f"Fetched {len(papers)} papers from {category}")
            return papers

        except Exception as e:
            logger.error(f"Error fetching papers from {category}: {e}")
            self.stats["errors"] += 1
            return []

    def ingest_batch(
        self,
        papers: List[Dict[str, Any]],
        embed_in_chroma: bool = True
    ) -> Dict[str, int]:
        """
        Ingest a batch of papers into Elasticsearch and optionally ChromaDB.

        Args:
            papers: List of paper dictionaries
            embed_in_chroma: Whether to embed in ChromaDB

        Returns:
            Dictionary with success/failure counts
        """
        elastic_success = 0
        chroma_success = 0

        # Split into batches for Elasticsearch
        for i in range(0, len(papers), ELASTICSEARCH_BATCH_SIZE):
            batch = papers[i:i + ELASTICSEARCH_BATCH_SIZE]

            # Ingest into Elasticsearch
            for paper in batch:
                try:
                    # Don't include sections in metadata (will be extracted)
                    sections = paper.pop("sections", None)

                    # Check if already exists
                    existing = self.elastic.get_paper_by_id(paper.get("paper_id"))
                    if existing:
                        logger.debug(f"Paper {paper['paper_id']} already exists, skipping")
                        continue

                    # Insert into Elastic
                    success = self.elastic.insert_paper_metadata(paper)
                    if success:
                        elastic_success += 1

                        # Selectively embed in ChromaDB
                        if embed_in_chroma and self.should_embed_in_chroma(paper):
                            # Re-add sections for ChromaDB
                            if sections:
                                chroma_sections = {k: v for k, v in sections.items() if v}
                                if chroma_sections:
                                    metadata = {
                                        "title": paper.get("title", ""),
                                        "authors": paper.get("authors", ""),
                                        "year": paper.get("year", 0),
                                        "field": paper.get("field", "")
                                    }
                                    self.chroma.add_paper_sections_batch(
                                        paper_id=paper["paper_id"],
                                        sections=chroma_sections,
                                        metadata=metadata
                                    )
                                    chroma_success += 1

                    # Re-add sections if needed
                    if sections:
                        paper["sections"] = sections

                except Exception as e:
                    logger.error(f"Error ingesting paper {paper.get('paper_id', 'unknown')}: {e}")
                    self.stats["errors"] += 1

            # Small delay between batches
            time.sleep(0.1)

        return {
            "elastic": elastic_success,
            "chroma": chroma_success
        }

    def preload_corpus(
        self,
        target_papers: int,
        categories: List[str] = None
    ):
        """
        Preload a large corpus of papers from arXiv.

        Args:
            target_papers: Target number of papers to preload
            categories: List of arXiv categories to fetch from
        """
        if categories is None:
            categories = ARXIV_CATEGORIES

        logger.info("="*80)
        logger.info("BULK PAPER PRELOAD")
        logger.info("="*80)
        logger.info(f"Target: {target_papers} papers")
        logger.info(f"Categories: {len(categories)}")
        logger.info(f"Elasticsearch batches: {ELASTICSEARCH_BATCH_SIZE}")
        logger.info(f"ChromaDB embedding ratio: {CHROMADB_EMBED_RATIO:.1%}")
        logger.info(f"ChromaDB min year: {CHROMADB_MIN_YEAR}")
        logger.info("="*80)

        self.stats["start_time"] = datetime.now()

        # Calculate papers per category
        papers_per_cat = min(PAPERS_PER_CATEGORY, target_papers // len(categories) + 1)

        # Fetch and ingest papers by category
        for category in categories:
            try:
                logger.info(f"\n📁 Processing category: {category}")

                # Fetch papers
                papers = self.fetch_papers_for_category(category, papers_per_cat)

                if not papers:
                    logger.warning(f"No papers fetched for {category}")
                    continue

                self.stats["papers_fetched"] += len(papers)

                # Ingest in batches
                logger.info(f"Ingesting {len(papers)} papers...")
                results = self.ingest_batch(papers, embed_in_chroma=True)

                self.stats["papers_in_elastic"] += results["elastic"]
                self.stats["papers_in_chroma"] += results["chroma"]
                self.stats["categories_processed"] += 1

                logger.info(f"✅ Ingested: {results['elastic']} → Elastic, {results['chroma']} → Chroma")

                # Check if reached target
                if self.stats["papers_in_elastic"] >= target_papers:
                    logger.info(f"\n🎯 Reached target of {target_papers} papers!")
                    break

                # Progress update
                progress = (self.stats["papers_in_elastic"] / target_papers) * 100
                logger.info(f"Progress: {progress:.1f}% ({self.stats['papers_in_elastic']}/{target_papers})")

                # Rate limiting
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error processing category {category}: {e}")
                self.stats["errors"] += 1
                continue

        self.stats["end_time"] = datetime.now()
        self._print_summary()

    def _print_summary(self):
        """Print final statistics."""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        logger.info("\n" + "="*80)
        logger.info("PRELOAD COMPLETE")
        logger.info("="*80)
        logger.info(f"📥 Papers fetched from arXiv: {self.stats['papers_fetched']}")
        logger.info(f"📊 Papers in Elasticsearch: {self.stats['papers_in_elastic']}")
        logger.info(f"🧠 Papers in ChromaDB: {self.stats['papers_in_chroma']}")
        logger.info(f"📁 Categories processed: {self.stats['categories_processed']}")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        logger.info(f"⏱️  Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")

        if self.stats["papers_in_elastic"] > 0:
            logger.info(f"⚡ Rate: {self.stats['papers_in_elastic']/duration:.1f} papers/second")
            logger.info(f"📈 ChromaDB ratio: {self.stats['papers_in_chroma']/self.stats['papers_in_elastic']:.1%}")

        logger.info("="*80)
        logger.info("\n✅ Your corpus is ready for two-stage hybrid search!")
        logger.info("   Run: streamlit run app.py")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Preload academic papers from arXiv for hybrid search"
    )
    parser.add_argument(
        "--target",
        type=int,
        default=TARGET_CORPUS_SIZE,
        help=f"Target number of papers (default: {TARGET_CORPUS_SIZE})"
    )
    parser.add_argument(
        "--categories",
        type=str,
        default="all",
        help="Comma-separated arXiv categories or 'all' (default: all)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: fetch only 100 papers"
    )

    args = parser.parse_args()

    # Parse categories
    if args.categories == "all":
        categories = ARXIV_CATEGORIES
    else:
        categories = [cat.strip() for cat in args.categories.split(",")]

    # Test mode
    if args.test:
        target = 100
        logger.info("🧪 TEST MODE: Fetching only 100 papers")
    else:
        target = args.target

    # Run preload
    preloader = BulkPreloader()

    try:
        preloader.preload_corpus(
            target_papers=target,
            categories=categories
        )

        logger.info("\n🎉 Preload successful!")
        logger.info("\n📚 Next steps:")
        logger.info("   1. Test search: python test_backend.py")
        logger.info("   2. Run app: streamlit run app.py")
        logger.info("   3. Try searching for any topic!")

        return 0

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Preload interrupted by user")
        preloader._print_summary()
        return 1

    except Exception as e:
        logger.error(f"\n❌ Error during preload: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
