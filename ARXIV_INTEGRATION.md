# arXiv Integration Guide

## 🎉 What's New

ScholarForge now **dynamically fetches real research papers** from arXiv! No more sample data - the system automatically retrieves, stores, and analyzes real papers on-demand.

## 🔄 How It Works

```
User searches for "quantum computing"
         ↓
Check local databases (Elastic + Chroma)
         ↓
    No results found?
         ↓
Fetch from arXiv API (10 papers)
         ↓
Ingest into Elastic + Chroma
         ↓
Re-search and analyze with Claude
         ↓
Display results to user
```

### Key Features

1. **On-Demand Fetching**: Papers are fetched only when needed
2. **Auto-Caching**: Once fetched, papers stay in your databases
3. **Duplicate Prevention**: Won't re-fetch papers already in system
4. **Real Metadata**: Publication dates, authors, venues, DOIs
5. **Full Abstracts**: Complete abstracts analyzed by Claude

## 📊 What Gets Stored

### Elasticsearch
- Title, authors, year, venue
- Abstract and full text
- DOI and PDF URL
- arXiv categories
- Publication/update dates

### Chroma Vector DB
- Embedded abstract
- Metadata (title, authors, year, field)
- Section name
- Used for semantic similarity search

## 🚀 Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This includes the `arxiv` Python package.

### 2. Clear Sample Data (Optional)

```bash
python clear_data.py
```

This removes the 5 sample papers and prepares the system for arXiv.

### 3. Run the App

```bash
streamlit run app.py
```

### 4. Search for Any Topic

Try searching for:
- "quantum computing"
- "graph neural networks"
- "large language models"
- "federated learning privacy"
- "computer vision transformers"
- Literally anything!

The system will:
1. Check if papers exist locally
2. If not, fetch from arXiv
3. Store them automatically
4. Analyze and display results

## 🔍 Search Examples

### Broad Topics
- `machine learning` - Returns 10 ML papers
- `quantum computing` - Returns quantum papers
- `natural language processing` - Returns NLP papers

### Specific Topics
- `graph neural networks for drug discovery`
- `transformer interpretability`
- `differential privacy in federated learning`

### By Category
The system searches all arXiv categories:
- `cs.AI` - Artificial Intelligence
- `cs.LG` - Machine Learning
- `cs.CV` - Computer Vision
- `quant-ph` - Quantum Physics
- And many more!

## 💾 Data Management

### View What's Stored

```bash
python test_backend.py
```

Shows:
- Number of papers in Elasticsearch
- Number of documents in Chroma
- Sample search results

### Clear All Data

```bash
python clear_data.py
```

Removes all papers (sample + arXiv) and resets databases.

### Add More Papers for a Topic

Just search again! The system will fetch 10 more recent/relevant papers.

## 📈 Performance

- **First search for a topic**: ~5-10 seconds (fetching + ingesting)
- **Subsequent searches**: ~2-3 seconds (analyzing cached papers)
- **arXiv API**: Returns up to 10 papers per query
- **Storage**: Each paper ~5-10 KB in Elastic, ~1-2 KB in Chroma

## 🔧 Configuration

### Disable arXiv Fetching

If you want to only use local papers:

```python
# In app.py
handler = get_query_handler(fetch_from_arxiv=False)
```

### Adjust Number of Papers

```python
# In backend/query_handler.py, line ~99
arxiv_papers = self._fetch_and_ingest_from_arxiv(
    topic,
    n_results=20  # Changed from 10
)
```

### Filter by Recency

Fetch only recent papers:

```python
from backend.arxiv_client import get_arxiv_client

arxiv = get_arxiv_client()
papers = arxiv.search_recent_papers(
    query="quantum computing",
    max_results=10,
    days=30  # Last 30 days only
)
```

## 🛠️ API Usage

### Direct arXiv Client

```python
from backend.arxiv_client import get_arxiv_client

arxiv = get_arxiv_client()

# Search by query
papers = arxiv.search_papers("machine learning", max_results=5)

# Get specific paper
paper = arxiv.get_paper_by_id("2301.12345")

# Search by category
ai_papers = arxiv.search_by_category("cs.AI", max_results=10)

# Recent papers only
recent = arxiv.search_recent_papers("transformers", max_results=5, days=7)
```

### Manual Ingestion

```python
from backend.data_ingestion import get_paper_ingestor
from backend.arxiv_client import get_arxiv_client

arxiv = get_arxiv_client()
ingestor = get_paper_ingestor()

# Fetch papers
papers = arxiv.search_papers("neural networks", max_results=10)

# Ingest into databases
results = ingestor.ingest_arxiv_papers(papers)
print(f"Ingested {results['success']} papers")
```

## 🎯 arXiv Paper Format

Each paper from arXiv includes:

```json
{
  "paper_id": "arxiv_2301.12345",
  "title": "Paper Title",
  "authors": "Author A; Author B; Author C",
  "year": 2023,
  "venue": "arXiv",
  "field": "machine_learning",
  "abstract": "Full abstract text...",
  "url": "https://arxiv.org/abs/2301.12345",
  "pdf_url": "https://arxiv.org/pdf/2301.12345",
  "doi": "10.1234/example",
  "categories": ["cs.LG", "cs.AI"],
  "primary_category": "cs.LG",
  "published": "2023-01-15T00:00:00",
  "updated": "2023-01-20T00:00:00",
  "sections": {
    "abstract": "...",
    "future_work": "...",  // Extracted from abstract if mentioned
    "limitations": "..."   // Extracted from abstract if mentioned
  }
}
```

## 🚨 Limitations

### arXiv API Limitations
- **Rate Limits**: 1 request per 3 seconds (handled automatically)
- **Max Results**: Can fetch many papers, but recommend 10-20 per query
- **No Full Text**: Only abstracts available (not full PDF content)
- **Search Quality**: Depends on arXiv's search algorithm

### System Limitations
- **First Search Delay**: Takes a few seconds to fetch + ingest
- **Storage**: Will grow over time (monitor disk space)
- **Abstract-Only Analysis**: Claude analyzes abstracts, not full papers

### Workarounds
- **Full Text**: Would require PDF parsing (complex)
- **Better Search**: Combine multiple searches or use specific arXiv categories
- **Storage**: Periodically clear old papers with `clear_data.py`

## 📚 arXiv Categories

ScholarForge maps arXiv categories to fields:

| arXiv Category | Field |
|----------------|-------|
| cs.AI | artificial_intelligence |
| cs.LG | machine_learning |
| cs.CL | natural_language_processing |
| cs.CV | computer_vision |
| cs.CR | cryptography |
| cs.DB | databases |
| quant-ph | quantum_computing |
| stat.ML | machine_learning |
| q-bio | computational_biology |

And many more! See `backend/arxiv_client.py` for full mapping.

## 🔮 Future Enhancements

Potential improvements:
1. **PDF Full Text Extraction** - Parse PDFs for complete paper text
2. **Citation Networks** - Fetch cited/citing papers
3. **Advanced Filters** - Date ranges, specific authors, institutions
4. **Scheduled Updates** - Periodic fetch of new papers in saved topics
5. **Paper Rankings** - Sort by citations, recency, relevance

## 🤝 Integration with Fetch.ai

The arXiv integration is designed to work seamlessly with Fetch.ai agents:

```python
# Future: IngestAgent handles arXiv fetching
class IngestAgent:
    async def handle_query(self, topic):
        # Fetch from arXiv
        papers = await self.arxiv.search_papers(topic)

        # Ingest into databases
        await self.ingestor.ingest_papers(papers)

        # Notify InsightAgent
        await self.send_message(insight_agent, "papers_ready")
```

## ✅ Testing

Test the arXiv integration:

```bash
# 1. Clear existing data
python clear_data.py

# 2. Run tests
python test_backend.py

# 3. Try a search in the app
streamlit run app.py
# Search for "quantum machine learning"
```

You should see:
- Console log: "Fetching papers from arXiv..."
- Papers being ingested
- Results displayed with real arXiv papers

## 📞 Troubleshooting

### "No papers found on arXiv"
- Check your internet connection
- Try a different/broader search term
- arXiv might be temporarily unavailable

### "Error fetching from arXiv"
- Install: `pip install arxiv>=2.0.0`
- Check Python version (3.8+ required)

### Papers Not Appearing
- Check Elasticsearch connection
- Run: `python test_backend.py`
- Verify credentials in `backend/config.py`

### Slow Performance
- First search is always slower (fetching)
- Subsequent searches use cached papers
- Reduce `n_results` if too slow

---

**🎉 Enjoy unlimited research papers from arXiv!**

No more sample data - your research gap discovery system is now powered by real, up-to-date papers from the world's largest open-access archive.
