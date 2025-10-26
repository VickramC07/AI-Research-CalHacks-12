"""
ScholarForge Backend Module

This module provides the data layer for ScholarForge, including:
- Elastic Search integration for keyword-based search and metadata storage
- Chroma vector database for semantic similarity search
- Claude API integration for research gap analysis
- arXiv API integration for fetching research papers
- Data ingestion pipeline for papers
- Query handler for coordinated retrieval and synthesis

Future integration: Fetch.ai agent orchestration
"""

from backend.elastic_client import get_elastic_client, ElasticClient
from backend.chroma_client import get_chroma_client, ChromaClient
from backend.claude_client import get_claude_client, ClaudeClient
from backend.arxiv_client import get_arxiv_client, ArxivClient
from backend.data_ingestion import get_paper_ingestor, PaperIngestor
from backend.query_handler import get_query_handler, QueryHandler

__all__ = [
    "get_elastic_client",
    "ElasticClient",
    "get_chroma_client",
    "ChromaClient",
    "get_claude_client",
    "ClaudeClient",
    "get_arxiv_client",
    "ArxivClient",
    "get_paper_ingestor",
    "PaperIngestor",
    "get_query_handler",
    "QueryHandler",
]

__version__ = "2.0.0"  # Updated to 2.0.0 with arXiv integration
