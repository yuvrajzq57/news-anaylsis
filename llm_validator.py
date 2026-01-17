import os
import json
import logging
from openai import AsyncOpenAI, APIError

logger = logging.getLogger(__name__)

class LLMValidator:
    """Validates analysis using Groq (Llama 3.1 8B)."""
    
    def __init__(self):
        """Initialize Groq client."""
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = "llama-3.1-8b-instant"
    
    async def validate_analysis(self, article, analysis):
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
  "is_valid": true,
  "notes": "Explain your validation here. If valid, explain why. If invalid, point out specific errors or mismatches."
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
            validation = json.loads(response_text)
            
            # Validate required fields
            if 'is_valid' in validation and 'notes' in validation:
                return validation
            else:
                raise ValueError("Missing required fields in validation response")
        
        except Exception as e:
            logger.error(f"Error validating analysis: {str(e)}")
            # Return default validation on error
            return {
                'is_valid': False,
                'notes': f'Validation failed due to error: {str(e)}',
                'error': str(e)
            }