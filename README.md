# RAGe: Research Gap Discovery

**A Multi-Layer AI Research Platform for Discovering Limitations and Future Directions**

Built with **Claude AI**, **Elasticsearch**, **ChromaDB**, **Elastic AI Agents**, and **4 Research Paper Sources**

---

## 🎯 Overview

RAGe is a sophisticated research analysis platform that automatically:
- 🔍 **Fetches real papers** from 4 sources (arXiv, Semantic Scholar, PubMed, Crossref)
- 🧠 **Two-stage hybrid search** (Elasticsearch keyword → ChromaDB semantic re-ranking)
- 🤖 **Triple AI integration** (Research analyzer, interactive chatbot, Elastic agents)
- 📊 **Interactive visualizations** (keyword trends, topic clustering, year distribution)
- 💬 **Function-calling chatbot** with direct database access
- ⚡ **Recent paper prioritization** (2020+) with minimum 5 papers guarantee

---

## ✨ Key Features

### Multi-Source Paper Fetching
- **arXiv**: Computer Science, Physics, Mathematics
- **Semantic Scholar**: Cross-disciplinary CS research
- **PubMed**: Biomedical and Life Sciences
- **Crossref**: General academic (all fields)

**Strategy**: 50% arXiv, 50% distributed across other sources for diversity

### Two-Stage Hybrid Retrieval
1. **Stage 1**: Elasticsearch keyword search (100 candidates)
2. **Stage 2**: ChromaDB semantic re-ranking (top 20 most relevant)
3. **Result**: Higher precision than independent searches

### Triple Claude Integration
- **Research Analyzer**: Extracts limitations & future directions from papers
- **Interactive Chatbot**: Q&A with function calling (searches papers on demand)
- **Elastic AI Agents**: Integration with paper_chaser_gamma and ScholarBot

### Quality Guarantees
- Prioritizes papers from 2020+ (configurable)
- Minimum 5 papers per query with multi-source fallback
- Relevance threshold filtering (0.7 default)

---

## 🏗️ Architecture

### System Components

```
┌──────────────────────────────────────────────────────────────────┐
│                      STREAMLIT FRONTEND                           │
│  - Animated gradient UI with floating background elements         │
│  - 3 Interactive charts (Altair): Keywords, Topics, Years         │
│  - Claude chatbot with function calling interface                 │
└────────────────────────────┬─────────────────────────────────────┘
                             ↓
┌──────────────────────────────────────────────────────────────────┐
│                    QUERY HANDLER (Orchestration)                  │
│  - Coordinates retrieval strategy (two-stage or traditional)      │
│  - Manages multi-source fetching with fallback                    │
│  - Ensures quality guarantees (min papers, recency)               │
└──────────┬───────────────────────────────────┬───────────────────┘
           ↓                                   ↓
┌──────────────────────┐           ┌──────────────────────┐
│   LOCAL DATABASES    │           │  EXTERNAL SOURCES    │
│                      │           │                      │
│  ┌────────────────┐  │           │  ┌────────────────┐ │
│  │ Elasticsearch  │  │           │  │     arXiv      │ │
│  │  (keyword +    │  │           │  │      API       │ │
│  │   metadata)    │  │           │  └────────────────┘ │
│  └────────────────┘  │           │  ┌────────────────┐ │
│  ┌────────────────┐  │           │  │   Semantic     │ │
│  │   ChromaDB     │  │           │  │    Scholar     │ │
│  │  (embeddings)  │  │           │  └────────────────┘ │
│  └────────────────┘  │           │  ┌────────────────┐ │
└──────────────────────┘           │  │    PubMed      │ │
           ↓                       │  └────────────────┘ │
┌──────────────────────┐           │  ┌────────────────┐ │
│   DATA INGESTION     │←──────────┤  │   Crossref     │ │
│  - Normalizes papers │           │  └────────────────┘ │
│  - Dual storage      │           └──────────────────────┘
└──────────┬───────────┘
           ↓
┌──────────────────────────────────────────────────────────────────┐
│                     CLAUDE AI LAYER                               │
│                                                                   │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │   Research     │  │   Chatbot    │  │  Elastic AI Agents   │ │
│  │   Analyzer     │  │  (Function   │  │  (paper_chaser_      │ │
│  │ (Gap Analysis) │  │   Calling)   │  │   gamma, ScholarBot) │ │
│  └────────────────┘  └──────────────┘  └──────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### Request Flow

```
User Query → Query Handler
                │
                ├─→ Check Local Databases
                │   ├─→ Elasticsearch (keyword search - 100 candidates)
                │   └─→ ChromaDB (semantic re-rank - top 20)
                │
                ├─→ < 10 results? → Multi-Source Fetch
                │                    ├─→ arXiv (50%)
                │                    └─→ Others (50%): Semantic Scholar, PubMed, Crossref
                │                    └─→ Ingest → Elasticsearch + ChromaDB
                │                    └─→ Re-search
                │
                └─→ Claude Analysis → Return Results
                                      ├─→ Summary
                                      ├─→ Limitations
                                      ├─→ Future Directions
                                      └─→ Keyword Trends
```

---

## 🛠️ Technology Stack

### Frontend
| Tool | Purpose | File |
|------|---------|------|
| **Streamlit** | Web UI framework | `app.py` |
| **Altair** | Interactive charts | `app.py` |
| **Pandas** | Data manipulation | `app.py` |

### Databases
| Tool | Purpose | File |
|------|---------|------|
| **Elasticsearch** | Keyword search + metadata storage | `backend/elastic_client.py` |
| **ChromaDB** | Semantic similarity search | `backend/chroma_client.py` |

### AI & Agents
| Tool | Purpose | File |
|------|---------|------|
| **Claude API** | Research gap analysis | `backend/claude_client.py` |
| **Claude Chatbot** | Interactive Q&A with function calling | `backend/claude_chatbot.py` |
| **Elastic AI Agents** | MCP protocol agent integration | `backend/elastic_agent_client.py` |

### Paper Sources
| Source | Domain | File |
|--------|--------|------|
| **arXiv** | CS, Physics, Math | `backend/arxiv_client.py` |
| **Semantic Scholar** | Cross-disciplinary CS | `backend/semantic_scholar_client.py` |
| **PubMed** | Biomedical | `backend/pubmed_client.py` |
| **Crossref** | General academic | `backend/crossref_client.py` |

### Orchestration
| Component | Purpose | File |
|-----------|---------|------|
| **Query Handler** | Coordinates all retrieval & synthesis | `backend/query_handler.py` |
| **Data Ingestor** | Normalizes & stores papers | `backend/data_ingestion.py` |

---

## 📦 Project Structure

```
ResearchCH12/
├── app.py                                # Streamlit web application (1000+ lines)
│                                        # - Animated gradient UI
│                                        # - Interactive Altair charts
│                                        # - Claude chatbot interface
│
├── backend/
│   ├── __init__.py                      # Module exports (v3.0.0)
│   ├── config.py                        # API credentials & configuration
│   │
│   ├── query_handler.py                 # ORCHESTRATION LAYER
│   │                                    # - Two-stage hybrid retrieval
│   │                                    # - Multi-source fetching
│   │                                    # - Quality guarantees
│   │
│   ├── data_ingestion.py                # DATA PIPELINE
│   │                                    # - Paper normalization
│   │                                    # - Dual database storage
│   │
│   ├── elastic_client.py                # ELASTICSEARCH CLIENT
│   │                                    # - Keyword search (BM25)
│   │                                    # - Metadata storage
│   │
│   ├── chroma_client.py                 # CHROMADB CLIENT
│   │                                    # - Semantic search (embeddings)
│   │                                    # - Cosine similarity
│   │
│   ├── claude_client.py                 # CLAUDE ANALYZER
│   │                                    # - Extracts limitations
│   │                                    # - Identifies future directions
│   │
│   ├── claude_chatbot.py                # CLAUDE CHATBOT
│   │                                    # - Function calling (search_papers)
│   │                                    # - Interactive Q&A
│   │
│   ├── elastic_agent_client.py          # ELASTIC AI AGENTS
│   │                                    # - paper_chaser_gamma agent
│   │                                    # - ScholarBot integration
│   │                                    # - MCP protocol
│   │
│   ├── arxiv_client.py                  # arXiv API CLIENT
│   ├── semantic_scholar_client.py       # Semantic Scholar API CLIENT
│   ├── pubmed_client.py                 # PubMed API CLIENT
│   └── crossref_client.py               # Crossref API CLIENT
│
├── requirements.txt                     # Python dependencies
├── chroma_db/                           # Local ChromaDB storage (auto-created)
│
├── test_backend.py                      # Backend diagnostics
├── test_multisource.py                  # Multi-source fetching tests
├── test_v3_features.py                  # Feature tests
├── clear_data.py                        # Database reset script
│
└── README.md                            # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Internet connection (for paper sources)
- Elasticsearch account (cloud or self-hosted)
- Claude API key from Anthropic

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd ResearchCH12

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Add your API keys to `backend/config.py` or set environment variables:

```python
# Elasticsearch
ELASTIC_URL = "https://your-deployment.es.gcp.elastic.cloud:443"
ELASTIC_API_KEY = "your_api_key"
ELASTIC_TENANT = "your_tenant_id"

# Claude API
CLAUDE_API_KEY = "sk-ant-api03-..."
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
```

### Run the Application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

### First Search

1. Enter a research topic (e.g., "quantum computing", "transformer models", "CRISPR gene editing")
2. System checks local databases
3. If no results, automatically fetches from 4 sources
4. Papers are stored locally for future searches
5. Claude analyzes and displays:
   - Research gaps
   - Limitations
   - Future directions
   - Visualizations

### Using the Chatbot

After searching, scroll down to the RAGe Chatbot:
- Ask questions about the papers
- Request summaries of specific papers
- Explore research concepts
- Claude uses function calling to search papers on demand

---

## 🔧 Backend API

### Query Handler

```python
from backend.query_handler import QueryHandler

# Initialize with settings
handler = QueryHandler(
    fetch_from_arxiv=True,  # Enable external fetching
    min_year=2020           # Prioritize recent papers
)

# Query research gaps
result = handler.query_research_gaps(
    topic="quantum machine learning",
    n_results=20,
    use_semantic=True,      # Use ChromaDB
    use_keyword=True,       # Use Elasticsearch
    relevance_threshold=0.7, # Minimum similarity
    use_two_stage=True      # Two-stage hybrid retrieval
)

print(result["summary"])
print(result["limitations"])
print(result["future_directions"])
print(result["papers"])
```

### Claude Chatbot

```python
from backend.claude_chatbot import get_claude_chatbot

chatbot = get_claude_chatbot()

# Start conversation
response = chatbot.chat(
    message="What papers discuss quantum error correction?",
    conversation_history=[]
)

print(response["response"])
print(response["conversation_history"])
```

### Direct Client Access

```python
# Elasticsearch
from backend.elastic_client import get_elastic_client
elastic = get_elastic_client()
papers = elastic.search_papers("neural networks", size=10)

# ChromaDB
from backend.chroma_client import get_chroma_client
chroma = get_chroma_client()
results = chroma.semantic_search("deep learning", n_results=10)

# arXiv
from backend.arxiv_client import get_arxiv_client
arxiv = get_arxiv_client()
papers = arxiv.search_papers("quantum computing", max_results=5)

# Semantic Scholar
from backend.semantic_scholar_client import get_semantic_scholar_client
ss = get_semantic_scholar_client()
papers = ss.search_papers("graph neural networks", max_results=5)

# PubMed
from backend.pubmed_client import get_pubmed_client
pubmed = get_pubmed_client()
papers = pubmed.search_papers("protein folding", max_results=5)

# Crossref
from backend.crossref_client import get_crossref_client
crossref = get_crossref_client()
papers = crossref.search_papers("climate change", max_results=5)
```

### Data Ingestion

```python
from backend.data_ingestion import get_paper_ingestor

ingestor = get_paper_ingestor()

# Ingest a single paper
paper_data = {
    "title": "Attention Is All You Need",
    "authors": "Vaswani, A.; Shazeer, N.; et al.",
    "year": 2017,
    "abstract": "The dominant sequence transduction models...",
    "source": "arXiv"
}

sections = {
    "abstract": "...",
    "conclusion": "...",
    "future_work": "..."
}

success = ingestor.ingest_paper(paper_data, sections)
```

---

## 🎓 How It Works

### Two-Stage Hybrid Retrieval

Traditional retrieval systems use either keyword search OR semantic search. RAGe uses **both in sequence**:

**Stage 1: Keyword Filtering (Elasticsearch)**
- Retrieves 100 candidates matching query terms
- Fast, broad coverage
- Ensures relevant domain/topic

**Stage 2: Semantic Re-Ranking (ChromaDB)**
- Computes semantic similarity for all 100 candidates
- Selects top 20 most conceptually relevant
- Filters by relevance threshold (0.7 default)

**Result**: Higher precision than either method alone.

### Multi-Source Fetching Strategy

When local results are insufficient (<10 papers):

1. **Calculate need**: `needed = 10 - local_results`
2. **Split quota**:
   - 50% from arXiv (largest coverage)
   - 50% distributed: Semantic Scholar, PubMed, Crossref
3. **Fetch in parallel**
4. **Ingest all papers** into Elasticsearch + ChromaDB
5. **Re-search** local databases
6. **Return unified results**

**Example**: Need 8 papers
- Fetch 4 from arXiv
- Fetch 1-2 from each of Semantic Scholar, PubMed, Crossref
- Store all 8 locally
- Re-run search

### Claude Function Calling

The chatbot uses Claude's function calling feature:

```python
# User asks: "Show me papers about quantum algorithms"

# Claude decides to call function
tool_use = {
    "name": "search_papers",
    "input": {
        "query": "quantum algorithms",
        "max_results": 5
    }
}

# Backend executes search
papers = elastic.search_papers("quantum algorithms", size=5)

# Claude receives results and generates response
response = "I found 5 papers on quantum algorithms:
1. [Paper Title] by [Authors] (2023)
   Abstract: ...

2. [Paper Title] by [Authors] (2022)
   ..."
```

### Recent Paper Prioritization

RAGe prioritizes papers from 2020+ (configurable):

1. **During retrieval**: Filters results by year
2. **After analysis**: Checks that ≥5 papers are from 2017+
3. **If insufficient**: Adds warning to results
4. **Sorting**: Recent papers appear first in lists

---

## 🐛 Troubleshooting

### Elasticsearch Connection Issues

```bash
# Verify credentials in backend/config.py
# Test connection
curl https://your-deployment.es.gcp.elastic.cloud:443
```

### ChromaDB Issues

```bash
# Reset ChromaDB database
rm -rf chroma_db/

# Re-run a search to rebuild
streamlit run app.py
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### No Papers Found

- Check internet connection
- Verify API rate limits not exceeded
- Try broader search terms
- Check logs for API errors

---

## 📊 Technical Specifications

### Performance
- **Average search time**: 2-5 seconds (local cache)
- **First-time fetch**: 10-20 seconds (external sources)
- **Papers per query**: 10-20 (configurable)
- **Relevance threshold**: 0.7 (configurable)

### Scalability
- **Local storage**: Unlimited (disk-based)
- **Elasticsearch**: Cloud-managed, auto-scaling
- **ChromaDB**: Local embeddings, 100K+ papers supported
- **Concurrent users**: Streamlit default (adjustable)

### Models
- **Claude**: claude-3-5-sonnet-20241022
- **Embeddings**: ChromaDB default (all-MiniLM-L6-v2)
- **Elastic Search**: BM25 algorithm

---

## 🎯 Use Cases

- **Researchers**: Discover unexplored areas in your field
- **PhD Students**: Identify dissertation topics and gaps
- **Grant Writers**: Find funding opportunities in research gaps
- **Literature Reviews**: Quickly synthesize limitations across papers
- **Innovation Teams**: Spot emerging research directions
- **Librarians**: Help researchers discover relevant papers
- **Educators**: Understand current state of research topics

---

## 📄 License

MIT License

---

## 🤝 Contributing

This is a research project. Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📮 Contact

For questions or issues, please open a GitHub issue.

---

**Built with Claude AI, Elasticsearch, ChromaDB, and Streamlit**

**Version 0 - Initial Release**
