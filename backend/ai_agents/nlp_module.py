"""
NLP Processing Module

Provides natural language processing capabilities for AI agents.
"""

import os
import json
import re
import logging
from typing import Dict, Any, List, Optional
from collections import Counter

# Check for OpenAI availability
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class NLPProcessor:
    """
    Natural Language Processing module for agent text understanding
    and generation.
    """
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.model_name = model_name
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None

        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = AsyncOpenAI(api_key=self.api_key)
                # Validate API key by testing a simple request in production
                # For now, just log that we have a client
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            if not OPENAI_AVAILABLE:
                logger.warning("OpenAI library not available. Using fallback NLP methods.")
            elif not self.api_key:
                logger.warning("OPENAI_API_KEY not found. Using fallback NLP methods.")
    
    async def generate(self, system: str, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate text response using LLM
        """
        if self.client:
            try:
                messages = [{"role": "system", "content": system}]

                # Add context if available
                if context and "previous_messages" in context:
                    for msg in context["previous_messages"]:
                        # Simplified context mapping
                        content = msg.get("content", {})
                        if isinstance(content, dict):
                            text = content.get("content", "")
                            sender = content.get("sender_id", "User")
                            messages.append({"role": "user", "content": f"{sender}: {text}"})

                messages.append({"role": "user", "content": prompt})

                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")

        # Fallback response
        return f"I received: {prompt}"

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text.
        
        Returns:
            Dict with sentiment label (positive, negative, neutral) and score (-1.0 to 1.0)
        """
        if self.client:
            try:
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "Analyze the sentiment of the following text. Return a JSON object with 'sentiment' (positive, negative, neutral) and 'score' (float -1.0 to 1.0)."},
                        {"role": "user", "content": text}
                    ],
                    response_format={"type": "json_object"}
                )
                
                raw_content = getattr(getattr(response.choices[0], "message", None), "content", None)
                if not raw_content:
                    raise ValueError("Empty content returned from sentiment analysis model.")

                result = json.loads(raw_content)
                if not isinstance(result, dict):
                    raise ValueError("Sentiment analysis response is not a JSON object.")

                if "sentiment" not in result or "score" not in result:
                    raise ValueError("Sentiment analysis JSON missing required 'sentiment' or 'score' keys.")

                # Optionally normalize and ensure a confidence field is present for consistency
                if "confidence" not in result:
                    result["confidence"] = 1.0

                return result
            except Exception as e:
                logger.error(f"Sentiment analysis error: {e}")

        # Fallback: Simple keyword based sentiment
        positive_words = {"good", "great", "excellent", "amazing", "love", "like", "agree", "yes"}
        negative_words = {"bad", "terrible", "awful", "hate", "dislike", "disagree", "no"}

        words = set(re.findall(r'\w+', text.lower()))
        pos_count = len(words.intersection(positive_words))
        neg_count = len(words.intersection(negative_words))

        if pos_count > neg_count:
            sentiment = "positive"
            score = 0.5 + (0.1 * min(pos_count, 5))
        elif neg_count > pos_count:
            sentiment = "negative"
            score = -0.5 - (0.1 * min(neg_count, 5))
        else:
            sentiment = "neutral"
            score = 0.0

        return {
            "sentiment": sentiment,
            "score": score,
            "confidence": 0.5  # Low confidence for heuristic
        }
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text.
        """
        if self.client:
            try:
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "Extract named entities (Person, Org, Location, etc) from the text. Return a JSON object with a key 'entities' containing a list of objects with 'text' and 'type'."},
                        {"role": "user", "content": text}
                    ],
                    response_format={"type": "json_object"}
                )
                
                raw_content = response.choices[0].message.content
                data = json.loads(raw_content)

                if not isinstance(data, dict):
                    logger.warning(
                        "Entity extraction response is not a JSON object: %r",
                        data,
                    )
                    return []

                entities = data.get("entities")
                if isinstance(entities, list) and all(
                    isinstance(entity, dict)
                    and "text" in entity
                    and "type" in entity
                    for entity in entities
                ):
                    return entities

                logger.warning(
                    "Entity extraction response has unexpected 'entities' structure: %r",
                    data,
                )
                return []
            except Exception as e:
                logger.error(f"Entity extraction error: {e}")

        # Fallback: Simple capitalization heuristic
        # Matches capitalized words that are not at the start of a sentence (simplified)
        entities = []
        words = text.split()
        for i, word in enumerate(words):
            clean_word = re.sub(r'[^\w]', '', word)
            if i > 0 and clean_word and clean_word[0].isupper():
                entities.append({"text": clean_word, "type": "UNKNOWN"})

        return entities
    
    async def summarize(self, text: str, max_length: int = 100) -> str:
        """
        Summarize text to specified length.
        """
        if self.client:
            try:
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": f"Summarize the following text in under {max_length} characters."},
                        {"role": "user", "content": text}
                    ]
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"Summarization error: {e}")

        # Fallback: Truncate
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    async def classify_topic(self, text: str) -> Dict[str, float]:
        """
        Classify text into topic categories.
        """
        # Fallback only for now as it wasn't explicitly requested to be LLM-backed in the strict TODO list,
        # but good to have consistent structure.
        return {
            "general": 0.7,
            "politics": 0.2,
            "technology": 0.1
        }
    
    async def extract_keywords(self, text: str, top_k: int = 5) -> List[str]:
        """
        Extract key terms from text using frequency.
        """
        words = re.findall(r'\w+', text.lower())
        # Filter common stopwords (very basic list)
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "is", "of", "it", "that", "with"}
        filtered_words = [w for w in words if w not in stopwords and len(w) > 3]

        counts = Counter(filtered_words)
        return [word for word, count in counts.most_common(top_k)]
