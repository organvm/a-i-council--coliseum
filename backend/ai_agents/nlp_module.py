"""
NLP Processing Module

Provides natural language processing capabilities for AI agents.
"""

import os
from typing import Dict, Any, List, Optional
import re
from collections import Counter
import logging

# Check for OpenAI availability
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from openai import AsyncOpenAI

# Configure logging
logger = logging.getLogger(__name__)

class NLPProcessor:
    """
    Natural Language Processing module for agent text understanding
    and generation.
    """
    
    def __init__(self, model_name: str = "gpt-4-turbo-preview"):
        self.model_name = model_name
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("OPENAI_API_KEY not found. NLP features will use placeholders.")
    
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
                import json
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                logger.error(f"Sentiment analysis error: {e}")

        # Fallback: Simple keyword based sentiment
        positive_words = {"good", "great", "excellent", "amazing", "love", "like", "agree", "yes"}
        negative_words = {"bad", "terrible", "awful", "hate", "dislike", "disagree", "no"}

        words = set(re.findall(r'\w+', text.lower()))
        pos_count = len(words.intersection(positive_words))
        neg_count = len(words.intersection(negative_words))

        score = 0.0
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
                import json
                return json.loads(response.choices[0].message.content).get("entities", [])
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
        if not self.client:
            # Fallback for when API is not available
            return {
                "general": 0.7,
                "politics": 0.2,
                "technology": 0.1
            }

        prompt = f"""
        Classify the following text into relevant topics (e.g., politics, technology, economy, entertainment, sports, science).
        Return a JSON object where keys are topics and values are confidence scores between 0 and 1.

        Text: {text}
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that classifies text into topics. Output valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            else:
                return {"error": 1.0}
        except Exception as e:
            logger.error(f"Error classifying topic: {e}")
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
