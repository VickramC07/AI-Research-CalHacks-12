# ScholarForge: Research Gap Discovery

A dynamic AI-powered platform that **fetches real research papers from arXiv** and identifies limitations and future research directions. Built with **arXiv API**, **Claude**, **Elasticsearch**, **Chroma**, and designed for future integration with **Fetch.ai** agents.

## 🎯 Overview

ScholarForge helps researchers discover gaps in existing literature by:
- **🔍 arXiv Integration**: Automatically fetches real research papers on-demand
- **🧠 Semantic Search**: Using Chroma vector database to find conceptually similar papers
- **📊 Keyword Search**: Using Elasticsearch for precise metadata and text matching
- **🤖 AI Synthesis**: Using Claude to analyze papers and extract limitations & future directions
- **🤝 Agent Orchestration**: (Coming soon) Fetch.ai agents for distributed processing

## ✨ What's New in v2.0

**No more sample data!** ScholarForge now:
- ✅ Fetches papers directly from arXiv
- ✅ Stores them automatically in Elastic + Chroma
- ✅ Searches ANY research topic
- ✅ Provides real publication dates, authors, and citations
- ✅ Self-populates on first search

## 🏗️ Architecture

```
User Query → Query Handler
              │
              ├──→ Check Local DBs (Elastic + Chroma)
              │
              ├──→ No results? → Fetch from arXiv
              │                   │
              │                   ├──→ Store in Elastic
              │                   └──→ Store in Chroma
              │
              ├──→ Re-search local DBs
              │
              └──→ Send to Claude → Analyze gaps
                                     │
                                     └──→ Return to UI
```

### Flow Diagram

```
┌─────────────────┐
│  Streamlit UI   │
└────────┬────────┘
         │
         ▼
┌────────────────────────────┐
│   Query Handler            │  ← Future: Fetch.ai InsightAgent
│  - Checks local databases  │
│  - Fetches from arXiv      │
│  - Ingests papers          │
│  - Calls Claude API        │
└──────┬─────────────────────┘
       │
   ┌───┴────────┬─────────────┐
   ▼            ▼             ▼
┌─────────┐ ┌─────────┐ ┌──────────┐
│ Elastic │ │ Chroma  │ │  arXiv   │
│ Search  │ │ Vector  │ │   API    │
│         │ │   DB    │ │          │
└─────────┘ └─────────┘ └──────────┘
```

### Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| **Frontend** | User interface | Streamlit |
| **Query Handler** | Coordinates retrieval & synthesis | Python |
| **arXiv Client** | Fetches papers from arXiv | arXiv API |
| **Elastic Client** | Keyword search & metadata storage | Elasticsearch |
| **Chroma Client** | Semantic similarity search | ChromaDB |
| **Claude Client** | Research gap analysis | Anthropic Claude API |
| **Data Ingestor** | Paper parsing & upload | Python |

## 📦 Project Structure

```
ResearchCH12/
├── app.py                      # Streamlit web application
├── backend/
│   ├── __init__.py            # Module exports
│   ├── config.py              # Configuration & API credentials
│   ├── arxiv_client.py        # arXiv API integration (NEW!)
│   ├── elastic_client.py      # Elasticsearch integration
│   ├── chroma_client.py       # Chroma vector DB integration
│   ├── claude_client.py       # Claude API integration
│   ├── data_ingestion.py      # Paper ingestion pipeline
│   └── query_handler.py       # Query orchestration + arXiv fetching
├── clear_data.py               # Script to clear databases
├── test_backend.py             # Backend diagnostics
├── requirements.txt            # Python dependencies
├── chroma_db/                  # Local Chroma database (auto-created)
├── ARXIV_INTEGRATION.md        # arXiv integration guide
└── README.md                   # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- Internet connection (for arXiv)
- Elasticsearch account ✅ (already configured)
- Claude API key ✅ (already configured)

### 2. Installation

```bash
# Install dependencies (includes arXiv package)
pip install -r requirements.txt
```

### 3. Clear Sample Data (Optional)

If you previously used sample papers:

```bash
python clear_data.py
```

Type `yes` to confirm. This prepares the system for arXiv integration.

### 4. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### 5. Search for ANY Research Topic!

Try searching for:
- **AI/ML**: `large language models`, `graph neural networks`, `computer vision`
- **Quantum**: `quantum computing`, `quantum machine learning`, `quantum algorithms`
- **Privacy**: `differential privacy`, `federated learning`, `secure multi-party computation`
- **Biology**: `protein folding`, `gene expression`, `drug discovery`
- **Physics**: `quantum gravity`, `dark matter`, `string theory`
- **Anything!**: The system will fetch real papers from arXiv

### 6. What Happens on First Search

1. 🔍 System checks local databases
2. 📥 Finds no papers → Fetches from arXiv (takes ~5-10 seconds)
3. 💾 Stores papers in Elasticsearch + Chroma
4. 🤖 Claude analyzes them
5. 📊 Displays results with citations and dates

### 7. Subsequent Searches

- Same topic: Uses cached papers (fast!)
- New topic: Fetches more papers automatically
- Papers persist across sessions

## 🔧 Backend API

### Query Handler

```python
from backend.query_handler import get_query_handler

handler = get_query_handler()

# Query research gaps
result = handler.query_research_gaps(
    topic="quantum simulation",
    n_results=10,
    use_semantic=True,  # Use Chroma vector search
    use_keyword=True    # Use Elastic keyword search
)

print(result["summary"])
print(result["limitations"])
print(result["future_directions"])
```

### Data Ingestion

```python
from backend.data_ingestion import get_paper_ingestor

ingestor = get_paper_ingestor()

# Ingest a single paper
paper_data = {
    "title": "Example Paper Title",
    "authors": "Smith, J.; Doe, A.",
    "year": 2024,
    "abstract": "Paper abstract...",
    "field": "machine_learning"
}

sections = {
    "abstract": "Paper abstract...",
    "conclusion": "Conclusions...",
    "future_work": "Future directions..."
}

success = ingestor.ingest_paper(paper_data, sections)
```

### Direct Client Access

```python
# Elasticsearch
from backend.elastic_client import get_elastic_client
elastic = get_elastic_client()
papers = elastic.search_papers("quantum computing", size=5)

# Chroma
from backend.chroma_client import get_chroma_client
chroma = get_chroma_client()
results = chroma.semantic_search("neural networks", n_results=5)

# Claude
from backend.claude_client import get_claude_client
claude = get_claude_client()
analysis = claude.analyze_research_gaps(topic, paper_sections)
```

## 🤖 Future: Fetch.ai Integration

The architecture is designed for easy migration to Fetch.ai agent orchestration:

### Planned Agents

1. **IngestAgent**
   - Parses and uploads paper metadata
   - Handles bulk ingestion operations
   - Maintains data consistency

2. **InsightAgent**
   - Receives user queries
   - Coordinates retrieval across Elastic and Chroma
   - Calls Claude API for synthesis
   - Returns structured results

### Integration Points

```python
# backend/query_handler.py contains FetchAgentInterface class
# Ready for implementation after agent deployment

from backend.query_handler import FetchAgentInterface

agent_interface = FetchAgentInterface(
    insight_agent_address="agent1q..."
)

result = await agent_interface.query_via_agent("quantum simulation")
```

## 📊 Sample Data

The system includes 5 sample papers covering:

1. **Quantum Simulation** - SU(3) Lattice Gauge Theory
2. **Transformer Interpretability** - Attention Mechanisms
3. **Vector Databases** - Scalable Architecture for AI
4. **Federated Learning** - Differential Privacy
5. **Drug Discovery** - Graph Neural Networks

## 🛠️ Development

### Adding New Papers

```python
python ingest_sample_data.py  # Loads predefined samples

# Or programmatically:
from backend.data_ingestion import get_paper_ingestor

ingestor = get_paper_ingestor()
papers = [...]  # Your paper data
results = ingestor.ingest_papers_batch(papers)
```

### Monitoring

Check system status:

```python
from backend.query_handler import get_query_handler

handler = get_query_handler()
stats = handler.get_collection_stats()

print(f"Chroma documents: {stats['chroma_documents']}")
print(f"Status: {stats['status']}")
```

### Testing Without Claude API

The system works in mock mode without a Claude API key:
- Returns sample analysis data
- Allows testing of retrieval pipelines
- Useful for development and debugging

## 🐛 Troubleshooting

### Elasticsearch Connection Issues

```bash
# Verify credentials in backend/config.py
# Check that the URL is accessible:
curl https://my-elasticsearch-project-cf6e91.es.us-central1.gcp.elastic.cloud:443
```

### Chroma Database Issues

```bash
# Reset Chroma database
rm -rf chroma_db/
python ingest_sample_data.py  # Re-ingest data
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

## 📝 API Credentials

### Elasticsearch (Already Configured)

```
URL: https://my-elasticsearch-project-cf6e91.es.us-central1.gcp.elastic.cloud:443
API Key: ck-nQkNRS43HxvzLMDgwck9Bahf3RAXFhmpScAeVoQYLpK
Tenant: 5b0d022c-f700-43ea-8aed-698c89faebbe
```

### Claude API (Optional)

Get your API key from: https://console.anthropic.com/

Add to `backend/config.py` or set as environment variable.

## 🎓 Use Cases

- **Researchers**: Discover unexplored areas in your field
- **PhD Students**: Identify dissertation topics
- **Grant Writers**: Find funding opportunities in research gaps
- **Literature Reviews**: Quickly synthesize limitations across papers
- **Innovation Teams**: Spot emerging research directions

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

This is a research project. Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📮 Contact

For questions or issues, please open a GitHub issue.

---

**Built with ❤️ using Claude, Elasticsearch, Chroma, and Streamlit**
