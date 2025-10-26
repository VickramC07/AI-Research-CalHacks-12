#!/usr/bin/env python3
"""
Backend Testing and Diagnostics Script

This script helps diagnose issues with the backend:
- Tests Elasticsearch connection
- Tests Chroma connection
- Shows what data is actually stored
- Tests search functionality

Usage:
    python test_backend.py
"""

import logging
from backend.elastic_client import get_elastic_client
from backend.chroma_client import get_chroma_client
from backend.query_handler import get_query_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_elasticsearch():
    """Test Elasticsearch connection and data."""
    print("\n" + "="*80)
    print("TESTING ELASTICSEARCH")
    print("="*80)

    try:
        elastic = get_elastic_client()
        print("✅ Connected to Elasticsearch")

        # Try to get some papers
        print("\nSearching for all papers (using wildcard)...")
        papers = elastic.search_papers("*", size=100)
        print(f"📊 Found {len(papers)} papers in Elasticsearch")

        if papers:
            print("\n📄 Papers in database:")
            for i, paper in enumerate(papers[:10], 1):
                title = paper.get("title", "No title")
                year = paper.get("year", "N/A")
                field = paper.get("field", "N/A")
                print(f"  {i}. [{year}] {title} (field: {field})")

            # Test specific searches
            print("\n🔍 Testing specific searches:")
            test_queries = ["quantum", "transformer", "federated", "vector", "drug"]
            for query in test_queries:
                results = elastic.search_papers(query, size=5)
                print(f"  - '{query}': {len(results)} results")
        else:
            print("⚠️  No papers found in Elasticsearch!")
            print("   Run: python ingest_sample_data.py")

        return True

    except Exception as e:
        print(f"❌ Elasticsearch Error: {e}")
        return False


def test_chroma():
    """Test Chroma connection and data."""
    print("\n" + "="*80)
    print("TESTING CHROMA")
    print("="*80)

    try:
        chroma = get_chroma_client()
        print("✅ Connected to Chroma")

        # Get stats
        stats = chroma.get_collection_stats()
        doc_count = stats.get("document_count", 0)
        print(f"📊 Chroma has {doc_count} document sections")

        if doc_count > 0:
            # Test semantic search
            print("\n🔍 Testing semantic searches:")
            test_queries = ["quantum simulation", "neural networks", "privacy"]
            for query in test_queries:
                results = chroma.semantic_search(query, n_results=3)
                print(f"  - '{query}': {len(results)} results")

                if results:
                    for r in results[:1]:  # Show first result
                        title = r.get("metadata", {}).get("title", "Unknown")
                        distance = r.get("distance", 0)
                        print(f"      → {title} (distance: {distance:.3f})")
        else:
            print("⚠️  No documents found in Chroma!")
            print("   Run: python ingest_sample_data.py")

        return True

    except Exception as e:
        print(f"❌ Chroma Error: {e}")
        return False


def test_full_pipeline():
    """Test the full query pipeline."""
    print("\n" + "="*80)
    print("TESTING FULL PIPELINE")
    print("="*80)

    try:
        handler = get_query_handler()
        print("✅ Query handler initialized")

        # Test queries
        test_queries = ["quantum simulation", "transformers", "social media"]

        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            result = handler.query_research_gaps(query, n_results=5)

            stats = result.get("retrieval_stats", {})
            print(f"   Semantic results: {stats.get('semantic_count', 0)}")
            print(f"   Keyword results: {stats.get('keyword_count', 0)}")
            print(f"   Papers used: {stats.get('papers_used', 0)}")

            if result.get("no_results"):
                print(f"   ⚠️  No relevant results")
            else:
                print(f"   ✅ Analysis generated")
                print(f"   Summary: {result.get('summary', '')[:100]}...")

        return True

    except Exception as e:
        print(f"❌ Pipeline Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("SCHOLARFORGE BACKEND DIAGNOSTICS")
    print("="*80)

    results = {
        "Elasticsearch": test_elasticsearch(),
        "Chroma": test_chroma(),
        "Full Pipeline": test_full_pipeline()
    }

    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    for test, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test}: {status}")

    if all(results.values()):
        print("\n🎉 All tests passed! System is working correctly.")
        print("\nYou can now run: streamlit run app.py")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("\nTroubleshooting:")
        print("  1. Run: pip install -r requirements.txt")
        print("  2. Run: python ingest_sample_data.py")
        print("  3. Check backend/config.py for correct credentials")


if __name__ == "__main__":
    main()
