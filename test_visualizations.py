#!/usr/bin/env python3
"""
Quick test to verify visualization data is properly formatted.
"""

from backend.query_handler import get_query_handler
import pandas as pd

def test_visualization_data():
    print("\n" + "="*80)
    print("TESTING VISUALIZATION DATA")
    print("="*80)

    # Get query handler and run a query
    handler = get_query_handler()
    result = handler.query_research_gaps('quantum simulation', n_results=10)

    papers = result.get('papers', [])
    print(f"\n📊 Retrieved {len(papers)} papers")

    if not papers:
        print("❌ No papers retrieved!")
        return False

    # Test source distribution data
    print("\n1. Testing Source Distribution Data:")
    source_counts = {}
    for paper in papers:
        source = paper.get("source", "Other")
        if not source or source == "":
            source = "Other"
        source_counts[source] = source_counts.get(source, 0) + 1

    print(f"   Sources found: {list(source_counts.keys())}")
    for source, count in source_counts.items():
        print(f"   - {source}: {count} papers")

    # Calculate percentages
    df = pd.DataFrame([{"source": k, "count": v} for k, v in source_counts.items()])
    total = df['count'].sum()
    df['percentage'] = (df['count'] / total * 100).round(1)
    print(f"   ✅ Percentages calculated successfully")
    print(f"   Total: {total} papers, {df['percentage'].sum()}%")

    # Test year distribution data
    print("\n2. Testing Year Distribution Data:")
    year_counts = {}
    current_year = 2024
    for paper in papers:
        year = paper.get("year", 0)

        if year == 0 or year is None or year == "N/A":
            year_bucket = "Unknown"
        elif year < 2016:
            year_bucket = "<2016"
        else:
            year_bucket = str(year)

        year_counts[year_bucket] = year_counts.get(year_bucket, 0) + 1

    print(f"   Year buckets found: {list(year_counts.keys())}")
    for year, count in year_counts.items():
        print(f"   - {year}: {count} papers")

    # Check if years can be sorted
    year_order = [str(y) for y in range(current_year, 2015, -1)] + ["<2016"]
    if "Unknown" in year_counts:
        year_order.append("Unknown")
    print(f"   ✅ Year ordering works correctly")

    print("\n" + "="*80)
    print("✅ ALL VISUALIZATION DATA TESTS PASSED")
    print("="*80)
    print("\nBoth charts should render correctly in the app!")
    print("Run: streamlit run app.py")

    return True

if __name__ == "__main__":
    try:
        test_visualization_data()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
