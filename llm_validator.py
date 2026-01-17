"""
LLM Validator (LLM#2) using Groq with GPT OSS 20B.
Validates analysis from LLM#1 against the original article.
"""

import os
import requests
import json
import time

class LLMValidator:
    """Validates analysis using Groq (GPT OSS 20B model)."""
    
    def __init__(self):
        """Initialize Groq API with key from environment."""
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "openai/gpt-oss-20b"
    
    def validate_analysis(self, article, analysis):
        """
        Validate if the analysis matches the article content.
        
        Args:
            article: Original article dictionary
            analysis: Analysis from LLM#1 with gist, sentiment, tone
            
        Returns:
            Dictionary with validation results
        """
        # Build article text
        article_text = f"""
Title: {article.get('title', '')}
Description: {article.get('description', '')}
Content: {article.get('content', '')}
        """.strip()
        
        # Build validation prompt
        prompt = f"""
You are a fact-checker validating an AI's analysis of a news article.

Original Article:
{article_text}

AI Analysis:
- Gist: {analysis.get('gist', '')}
- Sentiment: {analysis.get('sentiment', '')}
- Tone: {analysis.get('tone', '')}

Questions to answer:
1. Does the gist accurately summarize the article? Is it factually correct?
2. Is the sentiment classification (positive/negative/neutral) justified by the article's content?
3. Is the tone assessment accurate based on the article's language and style?

Respond ONLY with valid JSON in this exact format:
{{
  "is_valid": true/false,
  "notes": "Explain your validation here. If valid, explain why. If invalid, point out specific errors or mismatches."
}}

Do not include any text before or after the JSON.
        """.strip()
        
        try:
            # Make API request with retry logic
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
                    
                    # Clean up response
                    if response_text.startswith('```json'):
                        response_text = response_text[7:]
                    if response_text.startswith('```'):
                        response_text = response_text[3:]
                    if response_text.endswith('```'):
                        response_text = response_text[:-3]
                    response_text = response_text.strip()
                    
                    # Parse JSON
                    validation = json.loads(response_text)
                    
                    # Validate required fields
                    if 'is_valid' in validation and 'notes' in validation:
                        return validation
                    else:
                        raise ValueError("Missing required fields in validation response")
                
                except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                    if attempt < max_retries - 1:
                        print(f"    Error, retrying... (attempt {attempt + 1})")
                        time.sleep(2)
                        continue
                    else:
                        raise
        
        except Exception as e:
            print(f"    Error validating analysis: {str(e)}")
            # Return default validation on error
            return {
                'is_valid': False,
                'notes': f'Validation failed due to error: {str(e)}',
                'error': str(e)
            }