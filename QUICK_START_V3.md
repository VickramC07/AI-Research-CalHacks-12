# 🚀 Quick Start: ScholarForge v3.0

## ✨ What's New

Your ScholarForge system now has **5 major upgrades**:

1. **🤖 Research Chatbot** - AI assistant at bottom of page
2. **📚 4 Paper Sources** - arXiv + Semantic Scholar + PubMed + Crossref
3. **📅 Recent Papers** - Prioritizes 2020+ papers
4. **✅ Minimum 5 Papers** - Always returns at least 5 papers
5. **🌐 Diverse Coverage** - CS, biomedical, and general research

---

## 🏃 Quick Start (5 Minutes)

### 1. Run the App

```bash
streamlit run app.py
```

### 2. Search for a Topic

**Example searches**:
- **CS topic**: "transformer architectures"
- **Biomedical topic**: "CRISPR gene editing"
- **General topic**: "climate change modeling"

### 3. View Results

You'll see:
- ✅ Research gap analysis
- ✅ **10 papers** from multiple sources
- ✅ **Source pie chart** (bottom left) - shows arXiv, PubMed, etc.
- ✅ **Year bar chart** (bottom right) - shows 2020-2024 distribution

### 4. Use the Chatbot

**Scroll to the bottom** of the page and you'll see:

```
🤖 Research Assistant Chat
Ask questions about papers, get recommendations, or explore research topics
```

**Try asking**:
- "What are the latest papers on quantum computing?"
- "Explain the research gaps in transformer models"
- "Find papers similar to CRISPR applications"

---

## 📊 What You'll See

### Search Results Page

```
┌─────────────────────────────────────────────────────────┐
│                    ScholarForge                         │
│           [Search: "quantum computing"]                 │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 🔍 Research Gap Summary                                 │
│ Current quantum computing research focuses on...        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ ⚠️ Common Limitations                                   │
│ L1  Limited quantum coherence time                      │
│ L2  High error rates in quantum gates                   │
│ L3  Scalability challenges                              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 🚀 Future Directions                                    │
│ Direction 1: Develop error-correcting codes            │
│ Direction 2: Improve qubit connectivity                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 📈 Keyword Trend Analysis                               │
│ [Bar chart showing keyword frequencies]                 │
└─────────────────────────────────────────────────────────┘

┌──────────────────────┐ ┌──────────────────────────────┐
│ 📊 Paper Sources     │ │ 📅 Publication Years         │
│ [Pie chart]          │ │ [Bar chart]                  │
│ - arXiv: 45%         │ │ 2024: 2 papers              │
│ - PubMed: 30%        │ │ 2023: 5 papers              │
│ - Crossref: 15%      │ │ 2022: 2 papers              │
│ - Semantic Scholar:10%│ │ 2021: 1 paper               │
└──────────────────────┘ └──────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 🤖 Research Assistant Chat                              │
│                                                          │
│ You: What are the latest papers on this topic?          │
│ Bot: Based on recent research, here are the latest...   │
│                                                          │
│ [Type your message here...]                             │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Key Features Explained

### 1. Multi-Source Fetching

**What happens when you search**:

```
1. Search local database (Elasticsearch)
   ├─ Found 2 papers → Need 3 more (minimum 5)
   └─ Fetch from external sources:

2. Try arXiv
   ├─ Found 1 paper (recent, 2020+)
   └─ Still need 2 more

3. Try Semantic Scholar
   ├─ Found 0 papers (rate limited)
   └─ Still need 2 more

4. Try PubMed (good for biomedical)
   ├─ Found 2 papers (perfect!)
   └─ Got 5 papers total ✅

5. Display results:
   - 2 from Elasticsearch (already stored)
   - 1 from arXiv
   - 2 from PubMed
   - All ingested into database for future use
```

### 2. Recent Paper Prioritization

**Default**: Papers from **2020 onwards**

**Why**: Recent papers are more relevant for:
- Current research trends
- Latest methodologies
- Modern citations
- Ongoing debates

**Customize**:

```python
# In app.py, line 31:
handler = QueryHandler(fetch_from_arxiv=True, min_year=2022)  # 2022+
handler = QueryHandler(fetch_from_arxiv=True, min_year=2018)  # 2018+
```

### 3. Chatbot Usage

The chatbot uses your **Elastic AI agents**:
- **paper_chaser_gamma** (default) - Paper recommendation & search
- **ScholarBot** - Research assistance

**Good questions**:
- ✅ "Find recent papers on [topic]"
- ✅ "What are research gaps in [field]?"
- ✅ "Recommend papers similar to [paper title]"
- ✅ "Explain [research concept]"

**Not ideal**:
- ❌ "How do I cook pasta?" (not research-related)
- ❌ "What's the weather?" (off-topic)

---

## 🔧 Configuration Options

### Change Minimum Year

```python
# app.py, line 31
handler = QueryHandler(fetch_from_arxiv=True, min_year=2020)

# Options:
# - min_year=2024  → Only 2024 papers
# - min_year=2020  → 2020+ (default, recommended)
# - min_year=2015  → 2015+
# - min_year=None  → All years
```

### Change Minimum Papers

```python
# backend/query_handler.py, line 123
min_required = max(5, n_results)

# Options:
# - max(10, n_results)  → Minimum 10 papers
# - max(3, n_results)   → Minimum 3 papers
```

### Disable Specific Sources

```python
# backend/query_handler.py, lines 134-139
sources = [
    ("arXiv", self._fetch_and_ingest_from_arxiv),
    ("Semantic Scholar", self._fetch_and_ingest_from_semantic_scholar),
    # ("PubMed", self._fetch_and_ingest_from_pubmed),  # Disabled
    ("Crossref", self._fetch_and_ingest_from_crossref),
]
```

---

## 📈 Example Searches

### Example 1: CS Topic

```
Search: "neural architecture search"

Results:
- 10 papers
- Sources: 8 arXiv, 2 Semantic Scholar
- Years: All 2020+
- Chatbot: "Explain NAS methods" → Detailed explanation

Time: ~5 seconds
```

### Example 2: Biomedical Topic

```
Search: "COVID-19 vaccine efficacy"

Results:
- 10 papers
- Sources: 7 PubMed, 2 Crossref, 1 arXiv
- Years: 2020-2024 (pandemic-relevant)
- Chatbot: "Find latest clinical trials" → Recent studies

Time: ~6 seconds (PubMed fetching)
```

### Example 3: Mixed Domain

```
Search: "quantum machine learning"

Results:
- 10 papers
- Sources: 5 arXiv, 3 Crossref, 2 Semantic Scholar
- Years: 2021-2024
- Chatbot: "Compare quantum vs classical ML" → Comparison

Time: ~5 seconds
```

---

## 🐛 Troubleshooting

### Issue: Chatbot Not Responding

**Possible causes**:
1. Elastic agents not configured
2. API key doesn't have agent permissions
3. Agent IDs/names incorrect

**Solution**:
- Check agent exists in Elastic: `paper_chaser_gamma`
- Verify API key permissions
- Check console logs for errors

**Workaround**: Other features (search, analysis) still work

### Issue: PubMed Rate Limiting

**Error**: "Too many requests"

**Solution**: The system already has delays built in (0.34s)

**If persists**: Increase delay in `backend/pubmed_client.py`:
```python
time.sleep(1.0)  # Increase from 0.34 to 1.0
```

### Issue: Slow External Fetching

**Why**: Fetching from 4 sources takes time

**Normal**: 5-15 seconds for multi-source fetch
**Expected**: First search slower, subsequent faster (uses cache)

**Tip**: Preload papers to avoid on-demand fetching:
```bash
python preload_papers.py --target 10000
```

---

## ✅ Verification Checklist

After starting the app, verify:

- [ ] App loads without errors
- [ ] Search returns 10 papers (or at least 5)
- [ ] Source pie chart shows multiple sources
- [ ] Year bar chart shows 2020+ distribution
- [ ] Chatbot appears at bottom of page
- [ ] Chatbot responds to messages (if agents configured)
- [ ] Papers display with correct source labels

---

## 📚 Documentation

- **`VERSION_3_FEATURES.md`** - Comprehensive feature documentation
- **`MULTISOURCE_VISUALIZATION_SUMMARY.md`** - Visualization details
- **`LARGE_SCALE_GUIDE.md`** - Scaling and preloading
- **`README.md`** - General usage guide

---

## 🎉 You're Ready!

Your ScholarForge v3.0 is production-ready with:

✅ Multi-source paper fetching
✅ Recent paper prioritization
✅ Minimum 5 papers guarantee
✅ Interactive chatbot
✅ Diverse source coverage
✅ Beautiful visualizations

**Start searching and discovering research gaps! 🚀📚🔬**

---

## 🆘 Need Help?

**Common commands**:
```bash
# Run app
streamlit run app.py

# Test features
python3 test_v3_features.py

# Test backend
python3 test_backend.py

# Test visualizations
python3 test_visualizations.py
```

**Check logs** for detailed information:
- Console output shows which sources are used
- Error messages indicate API issues
- "INFO" logs show fetching progress

**Everything working? Enjoy your upgraded research discovery system!** 🎊
