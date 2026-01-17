
import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

# Import existing modules
from news_fetcher import NewsFetcher
from llm_analyzer import LLMAnalyzer
from llm_validator import LLMValidator
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env vars
load_dotenv()

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:3000",  # Frontend URL
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/analyze")
async def analyze_news(request: Request, topic: str = "Indian Politics", count: int = 12):
    """
    Streams analysis progress and results using Server-Sent Events (SSE).
    """
    async def event_generator() -> AsyncGenerator[dict, None]:
        try:
            # --- Step 1: Initialization ---
            yield {
                "event": "log",
                "data": json.dumps({"message": f"Initializing pipeline for '{topic}' ({count} articles)...", "step": "fetch"})
            }
            await asyncio.sleep(0.5)

            # --- Step 2: Fetching ---
            yield {
                "event": "log",
                "data": json.dumps({"message": "Connecting to NewsAPI...", "step": "fetch"})
            }
            
            fetcher = NewsFetcher()
            # Run blocking code in thread pool
            articles = await asyncio.to_thread(fetcher.fetch_news, topic=topic, num_articles=count)
            
            if not articles:
                yield {
                    "event": "error",
                    "data": json.dumps({"message": "No articles found or API error."})
                }
                return

            yield {
                "event": "log",
                "data": json.dumps({"message": f"Retrieved {len(articles)} articles successfully", "step": "fetch"})
            }
            await asyncio.sleep(0.5)

            # --- Step 3: Analysis ---
            yield {
                "event": "log",
                "data": json.dumps({"message": "Starting LLM Analysis (Stage 1)...", "step": "analyze"})
            }

            analyzer = LLMAnalyzer()
            analysis_results = []
            
            for idx, article in enumerate(articles, 1):
                if await request.is_disconnected():
                    logger.info("Client disconnected during analysis")
                    return

                yield {
                    "event": "log",
                    "data": json.dumps({"message": f"Analyzed article {idx}/{len(articles)}: Sentiment analysis complete", "step": "analyze"})
                }
                
                # Run async analysis
                analysis = await analyzer.analyze_article(article)
                analysis_results.append({
                    'article': article,
                    'analysis': analysis
                })
                # Taking a small breath to not hit rate limits too hard if concurrent
                # (though existing code had 3s sleep, we might want faster for UI demo)
                await asyncio.sleep(1) 

            yield {
                "event": "log",
                "data": json.dumps({"message": "Analysis stage 1 complete - moving to validation", "step": "analyze"})
            }

            # --- Step 4: Validation ---
            yield {
                "event": "log",
                "data": json.dumps({"message": "Starting LLM Validation (Stage 2)...", "step": "validate"})
            }

            validator = LLMValidator()
            final_articles = []

            for idx, result in enumerate(analysis_results, 1):
                if await request.is_disconnected():
                    return

                yield {
                    "event": "log",
                    "data": json.dumps({"message": f"Validating article {idx}/{len(analysis_results)}...", "step": "validate"})
                }
                
                validation = await validator.validate_analysis(
                    result['article'], 
                    result['analysis']
                )

                # Format for frontend
                final_articles.append({
                    "id": idx,
                    "title": result['article']['title'],
                    "sentiment": result['analysis'].get('sentiment', 'neutral').lower(),
                    "validationPassed": validation.get('is_valid', False),
                    "validationNote": validation.get('notes', ''),
                    "summary": result['analysis'].get('gist', ''),
                    "url": result['article'].get('url', '#')
                })
                await asyncio.sleep(1)

            yield {
                "event": "log",
                "data": json.dumps({"message": "All articles validated successfully", "step": "validate"})
            }
            
            # --- Step 5: Done ---
            yield {
                "event": "log",
                "data": json.dumps({"message": "Pipeline complete - results ready", "step": "done"})
            }
            
            # Send final data
            yield {
                "event": "result",
                "data": json.dumps({"articles": final_articles})
            }
            
            # Close stream
            yield {
                "event": "close",
                "data": json.dumps({"message": "Stream closed"})
            }

        except Exception as e:
            logger.error(f"Error in analyze_news: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"message": f"Internal Server Error: {str(e)}"})
            }

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
