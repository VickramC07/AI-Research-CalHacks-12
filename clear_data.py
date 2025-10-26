#!/usr/bin/env python3
"""
Clear all data from Elasticsearch and Chroma databases.

This script removes sample papers and resets the databases to prepare for
arXiv integration.

Usage:
    python clear_data.py
"""

import logging
import sys
from backend.elastic_client import get_elastic_client
from backend.chroma_client import get_chroma_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clear_elasticsearch():
    """Clear all papers from Elasticsearch."""
    try:
        logger.info("Clearing Elasticsearch...")
        elastic = get_elastic_client()

        # Delete indices
        from backend.config import PAPERS_INDEX, FUTURE_WORK_INDEX

        if elastic.client.indices.exists(index=PAPERS_INDEX):
            elastic.client.indices.delete(index=PAPERS_INDEX)
            logger.info(f"Deleted index: {PAPERS_INDEX}")

        if elastic.client.indices.exists(index=FUTURE_WORK_INDEX):
            elastic.client.indices.delete(index=FUTURE_WORK_INDEX)
            logger.info(f"Deleted index: {FUTURE_WORK_INDEX}")

        # Recreate indices
        elastic._create_indices()
        logger.info("Recreated fresh indices")

        return True

    except Exception as e:
        logger.error(f"Error clearing Elasticsearch: {e}")
        return False


def clear_chroma():
    """Clear all documents from Chroma."""
    try:
        logger.info("Clearing Chroma...")
        chroma = get_chroma_client()

        # Reset collection
        success = chroma.reset_collection()

        if success:
            logger.info("Chroma collection reset successfully")
        else:
            logger.warning("Failed to reset Chroma collection")

        return success

    except Exception as e:
        logger.error(f"Error clearing Chroma: {e}")
        return False


def main():
    """Main function to clear all data."""
    print("\n" + "="*80)
    print("CLEAR ALL DATA")
    print("="*80)
    print("\n⚠️  WARNING: This will delete ALL papers from your databases!")
    print("This includes sample papers and any arXiv papers you've ingested.\n")

    # Ask for confirmation
    response = input("Are you sure you want to continue? (yes/no): ")

    if response.lower() != "yes":
        print("\n❌ Operation cancelled.")
        return 0

    print("\n" + "="*80)
    print("CLEARING DATA...")
    print("="*80)

    results = {
        "Elasticsearch": clear_elasticsearch(),
        "Chroma": clear_chroma()
    }

    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    for database, success in results.items():
        status = "✅ CLEARED" if success else "❌ FAILED"
        print(f"{database}: {status}")

    if all(results.values()):
        print("\n✅ All data cleared successfully!")
        print("\nThe system will now fetch papers from arXiv on-demand when you search.")
        print("\nYou can now run: streamlit run app.py")
        return 0
    else:
        print("\n⚠️  Some operations failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
