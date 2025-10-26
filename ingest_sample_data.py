#!/usr/bin/env python3
"""
Sample Data Ingestion Script for ScholarForge

This script loads sample research papers into Elastic and Chroma to get started quickly.
Run this script after setting up the environment to populate the databases with test data.

Usage:
    python ingest_sample_data.py
"""

import logging
import sys
from backend.data_ingestion import get_paper_ingestor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to ingest sample papers."""
    logger.info("=" * 80)
    logger.info("ScholarForge Sample Data Ingestion")
    logger.info("=" * 80)

    try:
        # Initialize the ingestor
        logger.info("Initializing paper ingestor...")
        ingestor = get_paper_ingestor()

        # Create sample papers
        logger.info("Creating sample papers...")
        sample_papers = ingestor.create_sample_papers(count=5)

        logger.info(f"Generated {len(sample_papers)} sample papers")
        for i, paper in enumerate(sample_papers, 1):
            logger.info(f"  {i}. {paper['title']}")

        # Ingest papers
        logger.info("\nIngesting papers into Elastic and Chroma...")
        results = ingestor.ingest_papers_batch(sample_papers)

        logger.info("\n" + "=" * 80)
        logger.info("Ingestion Results:")
        logger.info(f"  ✓ Successfully ingested: {results['success']} papers")
        logger.info(f"  ✗ Failed to ingest: {results['failed']} papers")
        logger.info("=" * 80)

        if results['success'] > 0:
            logger.info("\n✅ Sample data ingestion complete!")
            logger.info("\nYou can now:")
            logger.info("  1. Run the Streamlit app: streamlit run app.py")
            logger.info("  2. Search for topics like:")
            logger.info("     - 'quantum simulation'")
            logger.info("     - 'transformer interpretability'")
            logger.info("     - 'federated learning'")
            logger.info("     - 'vector databases'")
            logger.info("     - 'drug discovery'")
            return 0
        else:
            logger.error("\n❌ Failed to ingest sample data")
            logger.error("Please check the error messages above and try again")
            return 1

    except Exception as e:
        logger.error(f"\n❌ Error during ingestion: {e}", exc_info=True)
        logger.error("\nTroubleshooting:")
        logger.error("  1. Check that Elasticsearch is accessible")
        logger.error("  2. Verify API credentials in backend/config.py")
        logger.error("  3. Ensure all dependencies are installed: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
