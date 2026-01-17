import os
import json
import logging
from openai import AsyncOpenAI, APIError

logger = logging.getLogger(__name__)

class LLMAnalyzer:
    """Analyzes news articles using Groq (Llama 3.3 70B)."""
    
    def __init__(self):
        """Initialize Groq client."""
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = "llama-3.3-70b-versatile"
    
    async def analyze_article(self, article):
        """
        Analyze a single article for gist, sentiment, and tone.
        
        Args:
            article: Dictionary with 'title', 'description', 'content'
            
        Returns:
            Dictionary with 'gist', 'sentiment', 'tone'
        """
        # Build the article text
        article_text = f"""
Title: {article.get('title', '')}
Description: {article.get('description', '')}
Content: {article.get('content', '')}
        """.strip()
        
        # Create analysis prompt
        prompt = f"""
Analyze the following news article and provide:
1. Gist: A 1-2 sentence summary of the news
2. Sentiment: Choose one - positive, negative, or neutral
3. Tone: Choose one or more - urgent, analytical, satirical, balanced, critical, optimistic, alarmist

Article:
{article_text}

Respond ONLY with valid JSON in this exact format:
{{
  "gist": "your 1-2 sentence summary here",
  "sentiment": "positive/negative/neutral",
  "tone": "analytical"
}}
        """.strip()
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content
            analysis = json.loads(response_text)
            
            # Validate required fields
            required_fields = ['gist', 'sentiment', 'tone']
            if all(field in analysis for field in required_fields):
                return analysis
            else:
                raise ValueError("Missing required fields in response")
            
        except Exception as e:
            logger.error(f"Error analyzing article: {str(e)}")
            return {
                'gist': 'Unable to analyze article',
                'sentiment': 'neutral',
                'tone': 'unknown',
                'error': str(e)
            }