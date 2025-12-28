"""
NLP Processing Module

Provides natural language processing capabilities for AI agents.
"""

import os
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
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text
        
        Returns:
            Dict with sentiment label and score
        """
        # Placeholder for actual sentiment analysis
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
        if not self.client:
            # Fallback for when API is not available
            if len(text) <= max_length:
                return text
            return text[:max_length] + "..."

        prompt = f"""
        Summarize the following text efficiently. The summary must be under {max_length} characters.

        Text: {text}
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes text."},
                    {"role": "user", "content": prompt}
                ]
            )
            content = response.choices[0].message.content
            if content:
                # Ensure the summary respects the max_length constraint as a safety net
                if len(content) > max_length:
                    # Handle edge case where max_length is very small
                    slice_idx = max(0, max_length - 3)
                    return content[:slice_idx] + "..."
                return content

            # If content is empty, fall back to slicing
            if len(text) <= max_length:
                return text
            return text[:max_length] + "..."

        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            # Fallback on error
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
