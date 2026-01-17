# News Analysis Pipeline with Dual LLM Validation

A production-ready Python pipeline that fetches recent news about Indian politics, analyzes articles using Groq (GPT OSS 120B), and validates the analysis using Groq (GPT OSS 20B).

## Features

- 📰 Fetches recent news from NewsAPI
- 🤖 Dual-LLM architecture for enhanced accuracy
- ✅ Automated validation and quality checks
- 📊 Generates comprehensive reports (JSON + Markdown)
- 🧪 Full test coverage with pytest
- 🔒 Secure API key management with .env

## Project Structure

```
news-analyzer/
├── main.py                      # Entry point & orchestration
├── news_fetcher.py              # NewsAPI integration
├── llm_analyzer.py              # LLM#1: Groq GPT OSS 120B analysis
├── llm_validator.py             # LLM#2: Groq GPT OSS 20B validation
├── requirements.txt             # Python dependencies
├── .env.template                # API key template
├── .gitignore                   # Git ignore rules
├── DEVELOPMENT_PROCESS.md       # Development documentation
├── README.md                    # This file
├── tests/
│   └── test_analyzer.py         # Unit tests
└── output/                      # Generated reports (created on first run)
    ├── raw_articles.json
    ├── analysis_results.json
    ├── validated_results.json
    └── final_report.md
```

## Installation

### Prerequisites
- Python 3.8 or higher
- API keys for:
  - [NewsAPI](https://newsapi.org/)
  - [Groq](https://console.groq.com/keys)

### Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd news-analyzer
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure API keys**
```bash
# Copy the template
cp .env.template .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

Your `.env` should look like:
```env
NEWSAPI_KEY=your_actual_newsapi_key
GROQ_API_KEY=your_actual_groq_key
```

## Usage

### Run the Full Pipeline

```bash
python main.py
```

This will:
1. Fetch 12 recent articles about Indian politics
2. Analyze each with Gemini (gist, sentiment, tone)
3. Validate each analysis with Mistral
4. Generate comprehensive reports

### Expected Output

```
============================================================
NEWS ANALYSIS PIPELINE - DUAL LLM VALIDATION
============================================================

[Step 1/5] Setting up...
✓ Created output directory

[Step 2/5] Fetching news articles...
  Requesting articles from NewsAPI...
✓ Saved raw_articles.json
✓ Fetched 12 articles

[Step 3/5] Analyzing with LLM#1 (Groq GPT OSS 120B)...
  Analyzing article 1/12... ✓
  Analyzing article 2/12... ✓
  ...
✓ Saved analysis_results.json

[Step 4/5] Validating with LLM#2 (Groq GPT OSS 20B)...
  Validating article 1/12... ✓
  Validating article 2/12... ✓
  ...
✓ Saved validated_results.json

[Step 5/5] Generating final report...
✓ Generated final_report.md

============================================================
PIPELINE COMPLETED SUCCESSFULLY!
============================================================
```

### Run Tests

```bash
# Run all tests with verbose output
pytest tests/test_analyzer.py -v

# Run with coverage
pytest tests/test_analyzer.py --cov
```

## Output Files

### 1. `raw_articles.json`
Raw articles from NewsAPI with fields:
- title, description, content
- url, publishedAt, source

### 2. `analysis_results.json`
Each article with LLM#1 analysis:
```json
{
  "article": {...},
  "analysis": {
    "gist": "1-2 sentence summary",
    "sentiment": "positive/negative/neutral",
    "tone": "analytical/urgent/balanced/etc"
  }
}
```

### 3. `validated_results.json`
Full results with LLM#2 validation:
```json
{
  "article": {...},
  "analysis": {...},
  "validation": {
    "is_valid": true,
    "notes": "Explanation of validation"
  }
}
```

### 4. `final_report.md`
Human-readable markdown report with:
- Summary statistics
- Detailed analysis of each article
- Validation status with explanations

## Architecture

### Why Dual-LLM?

1. **LLM#1 (Groq GPT OSS 120B)**: Fast, intelligent analysis
2. **LLM#2 (Groq GPT OSS 20B)**: Independent validation catches errors

This cross-validation approach using two different models reduces hallucinations and improves accuracy.

### Error Handling

- **Timeouts**: 10-second timeout on NewsAPI, 30-second on LLMs
- **Rate Limits**: Automatic retry with backoff
- **Malformed JSON**: Cleanup logic + retry mechanism
- **Missing Data**: Graceful degradation with default values

## Development Philosophy

This project follows the **"You Break Down; AI Executes"** approach:

1. **Human**: Define architecture, break into tasks
2. **AI**: Generate boilerplate, handle edge cases
3. **Human**: Review, refine, test, document

See `DEVELOPMENT_PROCESS.md` for detailed development workflow.

## Testing

Tests cover:
- ✅ API initialization (missing keys)
- ✅ Successful operations (mocked)
- ✅ Error handling (timeouts, malformed responses)
- ✅ Data structure validation

Run tests before deployment:
```bash
pytest tests/test_analyzer.py -v
```

## Troubleshooting

### Common Issues

**"NEWSAPI_KEY not found"**
- Ensure `.env` file exists in project root
- Check that API key is correctly formatted (no quotes)

**"Rate limit exceeded"**
- Groq free tier: 14,400 requests/day
- Wait or upgrade plan

**"JSON decode error"**
- LLM responses occasionally malformed
- Retry logic handles this automatically
- If persistent, check API status

**No articles fetched**
- Check NewsAPI quota
- Verify internet connection
- Try broader search query

## Future Enhancements

- [ ] Add caching for article fetches
- [ ] Implement parallel processing with `asyncio`
- [ ] Store results in SQLite database
- [ ] Add web dashboard for results visualization
- [ ] Support multiple news sources
- [ ] Add fact-checking with third LLM

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request
