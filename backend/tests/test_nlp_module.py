"""Contract tests for NLPProcessor fallback and optional OpenAI mode."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.ai_agents import nlp_module
from backend.ai_agents.nlp_module import NLPProcessor


@pytest.fixture
def nlp_processor():
    with patch.dict(os.environ, {}, clear=True):
        return NLPProcessor()


@pytest.mark.asyncio
async def test_sentiment_analysis_fallback(nlp_processor):
    result = await nlp_processor.analyze_sentiment("I love this amazing project!")
    assert result["sentiment"] == "positive"
    assert result["score"] > 0

    bad_result = await nlp_processor.analyze_sentiment("I hate this terrible bug.")
    assert bad_result["sentiment"] == "negative"
    assert bad_result["score"] < 0


@pytest.mark.asyncio
async def test_extract_entities_fallback(nlp_processor):
    entities = await nlp_processor.extract_entities("Hello World from Python.")
    texts = [e["text"] for e in entities]
    assert "World" in texts
    assert "Python" in texts


@pytest.mark.asyncio
async def test_fallback_works_when_openai_unavailable_even_with_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(nlp_module, "litellm", None)
    processor = NLPProcessor()

    response = await processor.generate("system", "prompt")
    assert response == "I received: prompt"


@pytest.mark.asyncio
async def test_generate_with_mocked_openai_client():
    with patch("backend.ai_agents.nlp_module.litellm") as mock_litellm:
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content="Mocked Response"))]
        mock_litellm.acompletion = AsyncMock(return_value=mock_completion)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-fake"}):
            processor = NLPProcessor()
            response = await processor.generate("system", "prompt")

    assert response == "Mocked Response"

