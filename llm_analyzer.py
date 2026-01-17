"""
LLM Analyzer (LLM#1) using Groq with GPT OSS 120B.
Analyzes news articles for gist, sentiment, and tone.
"""

import os
import requests
import json
import time

class LLMAnalyzer:
    """Analyzes news articles using Groq (GPT OSS 120B model)."""
    
    def __init__(self):
        """Initialize Groq API with key from environment."""
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "openai/gpt-oss-120b"
    
    def analyze_article(self, article):
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
Analyze the following news article about Indian politics and provide:
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

Do not include any text before or after the JSON.
        """.strip()
        
        try:
            # Generate response with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        self.base_url,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": self.model,
                            "messages": [
                                {
                                    "role": "user",
                                    "content": prompt
                                }
                            ],
                            "temperature": 0.3
                        },
                        timeout=30
                    )
                    
                    # Handle rate limiting
                    if response.status_code == 429:
                        print("    Rate limit hit, waiting...")
                        time.sleep(5)
                        continue
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    # Extract response text
                    response_text = data['choices'][0]['message']['content'].strip()
                    
                    # Clean up response (remove markdown code blocks if present)
                    if response_text.startswith('```json'):
                        response_text = response_text[7:]
                    if response_text.startswith('```'):
                        response_text = response_text[3:]
                    if response_text.endswith('```'):
                        response_text = response_text[:-3]
                    response_text = response_text.strip()
                    
                    # Parse JSON
                    analysis = json.loads(response_text)
                    
                    # Validate required fields
                    required_fields = ['gist', 'sentiment', 'tone']
                    if all(field in analysis for field in required_fields):
                        return analysis
                    else:
                        raise ValueError("Missing required fields in response")
                
                except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                    if attempt < max_retries - 1:
                        print(f"    Error, retrying... (attempt {attempt + 1})")
                        time.sleep(2)
                        continue
                    else:
                        raise
            
        except Exception as e:
            print(f"    Error analyzing article: {str(e)}")
            # Return default analysis on error
            return {
                'gist': 'Unable to analyze article',
                'sentiment': 'neutral',
                'tone': 'unknown',
                'error': str(e)
            }