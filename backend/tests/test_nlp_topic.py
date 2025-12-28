import pytest
from backend.ai_agents.nlp_module import NLPProcessor

@pytest.mark.asyncio
async def test_classify_topic_heuristic():
    nlp = NLPProcessor()
    # Ensure no API key uses heuristic
    nlp.client = None

    # Test Politics
    text_politics = "The president signed a new bill regarding the election."
    result = await nlp.classify_topic(text_politics)
    assert "politics" in result
    assert result["politics"] > 0

    # Test Technology
    text_tech = "Python is a great programming language for AI and software."
    result = await nlp.classify_topic(text_tech)
    assert "technology" in result
    assert result["technology"] > 0

    # Test Economy
    text_econ = "The stock market crashed due to inflation and trade wars."
    result = await nlp.classify_topic(text_econ)
    assert "economy" in result
    assert result["economy"] > 0

    # Test Science
    text_science = "NASA made a new discovery in space research."
    result = await nlp.classify_topic(text_science)
    assert "science" in result
    assert result["science"] > 0

    # Test Sports
    text_sports = "The football team won the championship match."
    result = await nlp.classify_topic(text_sports)
    assert "sports" in result
    assert result["sports"] > 0

    # Test Entertainment
    text_ent = "The new movie by the famous actor won an award."
    result = await nlp.classify_topic(text_ent)
    assert "entertainment" in result
    assert result["entertainment"] > 0

    # Test General (fallback)
    text_general = "This is just a random sentence with no specific context."
    result = await nlp.classify_topic(text_general)
    assert "general" in result
    assert result["general"] == 1.0

    # Test Mixed
    text_mixed = "The president discussed the new software for the stock market."
    result = await nlp.classify_topic(text_mixed)
    # Should have politics, technology, and economy
    assert "politics" in result or "technology" in result or "economy" in result
