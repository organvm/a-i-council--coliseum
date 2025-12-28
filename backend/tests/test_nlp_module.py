import pytest
import os
from unittest.mock import MagicMock, patch, AsyncMock
from backend.ai_agents.nlp_module import NLPProcessor

@pytest.mark.asyncio
async def test_extract_entities_fallback():
    # Force client to be None to test fallback
    with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
        processor = NLPProcessor()
        text = "Apple Inc. announced a new product. Tim Cook spoke about it."
        entities = await processor.extract_entities(text)

        # Check if we got entities
        assert len(entities) > 0
        texts = [e['text'] for e in entities]
        assert "Apple Inc" in texts
        assert "Tim Cook" in texts

@pytest.mark.asyncio
async def test_extract_entities_openai_mock():
    # Mock OpenAI client
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"entities": [{"text": "Apple", "type": "ORGANIZATION", "confidence": 0.9}]}'
    mock_client.chat.completions.create.return_value = mock_response

    with patch('backend.ai_agents.nlp_module.AsyncOpenAI', return_value=mock_client):
        # We need to set env var so client is initialized
        with patch.dict(os.environ, {"OPENAI_API_KEY": "fake-key"}):
            processor = NLPProcessor()
            # Inject the mock client directly because __init__ might have created a real one or failed if we didn't mock AsyncOpenAI class correctly
            # Actually, patch on 'backend.ai_agents.nlp_module.AsyncOpenAI' will make processor.client be the mock instance

            # Wait, processor.client is set in __init__.
            # patch needs to be active when NLPProcessor is instantiated.

            entities = await processor.extract_entities("Apple is great.")
            assert len(entities) == 1
            assert entities[0]['text'] == "Apple"
            assert entities[0]['type'] == "ORGANIZATION"
