"""
NLP Processing Module

Provides natural language processing capabilities for AI agents.
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from openai import AsyncOpenAI

# Try to import transformers for local sentiment analysis
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    pipeline = None

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

        # Local sentiment analyzer (lazy loaded)
        self._sentiment_analyzer = None
        self._sentiment_analyzer_loaded = False
    
    @property
    def sentiment_analyzer(self):
        """Lazy load the sentiment analyzer pipeline."""
        if not self._sentiment_analyzer_loaded:
            if TRANSFORMERS_AVAILABLE:
                try:
                    # Using a small, fast model for sentiment analysis
                    self._sentiment_analyzer = pipeline(
                        "sentiment-analysis",
                        model="distilbert-base-uncased-finetuned-sst-2-english"
                    )
                    logger.info("Local sentiment analysis model loaded successfully.")
                except Exception as e:
                    logger.warning(f"Could not load local sentiment model: {e}")
            else:
                logger.warning("Transformers library not available.")

            self._sentiment_analyzer_loaded = True

        return self._sentiment_analyzer

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text using local model or API fallback.
        
        Returns:
            Dict with:
            - "sentiment": 'positive', 'negative', or 'neutral'
            - "score": polarity score between 0 (negative) and 1 (positive)
            - "confidence": model confidence (0-1)
        """
        # 1. Try local transformers model first
        analyzer = self.sentiment_analyzer
        if analyzer:
            try:
                # Run sync pipeline in executor
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(None, analyzer, text)

                # Result format: [{'label': 'POSITIVE', 'score': 0.99...}]
                if result and len(result) > 0:
                    res = result[0]
                    label = res['label'].lower() # 'positive' or 'negative'
                    confidence = res['score']

                    # Normalize score to polarity (0=neg, 1=pos)
                    if label == 'positive':
                        polarity = confidence
                    elif label == 'negative':
                        polarity = 1.0 - confidence
                    else:
                        polarity = 0.5

                    return {
                        "sentiment": label,
                        "score": polarity,
                        "confidence": confidence
                    }
            except Exception as e:
                logger.error(f"Error in local sentiment analysis: {e}")

        # 2. Fallback to OpenAI API
        if self.client:
            prompt = f"""
            Analyze the sentiment of the following text.
            Return a JSON object with:
            - "sentiment": one of "positive", "negative", "neutral"
            - "score": a float between 0 (negative) and 1 (positive) representing the sentiment polarity
            - "confidence": a float between 0 and 1 representing model confidence

            Text: {text}
            """
            try:
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a sentiment analysis assistant. Output valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={ "type": "json_object" }
                )
                content = response.choices[0].message.content
                if content:
                    return json.loads(content)
            except Exception as e:
                logger.error(f"Error in API sentiment analysis: {e}")

        # 3. Fallback to placeholder
        return {
            "sentiment": "neutral",
            "score": 0.5,
            "confidence": 0.8
        }
    
    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text
        
        Returns:
            List of entities with type and text
        """
        # Placeholder for actual entity extraction
        return []
    
    async def summarize(self, text: str, max_length: int = 100) -> str:
        """
        Summarize text to specified length
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            
        Returns:
            Summarized text
        """
        # Placeholder for actual summarization
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
    
    async def classify_topic(self, text: str) -> Dict[str, float]:
        """
        Classify text into topic categories
        
        Returns:
            Dict of topics with confidence scores
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
        Extract key terms from text
        
        Args:
            text: Input text
            top_k: Number of keywords to extract
            
        Returns:
            List of keywords
        """
        # Placeholder for keyword extraction
        words = text.lower().split()
        return list(set(words[:top_k]))
