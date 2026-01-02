"""
Tests for NLP Processor
"""

import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from backend.ai_agents.nlp_module import NLPProcessor

@pytest.fixture
def nlp_processor():
    # Initialize without API key to force fallback or mock usage
    with patch.dict(os.environ, {}, clear=True):
        return NLPProcessor()

@pytest.mark.asyncio
async def test_sentiment_analysis_fallback(nlp_processor):
    text = "I love this amazing project!"
    result = await nlp_processor.analyze_sentiment(text)

    assert result["sentiment"] == "positive"
    assert result["score"] > 0

    text_bad = "I hate this terrible bug."
    result_bad = await nlp_processor.analyze_sentiment(text_bad)
    assert result_bad["sentiment"] == "negative"
    assert result_bad["score"] < 0

@pytest.mark.asyncio
async def test_extract_entities_fallback(nlp_processor):
    text = "Hello World from Python."
    # Our simple fallback matches Capitalized words not at start
    # "World" and "Python" should be caught
    entities = await nlp_processor.extract_entities(text)

    texts = [e["text"] for e in entities]
    assert "World" in texts
    assert "Python" in texts

@pytest.mark.asyncio
async def test_summarize_fallback(nlp_processor):
    text = "This is a very long text that needs to be truncated because we are running in fallback mode and cannot use advanced summarization techniques."
    summary = await nlp_processor.summarize(text, max_length=20)

    assert len(summary) <= 20
    assert summary.endswith("...")

@pytest.mark.asyncio
async def test_extract_keywords(nlp_processor):
    text = "Python is great. Python is fast. Coding in Python is fun."
    keywords = await nlp_processor.extract_keywords(text)

    assert "python" in keywords
    assert "coding" in keywords or "great" in keywords

@pytest.mark.asyncio
async def test_generate_mock_openai():
    # Mock the openai client
    with patch("backend.ai_agents.nlp_module.AsyncOpenAI") as MockOpenAI:
        # Setup mock response
        mock_client = AsyncMock()
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Mocked Response"))]
        mock_client.chat.completions.create.return_value = mock_completion

        MockOpenAI.return_value = mock_client

        # Re-init processor with fake key to trigger client creation
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-fake"}):
            processor = NLPProcessor()
            response = await processor.generate("system", "prompt")

            assert response == "Mocked Response"
            mock_client.chat.completions.create.assert_called_once()
