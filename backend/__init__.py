"""
ScholarForge Backend Module

This module provides the data layer for ScholarForge, including:
- Elastic Search integration for keyword-based search and metadata storage
- Elastic AI Assistant integration for research chat agents
- Chroma vector database for semantic similarity search
- Claude API integration for research gap analysis
- Multi-source paper fetching: arXiv, Semantic Scholar, PubMed, Crossref
- Data ingestion pipeline for papers
- Query handler for coordinated retrieval and synthesis

Features:
- Prioritizes recent papers (configurable minimum year)
- Minimum 5 papers guarantee with multi-source fallback
- Diverse source coverage across CS, biomedical, and general research
"""

from backend.elastic_client import get_elastic_client, ElasticClient
from backend.elastic_agent_client import get_elastic_agent_client, ElasticAgentClient
from backend.chroma_client import get_chroma_client, ChromaClient
from backend.claude_client import get_claude_client, ClaudeClient
from backend.arxiv_client import get_arxiv_client, ArxivClient
from backend.semantic_scholar_client import get_semantic_scholar_client, SemanticScholarClient
from backend.pubmed_client import get_pubmed_client, PubMedClient
from backend.crossref_client import get_crossref_client, CrossrefClient
from backend.data_ingestion import get_paper_ingestor, PaperIngestor
from backend.query_handler import get_query_handler, QueryHandler

__all__ = [
    "get_elastic_client",
    "ElasticClient",
    "get_elastic_agent_client",
    "ElasticAgentClient",
    "get_chroma_client",
    "ChromaClient",
    "get_claude_client",
    "ClaudeClient",
    "get_arxiv_client",
    "ArxivClient",
    "get_semantic_scholar_client",
    "SemanticScholarClient",
    "get_pubmed_client",
    "PubMedClient",
    "get_crossref_client",
    "CrossrefClient",
    "get_paper_ingestor",
    "PaperIngestor",
    "get_query_handler",
    "QueryHandler",
]

__version__ = "3.0.0"  # Updated to 3.0.0 with multi-source, agents, and recency prioritization
