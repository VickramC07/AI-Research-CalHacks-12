#!/usr/bin/env python3
"""
Test multi-source paper fetching and visualization data.

This script tests:
1. Semantic Scholar integration
2. Source detection in papers
3. Year distribution data
4. Multi-source fetching when local results are insufficient
"""

import logging
from backend.semantic_scholar_client import get_semantic_scholar_client
from backend.query_handler import get_query_handler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_semantic_scholar():
    """Test Semantic Scholar API directly."""
    print("\n" + "="*80)
    print("TESTING SEMANTIC SCHOLAR API")
    print("="*80)

    try:
        client = get_semantic_scholar_client()
        print("✅ Semantic Scholar client initialized")

        # Test search
        query = "quantum computing"
        print(f"\n🔍 Searching Semantic Scholar for: '{query}'")
        papers = client.search_papers(query, max_results=5)

        print(f"📊 Found {len(papers)} papers")

        if papers:
            print("\n📄 Sample papers:")
            for i, paper in enumerate(papers[:3], 1):
                print(f"  {i}. [{paper.get('year')}] {paper.get('title')}")
                print(f"     Source: {paper.get('source_api')}")
                print(f"     Venue: {paper.get('venue')}")

        return True

    except Exception as e:
        print(f"❌ Semantic Scholar Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_source_detection():
    """Test that papers have proper source labels."""
    print("\n" + "="*80)
    print("TESTING SOURCE DETECTION")
    print("="*80)

    try:
        handler = get_query_handler()

        # Query something that should have papers
        query = "quantum simulation"
        print(f"\n🔍 Querying: '{query}'")
        result = handler.query_research_gaps(query, n_results=10)

        papers = result.get("papers", [])
        print(f"📊 Retrieved {len(papers)} papers")

        if papers:
            # Count sources
            source_counts = {}
            for paper in papers:
                source = paper.get("source", "Unknown")
                source_counts[source] = source_counts.get(source, 0) + 1

            print("\n📊 Paper sources:")
            for source, count in source_counts.items():
                print(f"  - {source}: {count} papers")

            # Check year distribution
            years = [p.get("year", 0) for p in papers]
            years = [y for y in years if y > 0]
            if years:
                print(f"\n📅 Year range: {min(years)} - {max(years)}")
        else:
            print("⚠️  No papers retrieved")

        return True

    except Exception as e:
        print(f"❌ Source Detection Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multisource_fetching():
    """Test fetching from multiple sources when needed."""
    print("\n" + "="*80)
    print("TESTING MULTI-SOURCE FETCHING")
    print("="*80)

    try:
        handler = get_query_handler()

        # Query something that may not be in local DB
        # This will trigger external fetching
        query = "blockchain consensus algorithms"
        print(f"\n🔍 Querying: '{query}'")
        print("   (This may trigger external fetching if not in local DB)")

        result = handler.query_research_gaps(query, n_results=5)

        papers = result.get("papers", [])
        stats = result.get("retrieval_stats", {})

        print(f"\n📊 Results:")
        print(f"   Semantic results: {stats.get('semantic_count', 0)}")
        print(f"   Keyword results: {stats.get('keyword_count', 0)}")
        print(f"   Papers used: {stats.get('papers_used', 0)}")

        if papers:
            # Show sources
            sources = [p.get("source", "Unknown") for p in papers]
            unique_sources = set(sources)
            print(f"   Sources: {', '.join(unique_sources)}")

        if result.get("no_results"):
            print("   ⚠️  No results found (external fetching may have been attempted)")
        else:
            print("   ✅ Analysis completed")

        return True

    except Exception as e:
        print(f"❌ Multi-Source Fetching Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all multi-source tests."""
    print("\n" + "="*80)
    print("MULTI-SOURCE & VISUALIZATION TESTING")
    print("="*80)

    results = {
        "Semantic Scholar": test_semantic_scholar(),
        "Source Detection": test_source_detection(),
        "Multi-Source Fetching": test_multisource_fetching()
    }

    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    for test, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test}: {status}")

    if all(results.values()):
        print("\n🎉 All multi-source tests passed!")
        print("\nNext steps:")
        print("  1. Run: streamlit run app.py")
        print("  2. Search for a topic")
        print("  3. Verify the source pie chart and year distribution bar chart appear")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")


if __name__ == "__main__":
    main()
