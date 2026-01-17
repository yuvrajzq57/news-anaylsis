"""
Unit tests for the news analysis pipeline.
Tests core functionality without making actual API calls.
"""

import pytest
import json
from unittest.mock import Mock, patch
from news_fetcher import NewsFetcher
from llm_analyzer import LLMAnalyzer
from llm_validator import LLMValidator

# Test data
SAMPLE_ARTICLE = {
    'title': 'India announces new economic policy',
    'description': 'The government unveiled a comprehensive economic reform package.',
    'content': 'India has announced major economic reforms...',
    'url': 'https://example.com/article',
    'publishedAt': '2024-01-15T10:00:00Z',
    'source': 'Test News'
}

SAMPLE_ANALYSIS = {
    'gist': 'India announced major economic reforms to boost growth.',
    'sentiment': 'positive',
    'tone': 'analytical'
}

class TestNewsFetcher:
    """Test the NewsFetcher class."""
    
    def test_fetcher_initialization_without_api_key(self):
        """Test that fetcher raises error without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="NEWSAPI_KEY not found"):
                NewsFetcher()
    
    @patch('news_fetcher.requests.get')
    def test_successful_article_fetch(self, mock_get):
        """Test successful fetching of articles."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'ok',
            'articles': [SAMPLE_ARTICLE]
        }
        mock_get.return_value = mock_response
        
        with patch.dict('os.environ', {'NEWSAPI_KEY': 'test_key'}):
            fetcher = NewsFetcher()
            articles = fetcher.fetch_india_politics_news(num_articles=1)
            
            assert len(articles) == 1
            assert articles[0]['title'] == SAMPLE_ARTICLE['title']
            assert 'source' in articles[0]
    
    @patch('news_fetcher.requests.get')
    def test_fetch_with_timeout(self, mock_get):
        """Test handling of timeout errors."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()
        
        with patch.dict('os.environ', {'NEWSAPI_KEY': 'test_key'}):
            fetcher = NewsFetcher()
            articles = fetcher.fetch_india_politics_news()
            
            assert articles == []

class TestLLMAnalyzer:
    """Test the LLMAnalyzer class."""
    
    def test_analyzer_initialization_without_api_key(self):
        """Test that analyzer raises error without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GROQ_API_KEY not found"):
                LLMAnalyzer()
    
    @patch('llm_analyzer.requests.post')
    def test_successful_analysis(self, mock_post):
        """Test successful article analysis."""
        # Mock Groq response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps(SAMPLE_ANALYSIS)
                }
            }]
        }
        mock_post.return_value = mock_response
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test_key'}):
            analyzer = LLMAnalyzer()
            result = analyzer.analyze_article(SAMPLE_ARTICLE)
            
            assert 'gist' in result
            assert 'sentiment' in result
            assert 'tone' in result
            assert result['sentiment'] in ['positive', 'negative', 'neutral']
    
    @patch('llm_analyzer.requests.post')
    def test_analysis_with_json_error(self, mock_post):
        """Test handling of malformed JSON response."""
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': "This is not JSON"
                }
            }]
        }
        mock_post.return_value = mock_response
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test_key'}):
            analyzer = LLMAnalyzer()
            result = analyzer.analyze_article(SAMPLE_ARTICLE)
            
            # Should return default analysis on error
            assert 'gist' in result
            assert 'error' in result

class TestLLMValidator:
    """Test the LLMValidator class."""
    
    def test_validator_initialization_without_api_key(self):
        """Test that validator raises error without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GROQ_API_KEY not found"):
                LLMValidator()
    
    @patch('llm_validator.requests.post')
    def test_successful_validation(self, mock_post):
        """Test successful validation of analysis."""
        # Mock OpenRouter response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'is_valid': True,
                        'notes': 'Analysis is accurate and well-justified.'
                    })
                }
            }]
        }
        mock_post.return_value = mock_response
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test_key'}):
            validator = LLMValidator()
            result = validator.validate_analysis(SAMPLE_ARTICLE, SAMPLE_ANALYSIS)
            
            assert 'is_valid' in result
            assert 'notes' in result
            assert isinstance(result['is_valid'], bool)
    
    @patch('llm_validator.requests.post')
    def test_validation_with_api_error(self, mock_post):
        """Test handling of API errors during validation."""
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("API Error")
        
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test_key'}):
            validator = LLMValidator()
            result = validator.validate_analysis(SAMPLE_ARTICLE, SAMPLE_ANALYSIS)
            
            # Should return error validation
            assert 'is_valid' in result
            assert result['is_valid'] == False
            assert 'error' in result

def test_article_data_structure():
    """Test that sample article has required fields."""
    required_fields = ['title', 'description', 'content', 'url', 'publishedAt', 'source']
    for field in required_fields:
        assert field in SAMPLE_ARTICLE, f"Missing required field: {field}"

def test_analysis_data_structure():
    """Test that sample analysis has required fields."""
    required_fields = ['gist', 'sentiment', 'tone']
    for field in required_fields:
        assert field in SAMPLE_ANALYSIS, f"Missing required field: {field}"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])