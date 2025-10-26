"""
RAGe!: Research Gap Discovery
A Streamlit app for identifying limitations and future directions in research papers.
"""

import streamlit as st
import pandas as pd
import altair as alt
from typing import Dict, Any, List
import logging
from datetime import datetime

# Import backend modules
from backend.query_handler import get_query_handler, QueryHandler
from backend.claude_chatbot import get_claude_chatbot
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
        # Initialize with recent paper prioritization (2020+)
        # and minimum 5 papers guarantee
        handler = QueryHandler(fetch_from_arxiv=True, min_year=2020)
        return handler
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
            n_results=20,
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
    st.markdown("<h3 style='text-align: center;'>Research Gap Summary</h3>", unsafe_allow_html=True)
    st.info(summary)


def render_limitations(limitations: list):
    """Render common limitations as a formatted table."""
    st.markdown("<h3 style='text-align: center;'>Common Limitations</h3>", unsafe_allow_html=True)

    # Convert to DataFrame for better display
    df = pd.DataFrame({
        "Limitation": limitations
    })

    # Display as table
    st.table(df)


def render_future_directions(directions: list):
    """Render future directions as styled cards."""
    st.markdown("<h3 style='text-align: center;'>Future Directions</h3>", unsafe_allow_html=True)

    # Create columns for card layout
    for idx, direction in enumerate(directions, 1):
        with st.container():
            st.markdown(f"""
            <div style="
                padding: 22px;
                background-color: rgba(45, 27, 105, 0.5);
                margin-bottom: 18px;
                border-radius: 12px;
                color: white;
                border: 3px solid #a855f7;
                transition: all 0.3s ease;
            "
            onmouseover="this.style.boxShadow='0 6px 20px rgba(168, 85, 247, 0.4)';"
            onmouseout="this.style.boxShadow='';"
            >
                <strong style='color: white; font-size: 19px;'>Direction {idx}:</strong> {direction}
            </div>
            """, unsafe_allow_html=True)


def render_keyword_chart(keyword_data: list):
    """Render keyword frequency visualization using Altair."""
    st.markdown("<h3 style='text-align: center;'>Keyword Trend Analysis</h3>", unsafe_allow_html=True)

    # Convert to DataFrame
    df = pd.DataFrame(keyword_data)

    # Create Altair chart with purple theme and white text
    chart = alt.Chart(df).mark_bar(
        color='#a855f7',
        cornerRadiusTopLeft=6,
        cornerRadiusTopRight=6,
        opacity=0.9
    ).encode(
        x=alt.X('keyword:N', title='Keyword', sort='-y'),
        y=alt.Y('frequency:Q', title='Frequency in Future Work Discussions'),
        tooltip=['keyword', 'frequency']
    ).properties(
        title='Keyword Frequency in Future Work Discussions',
        height=380
    ).configure_axis(
        labelFontSize=13,
        titleFontSize=15,
        labelColor='white',
        titleColor='white',
        gridColor='rgba(168, 85, 247, 0.15)',
        domainColor='rgba(168, 85, 247, 0.4)'
    ).configure_title(
        fontSize=19,
        color='white',
        fontWeight=600
    ).configure_view(
        strokeWidth=0,
        fill='rgba(45, 27, 105, 0.3)'
    ).configure(
        background='transparent'
    )

    st.altair_chart(chart, use_container_width=True)


def cluster_papers_by_topic(papers: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Use Claude to cluster papers by topic/focus area."""
    if not papers:
        return {}

    try:
        import anthropic
        from backend import config

        # Use Opus model for better topic clustering
        client = anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)

        # Extract titles
        titles = [paper.get("title", "Unknown") for paper in papers if paper.get("title") != "Unknown"]

        if not titles:
            return {}

        # Create prompt for Claude
        titles_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(titles)])

        prompt = f"""Analyze these research paper titles and group them by their main topic/focus area.
Similar topics should be grouped together. Return ONLY a JSON object (no markdown, no explanation) in this exact format:

{{
  "Topic Name 1": [1, 3, 5],
  "Topic Name 2": [2, 4],
  "Topic Name 3": [6, 7, 8]
}}

Where the numbers are the paper indices from the list below. Make topic names concise (2-4 words).
If a paper doesn't fit with others, it can be in its own topic group or in "Other Topics".

Papers:
{titles_text}

Return ONLY the JSON object:"""

        response = client.messages.create(
            model="claude-opus-4-1-20250805",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract response text
        response_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                response_text += block.text

        # Parse JSON (remove any markdown formatting)
        import json
        response_text = response_text.strip()
        if response_text.startswith("```"):
            # Remove markdown code blocks
            lines = response_text.split("\n")
            response_text = "\n".join([l for l in lines if not l.startswith("```")])

        clusters = json.loads(response_text)

        # Convert indices to titles
        topic_papers = {}
        for topic, indices in clusters.items():
            topic_papers[topic] = [titles[i-1] for i in indices if 0 < i <= len(titles)]

        return topic_papers

    except Exception as e:
        logger.error(f"Error clustering papers: {e}")
        # Fallback to simple grouping
        return {"All Papers": [p.get("title", "Unknown") for p in papers[:5]]}


def render_topic_distribution(papers: List[Dict[str, Any]]):
    """Render pie chart showing distribution of papers by AI-clustered topics."""
    if not papers:
        return

    st.markdown("<h3 style='text-align: center;'>Research Topics Distribution</h3>", unsafe_allow_html=True)

    with st.spinner("Analyzing paper topics with AI..."):
        # Cluster papers by topic
        topic_clusters = cluster_papers_by_topic(papers)

        if not topic_clusters:
            st.info("Not enough papers to cluster by topic.")
            return

        # Count papers per topic
        topic_data = [{"topic": k, "count": len(v)} for k, v in topic_clusters.items()]
        df = pd.DataFrame(topic_data)

        # Calculate percentage
        total = df['count'].sum()
        df['percentage'] = (df['count'] / total * 100).round(1)

        # Create pie chart with purple/pink/blue theme
        chart = alt.Chart(df).mark_arc(
            stroke='rgba(168, 85, 247, 0.3)',
            strokeWidth=2,
            innerRadius=20
        ).encode(
            theta=alt.Theta(field="count", type="quantitative"),
            color=alt.Color(
                field="topic",
                type="nominal",
                scale=alt.Scale(range=['#a855f7', '#7c3aed', '#ec4899', '#3b82f6', '#9333ea', '#d946ef']),
                legend=alt.Legend(
                    title="Topic",
                    titleColor='white',
                    labelColor='white',
                    titleFontSize=14,
                    labelFontSize=12,
                    titleFontWeight=600
                )
            ),
            tooltip=[
                alt.Tooltip('topic:N', title='Topic'),
                alt.Tooltip('count:Q', title='Papers'),
                alt.Tooltip('percentage:Q', title='Percentage', format='.1f')
            ]
        ).properties(
            height=380,
            title='Papers Grouped by Research Topic'
        ).configure_title(
            fontSize=19,
            color='white',
            fontWeight=600
        ).configure_view(
            strokeWidth=0,
            fill='transparent'
        ).configure(
            background='transparent'
        )

        st.altair_chart(chart, use_container_width=True)

        # Show topic details in expander
        with st.expander("View topic clusters"):
            for topic, paper_titles in topic_clusters.items():
                st.markdown(f"**{topic}** ({len(paper_titles)} papers)")
                for title in paper_titles:
                    st.markdown(f"  - {title[:100]}{'...' if len(title) > 100 else ''}")
                st.markdown("")


def render_year_distribution(papers: List[Dict[str, Any]]):
    """Render bar chart showing distribution of papers by publication year."""
    if not papers:
        return

    st.markdown("<h3 style='text-align: center;'>Publication Year Distribution</h3>", unsafe_allow_html=True)

    # Extract years and bucket them
    year_counts = {}
    current_year = datetime.now().year
    for paper in papers:
        year = paper.get("year", 0)

        if year == 0 or year is None:
            year_bucket = "Unknown"
        elif year < 2016:
            year_bucket = "<2016"
        else:
            year_bucket = str(year)

        year_counts[year_bucket] = year_counts.get(year_bucket, 0) + 1

    # Create ordered list of years for past 10 years
    year_order = [str(y) for y in range(current_year, 2015, -1)] + ["<2016"]
    if "Unknown" in year_counts:
        year_order.append("Unknown")

    # Convert to DataFrame
    year_data = [{"year": k, "count": v} for k, v in year_counts.items()]
    df = pd.DataFrame(year_data)

    # Sort by year
    df['year_sort'] = df['year'].apply(
        lambda x: 0 if x == "Unknown"
        else 1 if x == "<2016"
        else int(x)
    )
    df = df.sort_values('year_sort', ascending=False)

    # Create bar chart with purple/blue gradient theme
    chart = alt.Chart(df).mark_bar(
        color='#3b82f6',
        cornerRadiusTopLeft=6,
        cornerRadiusTopRight=6,
        opacity=0.9
    ).encode(
        x=alt.X('year:N', title='Publication Year', sort=year_order),
        y=alt.Y('count:Q', title='Number of Papers'),
        tooltip=[
            alt.Tooltip('year:N', title='Year'),
            alt.Tooltip('count:Q', title='Papers')
        ]
    ).properties(
        height=380,
        title='Papers by Publication Year'
    ).configure_axis(
        labelFontSize=13,
        titleFontSize=15,
        labelColor='white',
        titleColor='white',
        gridColor='rgba(168, 85, 247, 0.15)',
        domainColor='rgba(168, 85, 247, 0.4)'
    ).configure_title(
        fontSize=19,
        color='white',
        fontWeight=600
    ).configure_view(
        strokeWidth=0,
        fill='rgba(45, 27, 105, 0.3)'
    ).configure(
        background='transparent'
    )

    st.altair_chart(chart, use_container_width=True)


def render_papers_used(papers: List[Dict[str, Any]]):
    """Render the list of papers used in the analysis."""
    st.markdown("<h3 style='text-align: center;'>Papers Analyzed</h3>", unsafe_allow_html=True)

    if not papers:
        st.info("No papers were used in this analysis.")
        return

    # Single big expander containing all papers
    with st.expander(f"View all {len(papers)} papers"):
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

            # Display paper
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

            # Add separator between papers (except for the last one)
            if i < len(papers):
                st.markdown("<hr style='margin: 28px 0;'>", unsafe_allow_html=True)


def render_results(data: Dict[str, Any]):
    """Render the complete results page."""
    # Check if no results
    if data.get("no_results"):
        st.warning("⚠️ " + data["summary"])
        st.info("**Suggestions:**\n- Try different search terms\n- Use broader keywords\n- Check available topics: quantum simulation, transformers, federated learning, vector databases, drug discovery")
        return

    # Show warning about recent sources if present
    if data.get("recent_warning"):
        st.warning(data["recent_warning"])

    # Add spacing
    st.markdown("<br>", unsafe_allow_html=True)

    # Show papers used first
    papers = data.get("papers", [])
    if papers:
        render_papers_used(papers)
        st.markdown("<hr>", unsafe_allow_html=True)

    # Render analysis sections
    render_summary(data["summary"])

    st.markdown("<hr>", unsafe_allow_html=True)

    if data.get("limitations"):
        render_limitations(data["limitations"])
        st.markdown("<hr>", unsafe_allow_html=True)

    if data.get("future_directions"):
        render_future_directions(data["future_directions"])
        st.markdown("<hr>", unsafe_allow_html=True)

    if data.get("keyword_trend"):
        render_keyword_chart(data["keyword_trend"])
        st.markdown("<hr>", unsafe_allow_html=True)

    # Render topic and year distributions
    if papers:
        col1, col2 = st.columns(2)
        with col1:
            render_topic_distribution(papers)
        with col2:
            render_year_distribution(papers)


# ============================================================================
# STYLING
# ============================================================================

def render_chatbot():
    """Render the RAGe! chatbot."""
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>RAGe! Chatbot</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-style: italic; color: #c7b5e8;'>Ask questions about papers, get recommendations, or explore research topics</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-style: italic; color: #c7b5e8;'>RAGe! can search the research database to answer your questions</p>", unsafe_allow_html=True)

    # Initialize chat history in session state
    if 'claude_chat_history' not in st.session_state:
        st.session_state.claude_chat_history = []

    # Display chat history
    for message in st.session_state.claude_chat_history:
        if isinstance(message, dict) and message.get("role") in ["user", "assistant"]:
            role = message["role"]
            content = message.get("content", "")

            # Handle different content types
            if isinstance(content, str):
                with st.chat_message(role):
                    st.markdown(content)
            elif isinstance(content, list):
                # Claude API returns list of content blocks
                with st.chat_message(role):
                    for block in content:
                        if hasattr(block, "text"):
                            st.markdown(block.text)
                        elif isinstance(block, dict) and block.get("type") == "text":
                            st.markdown(block.get("text", ""))

    # Chat input
    if prompt := st.chat_input("Ask about papers, research gaps, or topics..."):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get Claude response
        with st.chat_message("assistant"):
            with st.spinner("Searching papers and thinking..."):
                try:
                    chatbot = get_claude_chatbot()

                    # Chat with Claude, passing conversation history
                    response = chatbot.chat(
                        message=prompt,
                        conversation_history=st.session_state.claude_chat_history
                    )

                    if response.get("success"):
                        reply = response.get("response", "I apologize, but I couldn't generate a response.")
                        st.markdown(reply)

                        # Update conversation history
                        st.session_state.claude_chat_history = response.get("conversation_history", [])

                        # Scroll to bottom after response (only on user interaction, not on initialization)

                    else:
                        error_msg = f"I apologize, but I encountered an error: {response.get('response', 'Unknown error')}"
                        st.error(error_msg)
                        # Still add to history
                        st.session_state.claude_chat_history.append({"role": "user", "content": prompt})
                        st.session_state.claude_chat_history.append({"role": "assistant", "content": error_msg})

                        # Scroll to bottom after error

                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.claude_chat_history.append({"role": "user", "content": prompt})
                    st.session_state.claude_chat_history.append({"role": "assistant", "content": error_msg})

                    # Scroll to bottom after exception



def apply_custom_styles():
    """Apply custom CSS styling to the app."""
    st.markdown("""
        <style>
        /* Animated gradient background - dark blue to dark purple */
        .stApp {
            background: linear-gradient(135deg, #0a1128, #1a1b3d, #1e1b4e, #2d1b69, #1e1b4e, #1a1b3d, #0a1128);
            background-size: 400% 400%;
            animation: gradientShift 40s ease-in-out infinite;
        }

        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }

        /* Background decorative elements */
        .stApp::before {
            content: '';
            position: fixed;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(168, 85, 247, 0.15) 0%, transparent 70%);
            border-radius: 50%;
            top: 10%;
            left: 15%;
            animation: float1 20s ease-in-out infinite;
            z-index: 1;
            pointer-events: none;
        }

        .stApp::after {
            content: '';
            position: fixed;
            width: 250px;
            height: 250px;
            background: radial-gradient(circle, rgba(124, 58, 237, 0.12) 0%, transparent 70%);
            border-radius: 50%;
            bottom: 15%;
            right: 10%;
            animation: float2 25s ease-in-out infinite;
            z-index: 1;
            pointer-events: none;
        }

        @keyframes float1 {
            0%, 100% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(30px, -40px) scale(1.1); }
            66% { transform: translate(-20px, 30px) scale(0.9); }
        }

        @keyframes float2 {
            0%, 100% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(-40px, 30px) scale(1.15); }
            66% { transform: translate(25px, -25px) scale(0.85); }
        }

        @keyframes float3 {
            0%, 100% { transform: translate(0, 0); }
            50% { transform: translate(-30px, 40px); }
        }

        @keyframes pulse {
            0%, 100% { opacity: 0.3; transform: scale(1); }
            50% { opacity: 0.6; transform: scale(1.2); }
        }

        /* Remove default padding */
        .main {
            background-color: transparent;
            padding-top: 0 !important;
            padding-bottom: 0px;
            position: relative;
            z-index: 2;
        }

        .main::before {
            content: '';
            position: fixed;
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, rgba(236, 72, 153, 0.1) 0%, transparent 70%);
            border-radius: 50%;
            top: 50%;
            left: 5%;
            animation: float3 30s ease-in-out infinite;
            z-index: 1;
            pointer-events: none;
        }

        .main::after {
            content: '';
            position: fixed;
            width: 180px;
            height: 180px;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%);
            border-radius: 50%;
            top: 20%;
            right: 20%;
            animation: float1 22s ease-in-out infinite reverse;
            z-index: 1;
            pointer-events: none;
        }

        /* Page title at top */
        .page-title {
            text-align: center;
            font-size: 56px;
            font-weight: 700;
            padding: 40px 0;
            margin: 0;
            color: white;
            letter-spacing: 4px;
        }

        /* Section titles */
        h3 {
            color: white !important;
            font-weight: 600 !important;
            padding: 25px 0 15px 0 !important;
            font-size: 32px !important;
            letter-spacing: 2px;
            border-bottom: 3px solid #a855f7;
            padding-bottom: 15px !important;
            margin-bottom: 25px !important;
        }

        /* Container for centered layout */
        .center-container {
            display: flex;
            flex-direction: column;
            min-height: 100vh;
            padding-bottom: 60px;
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
            font-size: 18px;
            padding: 18px;
            background-color: rgba(45, 27, 105, 0.5);
            border: 1px solid #a855f7;
            color: white;
            border-radius: 12px;
            transition: all 0.3s ease;
            outline: none !important;
        }

        .stTextInput > div > div > input:focus {
            border-color: #a855f7 !important;
            font-size: 20px;
            box-shadow: 0 0 25px rgba(168, 85, 247, 0.8) !important;
            outline: none !important;
        }

        /* Remove any browser default focus styling */
        .stTextInput > div > div > input:focus-visible {
            outline: none !important;
        }

        .stTextInput > div > div > input::placeholder {
            color: rgba(255, 255, 255, 0.3);
        }

        /* Info box styling */
        .stInfo {
            background-color: rgba(45, 27, 105, 0.5);
            border: 3px solid #a855f7;
            color: white;
            padding: 22px;
            border-radius: 12px;
            transition: all 0.3s ease;
        }

        /* Table styling */
        .stTable {
            background-color: rgba(45, 27, 105, 0.5);
            border: 3px solid #a855f7;
            border-radius: 12px;
            overflow: hidden;
        }

        table {
            color: white !important;
        }

        thead tr th {
            background-color: rgba(45, 27, 105, 0.7) !important;
            color: white !important;
            font-size: 16px !important;
            font-weight: 600 !important;
            padding: 16px !important;
            border-bottom: 2px solid #a855f7 !important;
        }

        tbody tr td {
            padding: 16px !important;
            border-bottom: 1px solid rgba(168, 85, 247, 0.3) !important;
            transition: background-color 0.3s ease;
        }

        tbody tr:hover td {
            background-color: rgba(168, 85, 247, 0.2) !important;
        }

        /* Results container */
        .results-container {
            padding-bottom: 40px;
        }

        /* Chat container */
        .stChatMessage {
            background-color: rgba(45, 27, 105, 0.5);
            border-radius: 16px;
            padding: 22px;
            margin: 18px 0;
            border: 3px solid #a855f7;
            transition: all 0.3s ease;
        }

        .stChatMessage:hover {
            border-color: #a855f7;
            box-shadow: 0 4px 20px rgba(168, 85, 247, 0.3);
        }

        /* General text color */
        p, span, div {
            color: white;
            font-size: 16px;
            line-height: 1.8;
        }

        /* Markdown text */
        .stMarkdown {
            color: white;
        }

        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: rgba(45, 27, 105, 0.5);
            border: 3px solid #a855f7;
            color: white !important;
            padding: 16px !important;
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .streamlit-expanderHeader:hover {
            border-color: #a855f7;
            background-color: rgba(45, 27, 105, 0.7);
            box-shadow: 0 4px 15px rgba(168, 85, 247, 0.3);
        }

        /* Metric styling */
        .stMetric {
            background-color: rgba(45, 27, 105, 0.5);
            padding: 18px;
            border-radius: 12px;
            border: 3px solid #a855f7;
            transition: all 0.3s ease;
        }

        .stMetric:hover {
            border-color: #a855f7;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(168, 85, 247, 0.3);
        }

        .stMetric label {
            color: white !important;
            font-size: 14px !important;
            font-weight: 600 !important;
        }

        .stMetric .metric-value {
            color: white !important;
            font-size: 28px !important;
        }

        /* Horizontal rule styling - hide default rules */
        hr {
            display: none;
        }

        .stSpinner > div {
            border-color: #a855f7 transparent transparent transparent !important;
        }

        /* Warning/error box styling */
        .stWarning {
            background-color: rgba(45, 27, 105, 0.5);
            border: 3px solid #a855f7;
            color: white;
            padding: 22px;
            border-radius: 12px;
        }

        /* Button styling */
        .stButton > button {
            background-color: rgba(45, 27, 105, 0.5);
            color: white;
            border: 3px solid #a855f7;
            border-radius: 12px;
            padding: 14px 28px;
            font-weight: 600;
            transition: all 0.4s ease;
        }

        .stButton > button:hover {
            background-color: rgba(45, 27, 105, 0.7);
            box-shadow: 0 8px 25px rgba(168, 85, 247, 0.5);
        }

        /* Column styling for charts */
        [data-testid="column"] {
            padding: 12px;
        }

        /* Chat input styling */
        .stChatInputContainer {
            background-color: rgba(45, 27, 105, 0.5);
            border-top: 3px solid #a855f7;
            padding: 18px;
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
        page_title="RAGe!: Research Gap Discovery",
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
    st.markdown('<div class="page-title">RAGe!</div>', unsafe_allow_html=True)

    # Search interface with conditional centering
    if not has_results:
        # Use flexbox to center search bar in remaining space
        st.markdown('<div class="center-spacer">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            topic = st.text_input(
                "Research Topic",
                placeholder="Enter a research topic keywords",
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
                placeholder="Enter a research topic keywords",
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

        # Chatbot section at bottom - ONLY AFTER SEARCH
        render_chatbot()


# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    main()
