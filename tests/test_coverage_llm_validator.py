
import pytest
import json
import os
import requests
from unittest.mock import Mock, patch, MagicMock
from llm_validator import LLMValidator

# Sample data
SAMPLE_ARTICLE = {
    'title': 'Test Article',
    'description': 'Test Description',
    'content': 'Test Content'
}

SAMPLE_ANALYSIS = {
    'gist': 'Test Gist',
    'sentiment': 'neutral',
    'tone': 'objective'
}

class TestLLMValidatorCoverage:
    
    @pytest.fixture
    def validator(self):
        with patch.dict('os.environ', {'GROQ_API_KEY': 'test_key'}):
            return LLMValidator()

    @patch('llm_validator.requests.post')
    def test_json_cleanup_markdown(self, mock_post, validator):
        """Test validation when LLM returns JSON wrapped in markdown code blocks."""
        # Case 1: ```json ... ```
        mock_response = Mock()
        mock_response.status_code = 200
        content_json_str = json.dumps({'is_valid': True, 'notes': 'Valid'})
        mock_response.json.return_value = {
            'choices': [{'message': {'content': f'```json\n{content_json_str}\n```'}}]
        }
        mock_post.return_value = mock_response

        result = validator.validate_analysis(SAMPLE_ARTICLE, SAMPLE_ANALYSIS)
        assert result['is_valid'] is True
        assert result['notes'] == 'Valid'

        # Case 2: ``` ... ``` (no language specifier)
        mock_response.json.return_value = {
            'choices': [{'message': {'content': f'```\n{content_json_str}\n```'}}]
        }
        result = validator.validate_analysis(SAMPLE_ARTICLE, SAMPLE_ANALYSIS)
        assert result['is_valid'] is True

    @patch('llm_validator.requests.post')
    def test_json_cleanup_extra_text(self, mock_post, validator):
        """Test validation when LLM returns text alongside JSON (though cleanup might be strict/loose).
           The current implementation strips markdown but assumes the rest is JSON.
           Actually the code does:
           if startswith ```json -> strip
           if startswith ``` -> strip
           if endswith ``` -> strip
           Then json.loads(response_text)
           So it MUST be valid JSON after stripping tags.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        content_json_str = json.dumps({'is_valid': True, 'notes': 'Valid'})
        
        # If there is extra text outside code blocks, it might fail if the code doesn't handle it.
        # But let's test the success path where it is just whitespace.
        mock_response.json.return_value = {
            'choices': [{'message': {'content': f'   {content_json_str}   '}}]
        }
        mock_post.return_value = mock_response

        result = validator.validate_analysis(SAMPLE_ARTICLE, SAMPLE_ANALYSIS)
        assert result['is_valid'] is True

    @patch('llm_validator.requests.post')
    @patch('llm_validator.time.sleep')
    def test_rate_limiting_retry(self, mock_sleep, mock_post, validator):
        """Test that the validator retries on 429 status code."""
        # First response 429, second 200
        response_429 = Mock()
        response_429.status_code = 429
        
        response_200 = Mock()
        response_200.status_code = 200
        response_200.json.return_value = {
            'choices': [{'message': {'content': json.dumps({'is_valid': True, 'notes': 'Retry success'})}}]
        }
        
        mock_post.side_effect = [response_429, response_200]
        
        result = validator.validate_analysis(SAMPLE_ARTICLE, SAMPLE_ANALYSIS)
        
        assert mock_post.call_count == 2
        assert result['is_valid'] is True
        assert result['notes'] == 'Retry success'
        mock_sleep.assert_called()

    @patch('llm_validator.requests.post')
    @patch('llm_validator.time.sleep')
    def test_retry_on_request_exception(self, mock_sleep, mock_post, validator):
        """Test that the validator retries on RequestException."""
        # First attempt raises Exception, second succeeds
        response_200 = Mock()
        response_200.status_code = 200
        response_200.json.return_value = {
            'choices': [{'message': {'content': json.dumps({'is_valid': True, 'notes': 'Success'})}}]
        }
        
        mock_post.side_effect = [requests.exceptions.RequestException("Connection error"), response_200]
        
        result = validator.validate_analysis(SAMPLE_ARTICLE, SAMPLE_ANALYSIS)
        
        assert mock_post.call_count == 2
        assert result['is_valid'] is True

    @patch('llm_validator.requests.post')
    def test_missing_required_fields(self, mock_post, validator):
        """Test handling of JSON missing required fields."""
        mock_response = Mock()
        mock_response.status_code = 200
        # Missing 'notes'
        mock_response.json.return_value = {
            'choices': [{'message': {'content': json.dumps({'is_valid': True})}}]
        }
        mock_post.return_value = mock_response
        
        # It should retry. Let's make it fail all retries with the same bad response.
        # But wait, the code raises ValueError ("Missing required fields"), which is NOT a RequestException or JSONDecodeError.
        # So checking line 121: except (requests.exceptions.RequestException, json.JSONDecodeError) ...
        # ValueError is NOT caught there!
        # It bubbles up to line 129: except Exception as e.
        # So it should NOT retry for ValueError, it should fail immediately and return the error dict.
        
        result = validator.validate_analysis(SAMPLE_ARTICLE, SAMPLE_ANALYSIS)
        
        assert result['is_valid'] is False
        assert "Validation failed due to error" in result['notes']
        assert "Missing required fields" in result['error']

    @patch('llm_validator.requests.post')
    @patch('llm_validator.time.sleep')
    def test_exhaust_retries(self, mock_sleep, mock_post, validator):
        """Test that it fails gracefully after exhausting retries."""
        mock_post.side_effect = requests.exceptions.RequestException("Persistent Error")
        
        result = validator.validate_analysis(SAMPLE_ARTICLE, SAMPLE_ANALYSIS)
        
        # It tries 3 times (range(3))
        assert mock_post.call_count == 3
        assert result['is_valid'] is False
        assert "Validation failed" in result['notes']

