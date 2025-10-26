"""
ScholarForge: Research Gap Discovery
A Streamlit app for identifying limitations and future directions in research papers.
"""

import streamlit as st
import pandas as pd
import altair as alt
from typing import Dict, Any, List
import logging

# Import backend modules
from backend.query_handler import get_query_handler
from backend import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# BACKEND INTEGRATION
# ============================================================================

@st.cache_resource
def get_backend():
    """Initialize and cache the backend query handler."""
    try:
        return get_query_handler()
    except Exception as e:
        logger.error(f"Failed to initialize backend: {e}")
        st.error(f"Backend initialization failed: {e}")
        return None


def query_research_gaps(topic: str) -> Dict[str, Any]:
    """
    Query research gaps using the modular backend.

    This function:
    1. Retrieves relevant papers from Chroma (semantic search) and Elastic (keyword search)
    2. Sends results to Claude for analysis
    3. Returns structured response with gaps and future directions

    In the future, this will be replaced with Fetch.ai agent orchestration.

    Args:
        topic: Research topic to analyze

    Returns:
        Dictionary containing summary, limitations, future directions, and keyword trends
    """
    try:
        backend = get_backend()
        if backend is None:
            return _mock_response(topic)

        # Query through the backend
        result = backend.query_research_gaps(
            topic=topic,
            n_results=10,
            use_semantic=True,
            use_keyword=True
        )

        return result

    except Exception as e:
        logger.error(f"Error querying backend: {e}")
        return _mock_response(topic, error=str(e))


def _mock_response(topic: str, error: str = None) -> Dict[str, Any]:
    """Fallback mock response when backend is unavailable."""
    message = f"Using mock data for topic: {topic}"
    if error:
        message += f" (Backend error: {error})"

    return {
        "summary": f"Recent studies in {topic} highlight progress but note unresolved challenges. " + message,
        "limitations": [
            "Backend not fully initialized - using mock data",
            "Limited scalability in current implementations",
            "Lack of standardized evaluation benchmarks"
        ],
        "future_directions": [
            "Initialize backend with real data",
            "Develop more efficient algorithms for large-scale systems",
            "Create standardized benchmarks for fair comparison"
        ],
        "keyword_trend": [
            {"keyword": "scalability", "frequency": 7},
            {"keyword": "efficiency", "frequency": 5},
            {"keyword": "benchmarking", "frequency": 3}
        ],
        "papers": []
    }


# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_summary(summary: str):
    """Render the research gap summary section."""
    st.markdown("### 🔍 Research Gap Summary")
    st.info(summary)


def render_limitations(limitations: list):
    """Render common limitations as a formatted table."""
    st.markdown("### ⚠️ Common Limitations")

    # Convert to DataFrame for better display
    df = pd.DataFrame({
        "ID": [f"L{i+1}" for i in range(len(limitations))],
        "Limitation": limitations
    })

    # Display as table
    st.table(df)


def render_future_directions(directions: list):
    """Render future directions as styled cards."""
    st.markdown("### 🚀 Future Directions")

    # Create columns for card layout
    for idx, direction in enumerate(directions, 1):
        with st.container():
            st.markdown(f"""
            <div style="
                padding: 15px;
                border-left: 4px solid #4CAF50;
                background-color: rgba(76, 175, 80, 0.1);
                margin-bottom: 10px;
                border-radius: 4px;
            ">
                <strong>Direction {idx}:</strong> {direction}
            </div>
            """, unsafe_allow_html=True)


def render_keyword_chart(keyword_data: list):
    """Render keyword frequency visualization using Altair."""
    st.markdown("### 📈 Keyword Trend Analysis")

    # Convert to DataFrame
    df = pd.DataFrame(keyword_data)

    # Create Altair chart
    chart = alt.Chart(df).mark_bar(color='#4CAF50').encode(
        x=alt.X('keyword:N', title='Keyword', sort='-y'),
        y=alt.Y('frequency:Q', title='Frequency in Future Work Discussions'),
        tooltip=['keyword', 'frequency']
    ).properties(
        title='Keyword Frequency in Future Work Discussions',
        height=300
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=14
    ).configure_title(
        fontSize=16
    )

    st.altair_chart(chart, use_container_width=True)


def render_papers_used(papers: List[Dict[str, Any]]):
    """Render the list of papers used in the analysis."""
    st.markdown("### 📚 Papers Analyzed")

    if not papers:
        st.info("No papers were used in this analysis.")
        return

    st.markdown(f"*Analysis based on {len(papers)} research paper(s)*")
    st.markdown("")

    for i, paper in enumerate(papers, 1):
        # Create citation
        authors = paper.get("authors", "Unknown Authors")
        year = paper.get("year", "N/A")
        title = paper.get("title", "Unknown Title")
        venue = paper.get("venue", "")
        field = paper.get("field", "")
        relevance = paper.get("relevance_score", 0)

        # Format citation
        citation = f"**[{i}]** {authors} ({year}). *{title}*"
        if venue:
            citation += f". {venue}"

        # Display with expander
        with st.expander(f"📄 {title[:80]}..." if len(title) > 80 else f"📄 {title}"):
            st.markdown(citation)

            # Metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Year", year)
            with col2:
                st.metric("Relevance", f"{relevance:.0%}")
            with col3:
                if field:
                    st.markdown(f"**Field:** {field.replace('_', ' ').title()}")

            # Content preview
            if paper.get("content_preview"):
                st.markdown("**Excerpt:**")
                st.markdown(f"_{paper['content_preview']}_")


def render_results(data: Dict[str, Any]):
    """Render the complete results page."""
    # Check if no results
    if data.get("no_results"):
        st.warning("⚠️ " + data["summary"])
        st.info("**Suggestions:**\n- Try different search terms\n- Use broader keywords\n- Check available topics: quantum simulation, transformers, federated learning, vector databases, drug discovery")
        return

    # Add spacing
    st.markdown("<br>", unsafe_allow_html=True)

    # Show papers used first
    papers = data.get("papers", [])
    if papers:
        render_papers_used(papers)
        st.markdown("<hr style='margin: 30px 0; border: 1px solid #333;'>", unsafe_allow_html=True)

    # Render analysis sections
    render_summary(data["summary"])

    st.markdown("<hr style='margin: 30px 0; border: 1px solid #333;'>", unsafe_allow_html=True)

    if data.get("limitations"):
        render_limitations(data["limitations"])
        st.markdown("<hr style='margin: 30px 0; border: 1px solid #333;'>", unsafe_allow_html=True)

    if data.get("future_directions"):
        render_future_directions(data["future_directions"])
        st.markdown("<hr style='margin: 30px 0; border: 1px solid #333;'>", unsafe_allow_html=True)

    if data.get("keyword_trend"):
        render_keyword_chart(data["keyword_trend"])


# ============================================================================
# STYLING
# ============================================================================

def apply_custom_styles():
    """Apply custom CSS styling to the app."""
    st.markdown("""
        <style>
        /* Remove default padding */
        .main {
            background-color: #0e1117;
            padding-top: 0 !important;
            padding-bottom: 80px;
        }

        /* Page title at top */
        .page-title {
            text-align: center;
            font-size: 32px;
            font-weight: 700;
            padding: 20px 0;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        /* Container for centered layout */
        .center-container {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            padding-bottom: 80px;
        }

        /* Spacer to push search to center */
        .center-spacer {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* Search box styling */
        .stTextInput > div > div > input {
            text-align: center;
            font-size: 16px;
            padding: 12px;
        }

        /* Fixed footer at bottom */
        .fixed-footer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: #0e1117;
            z-index: 1000;
            text-align: center;
            color: #666;
            font-size: 12px;
            padding: 20px;
            border-top: 1px solid #333;
        }

        /* Info box styling */
        .stInfo {
            background-color: rgba(100, 100, 255, 0.1);
            border-left: 4px solid #667eea;
        }

        /* Table styling */
        .stTable {
            background-color: #1a1a2e;
        }

        /* Results container */
        .results-container {
            padding-bottom: 40px;
        }
        </style>
    """, unsafe_allow_html=True)


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main application entry point."""

    # Page configuration
    st.set_page_config(
        layout="centered",
        page_title="ScholarForge: Research Gap Discovery",
        page_icon="🔬",
        initial_sidebar_state="collapsed"
    )

    # Apply custom styling
    apply_custom_styles()

    # Initialize session state
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'search_performed' not in st.session_state:
        st.session_state.search_performed = False
    if 'last_topic' not in st.session_state:
        st.session_state.last_topic = ""

    # Determine if we should center the search bar
    has_results = st.session_state.search_performed and st.session_state.results is not None

    # Page title at top
    st.markdown('<div class="page-title">ScholarForge</div>', unsafe_allow_html=True)

    # Search interface with conditional centering
    if not has_results:
        # Use flexbox to center search bar in remaining space
        st.markdown('<div class="center-spacer">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            topic = st.text_input(
                "Research Topic",
                placeholder="Enter a research topic (e.g. 'quantum simulation', 'transformer interpretability')",
                label_visibility="collapsed",
                key="search_input"
            )
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Normal top alignment when results exist
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            topic = st.text_input(
                "Research Topic",
                placeholder="Enter a research topic (e.g. 'quantum simulation', 'transformer interpretability')",
                label_visibility="collapsed",
                key="search_input"
            )

    # Handle search - triggers automatically on Enter
    if topic and topic != st.session_state.last_topic:
        st.session_state.search_performed = True
        st.session_state.last_topic = topic

        with st.spinner("Analyzing research gaps..."):
            try:
                # Query the modular backend
                results = query_research_gaps(topic)

                if results and results.get("summary"):
                    st.session_state.results = results
                else:
                    st.session_state.results = None

            except Exception as e:
                logger.error(f"Error in search: {e}")
                st.error(f"An error occurred while fetching results: {str(e)}")
                st.session_state.results = None

    # Display results
    if st.session_state.search_performed:
        st.markdown('<div class="results-container">', unsafe_allow_html=True)
        if st.session_state.results:
            render_results(st.session_state.results)
        else:
            st.warning("No research gap information found for this topic. Try a broader query.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Fixed footer at bottom
    st.markdown(
        '<div class="fixed-footer">Powered by Claude, Fetch.ai, Elastic, and Chroma.</div>',
        unsafe_allow_html=True
    )


# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    main()
