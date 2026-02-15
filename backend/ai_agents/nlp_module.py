"""
NLP Processing Module.

Provides natural language processing capabilities for AI agents using
LiteLLM for universal model support and deterministic fallbacks.
"""

from __future__ import annotations

import json
import logging
import os
import re
from collections import Counter
from typing import Any, Dict, List, Optional

try:
    import litellm
except ImportError:
    litellm = None

logger = logging.getLogger(__name__)


class NLPProcessor:
    """NLP module for text understanding and generation using LiteLLM."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")  # allow-secret
        
        if not litellm:
            logger.warning("litellm package is unavailable. NLP features will use fallbacks")
        elif not self.api_key:
            logger.warning("No API key found (OPENAI_API_KEY or ANTHROPIC_API_KEY). Using fallbacks")

    async def generate(
        self,
        system: str,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate text response using LLM when available, otherwise fallback."""
        if litellm and self.api_key:
            try:
                messages = [{"role": "system", "content": system}]

                if context and "previous_messages" in context:
                    for msg in context["previous_messages"]:
                        content = msg.get("content", {}) if isinstance(msg, dict) else {}
                        if isinstance(content, dict):
                            text = content.get("content", "")
                            sender = content.get("sender_id", "User")
                            messages.append({"role": "user", "content": f"{sender}: {text}"})

                messages.append({"role": "user", "content": prompt})
                response = await litellm.acompletion(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.7,
                )
                content = response.choices[0].message.content
                if content:
                    return content
            except Exception as exc:
                logger.error("LLM generation error: %s", exc)

        return f"I received: {prompt}"

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using LLM when available, otherwise heuristics."""
        if litellm and self.api_key:
            try:
                response = await litellm.acompletion(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Analyze sentiment. Return JSON with 'sentiment' "
                                "(positive|negative|neutral) and 'score' (-1.0..1.0)."
                            ),
                        },
                        {"role": "user", "content": text},
                    ],
                    response_format={"type": "json_object"},
                )
                return json.loads(response.choices[0].message.content)
            except Exception as exc:
                logger.error("Sentiment analysis error: %s", exc)

        positive_words = {"good", "great", "excellent", "amazing", "love", "like", "agree", "yes"}
        negative_words = {"bad", "terrible", "awful", "hate", "dislike", "disagree", "no"}

        words = set(re.findall(r"\w+", text.lower()))
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

        return {"sentiment": sentiment, "score": score, "confidence": 0.5}

    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities using LLM when available, otherwise heuristics."""
        if litellm and self.api_key:
            try:
                response = await litellm.acompletion(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Extract named entities. Return JSON with key 'entities': "
                                "[{text, type}]"
                            ),
                        },
                        {"role": "user", "content": text},
                    ],
                    response_format={"type": "json_object"},
                )
                return json.loads(response.choices[0].message.content).get("entities", [])
            except Exception as exc:
                logger.error("Entity extraction error: %s", exc)

        entities: List[Dict[str, Any]] = []
        words = text.split()
        for i, word in enumerate(words):
            clean_word = re.sub(r"[^\w]", "", word)
            if i > 0 and clean_word and clean_word[0].isupper():
                entities.append({"text": clean_word, "type": "UNKNOWN"})

        return entities

    async def summarize(self, text: str, max_length: int = 100) -> str:
        """Summarize text to a maximum length."""
        if litellm and self.api_key:
            try:
                response = await litellm.acompletion(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": f"Summarize the following text in under {max_length} characters.",
                        },
                        {"role": "user", "content": text},
                    ],
                )
                content = response.choices[0].message.content
                if content:
                    return content
            except Exception as exc:
                logger.error("Summarization error: %s", exc)

        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    async def classify_topic(self, text: str) -> Dict[str, float]:
        """Classify topic with LLM or a deterministic fallback."""
        if not litellm or not self.api_key:
            return {"general": 0.7, "politics": 0.2, "technology": 0.1}

        prompt = (
            "Classify the following text into topics "
            "(politics, technology, economy, entertainment, sports, science). "
            "Return JSON where keys are topics and values are confidence scores.\n\n"
            f"Text: {text}"
        )

        try:
            response = await litellm.acompletion(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You classify text into topics. Output valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
        except Exception as exc:
            logger.error("Topic classification error: %s", exc)

        return {"general": 0.7, "politics": 0.2, "technology": 0.1}

    async def extract_keywords(self, text: str, top_k: int = 5) -> List[str]:
        """Extract top-k keywords by simple frequency analysis."""
        words = re.findall(r"\w+", text.lower())
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "is", "of", "it", "that", "with",
        }
        filtered_words = [w for w in words if w not in stopwords and len(w) > 3]
        counts = Counter(filtered_words)
        return [word for word, _ in counts.most_common(top_k)]
