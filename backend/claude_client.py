"""
Claude API client for ScholarForge.
Handles research gap analysis and synthesis using Claude API.
"""

import anthropic
from typing import Dict, Any, List, Optional
import logging
import json

from backend.config import (
    CLAUDE_API_KEY,
    CLAUDE_MODEL,
    CLAUDE_MAX_TOKENS
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClaudeClient:
    """Client for interacting with Claude API for research synthesis."""

    def __init__(self):
        """Initialize Claude API client."""
        try:
            if CLAUDE_API_KEY == "PUT_CLAUDE_API_KEY_HERE":
                logger.warning("Claude API key not set. Using mock mode.")
                self.client = None
                self.mock_mode = True
            else:
                self.client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
                self.mock_mode = False
                logger.info("Successfully initialized Claude API client")

        except Exception as e:
            logger.error(f"Error initializing Claude client: {e}")
            self.client = None
            self.mock_mode = True

    def analyze_research_gaps(
        self,
        topic: str,
        paper_sections: List[Dict[str, Any]],
        elastic_results: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze research papers to identify gaps, limitations, and future directions.

        Args:
            topic: Research topic query
            paper_sections: List of paper sections from Chroma (semantic search results)
            elastic_results: Optional list of papers from Elastic (keyword search)

        Returns:
            Dictionary containing:
                - summary: Synthesis of key themes
                - limitations: List of identified limitations
                - future_directions: List of research opportunities
                - keyword_trend: List of trending keywords with frequencies
        """
        if self.mock_mode:
            return self._mock_analyze_research_gaps(topic)

        try:
            # Build context from retrieved papers
            context = self._build_context(topic, paper_sections, elastic_results)

            # Create prompt for Claude
            prompt = self._create_analysis_prompt(topic, context)

            # Call Claude API
            message = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            response_text = message.content[0].text
            result = self._parse_analysis_response(response_text)

            logger.info(f"Completed research gap analysis for topic: {topic}")
            return result

        except Exception as e:
            logger.error(f"Error analyzing research gaps: {e}")
            return self._mock_analyze_research_gaps(topic)

    def synthesize_papers(
        self,
        papers: List[Dict[str, Any]],
        focus: str = "limitations and future work"
    ) -> str:
        """
        Synthesize multiple papers into a coherent summary.

        Args:
            papers: List of paper data with sections
            focus: What aspect to focus on (default: limitations and future work)

        Returns:
            Synthesized summary text
        """
        if self.mock_mode:
            return f"Mock synthesis of {len(papers)} papers focusing on {focus}."

        try:
            # Build paper summaries
            paper_texts = []
            for paper in papers:
                title = paper.get("title", "Unknown")
                content = paper.get("content", paper.get("abstract", ""))
                paper_texts.append(f"Title: {title}\nContent: {content}\n")

            combined_text = "\n---\n".join(paper_texts[:10])  # Limit to 10 papers

            # Create synthesis prompt
            prompt = f"""Synthesize the following research papers, focusing specifically on {focus}.
Provide a concise but comprehensive summary that identifies common themes, patterns, and insights.

Papers:
{combined_text}

Please provide a well-structured synthesis in 2-3 paragraphs."""

            message = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            synthesis = message.content[0].text
            logger.info(f"Synthesized {len(papers)} papers")
            return synthesis

        except Exception as e:
            logger.error(f"Error synthesizing papers: {e}")
            return f"Error synthesizing papers: {str(e)}"

    def _build_context(
        self,
        topic: str,
        paper_sections: List[Dict[str, Any]],
        elastic_results: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Build context string from retrieved papers."""
        context_parts = []

        # Add paper sections from Chroma (semantic search)
        if paper_sections:
            context_parts.append("=== RELEVANT PAPER SECTIONS (Semantic Search) ===\n")
            for i, section in enumerate(paper_sections[:15], 1):  # Limit to 15 sections
                title = section.get("metadata", {}).get("title", "Unknown")
                section_name = section.get("metadata", {}).get("section_name", "Unknown")
                content = section.get("content", "")
                context_parts.append(f"{i}. [{title}] - {section_name}\n{content}\n")

        # Add papers from Elastic (keyword search)
        if elastic_results:
            context_parts.append("\n=== RELATED PAPERS (Keyword Search) ===\n")
            for i, paper in enumerate(elastic_results[:10], 1):  # Limit to 10 papers
                title = paper.get("title", "Unknown")
                abstract = paper.get("abstract", "")
                context_parts.append(f"{i}. {title}\n{abstract}\n")

        return "\n".join(context_parts)

    def _create_analysis_prompt(self, topic: str, context: str) -> str:
        """Create prompt for research gap analysis."""
        return f"""You are a research analyst helping identify gaps and future directions in academic literature.

Topic: {topic}

Based on the following research papers and sections, analyze and identify:
1. A concise summary of the current state of research
2. Common limitations mentioned across papers
3. Potential future research directions
4. Key trending keywords and their frequency

Context:
{context}

Please provide your analysis in the following JSON format:
{{
    "summary": "A 2-3 sentence synthesis of the research landscape",
    "limitations": [
        "Limitation 1",
        "Limitation 2",
        "Limitation 3"
    ],
    "future_directions": [
        "Direction 1",
        "Direction 2",
        "Direction 3"
    ],
    "keyword_trend": [
        {{"keyword": "keyword1", "frequency": 5}},
        {{"keyword": "keyword2", "frequency": 3}}
    ]
}}

Focus on:
- Synthesizing insights from multiple sources
- Identifying patterns and recurring themes
- Suggesting actionable research directions
- Being specific and concrete rather than generic

Provide ONLY the JSON response, no additional text."""

    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's JSON response."""
        try:
            # Try to extract JSON from response
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1

            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                return result
            else:
                logger.error("Could not find JSON in Claude's response")
                return self._default_response()

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Claude response as JSON: {e}")
            return self._default_response()

    def _default_response(self) -> Dict[str, Any]:
        """Return default response structure."""
        return {
            "summary": "Unable to analyze research gaps at this time.",
            "limitations": ["Analysis unavailable"],
            "future_directions": ["Please try again later"],
            "keyword_trend": []
        }

    def _mock_analyze_research_gaps(self, topic: str) -> Dict[str, Any]:
        """Mock response for testing without API key."""
        return {
            "summary": f"Recent studies in {topic} highlight significant progress but note unresolved scalability and efficiency challenges across multiple domains.",
            "limitations": [
                "Limited scalability in current implementations",
                "High computational costs for large-scale applications",
                "Lack of standardized evaluation benchmarks",
                "Insufficient real-world deployment studies"
            ],
            "future_directions": [
                "Develop more efficient algorithms for large-scale systems",
                "Create standardized benchmarks for fair comparison",
                "Conduct extensive real-world validation studies",
                "Explore hybrid approaches combining multiple methodologies"
            ],
            "keyword_trend": [
                {"keyword": "scalability", "frequency": 8},
                {"keyword": "efficiency", "frequency": 6},
                {"keyword": "benchmarking", "frequency": 4},
                {"keyword": "real-world applications", "frequency": 5}
            ]
        }


# Singleton instance
_claude_client = None


def get_claude_client() -> ClaudeClient:
    """Get or create Claude client singleton."""
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client
